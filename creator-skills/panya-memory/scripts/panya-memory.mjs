#!/usr/bin/env node
// รับ-ส่ง memory ของ Claude Code กับ panya ผ่าน HTTP API · ใช้ Node 18+ อย่างเดียว ไม่มี dependency
//   node panya-memory.mjs setup --url $PANYA_URL --key <api key>
//   node panya-memory.mjs push [--project <ชื่อโฟลเดอร์โปรเจกต์>] [--dry]
//   node panya-memory.mjs search <คำถาม> [--limit 8] [--as-of 2026-01-31]
//   node panya-memory.mjs context [--days 30]
//   node panya-memory.mjs history <subject> <attribute>
//   node panya-memory.mjs remember <ข้อความ> [--subject s --attribute a] [--kind fact|preference|event] [--source s]
//   node panya-memory.mjs list [คำกรอง]
//   node panya-memory.mjs show <โปรเจกต์>/<ชื่อความจำ>
//   node panya-memory.mjs pull <โปรเจกต์> --to <โฟลเดอร์> [--force]
// ทุกคำสั่งรับ --brain <ชื่อ> (ค่าตั้งต้น claude-memory)
import { mkdir, readdir, readFile, stat, writeFile } from 'node:fs/promises'
import { homedir } from 'node:os'
import { basename, join } from 'node:path'

const CLAUDE = join(homedir(), '.claude')
const CONFIG = join(CLAUDE, 'panya.json')
const PREFIX = 'claude-memory/'
// panya บนคลาวด์ (AWS กรุงเทพ ผ่าน Cloudflare) · เปลี่ยนได้ด้วย setup --url หรือตัวแปร PANYA_URL
const DEFAULT_URL = '$PANYA_URL'

// ── อาร์กิวเมนต์ ──────────────────────────────────────────────────
const argv = process.argv.slice(2)
const cmd = argv[0]
const VALUE_FLAGS = new Set(['--url', '--key', '--brain', '--project', '--to', '--limit', '--subject', '--attribute', '--kind', '--source', '--as-of', '--days'])
const flags = {}, words = []
for (let i = 1; i < argv.length; i++) {
  if (VALUE_FLAGS.has(argv[i])) flags[argv[i].slice(2)] = argv[++i]
  else if (argv[i].startsWith('--')) flags[argv[i].slice(2)] = true
  else words.push(argv[i])
}
const brain = flags.brain || 'claude-memory'
// โยนแล้วจบที่ท้ายไฟล์ ไม่เรียก process.exit ตรง ๆ: บน Windows การปิดทันทีขณะ fetch ยังถือ socket อยู่ทำให้ Node แครช (UV_HANDLE_CLOSING)
class Fail extends Error {}
const fail = (msg) => { throw new Fail(msg) }

// ── การเชื่อมต่อ: ตัวแปรแวดล้อมมาก่อน แล้วจึงไฟล์ ~/.claude/panya.json ──
async function config() {
  const file = JSON.parse(await readFile(CONFIG, 'utf8').catch(() => '{}'))
  const url = (process.env.PANYA_URL || file.url || DEFAULT_URL).replace(/\/+$/, '')
  const key = process.env.PANYA_API_KEY || file.key
  if (!key) fail(`ยังไม่ได้ตั้งค่า API key · รัน: node ${basename(process.argv[1])} setup --url <url> --key <key>  (หรือตั้ง PANYA_URL และ PANYA_API_KEY)`)
  return { url, key }
}
let conn
async function call(method, path, body) {
  conn ??= await config()
  const res = await fetch(conn.url + path, {
    method,
    headers: { authorization: 'Bearer ' + conn.key, ...(body ? { 'content-type': 'application/json' } : {}) },
    body: body ? JSON.stringify(body) : undefined,
  }).catch((e) => fail(`ติดต่อ panya ที่ ${conn.url} ไม่ได้: ${e.cause?.code || e.message}`))
  if (!res.ok) fail(`panya ตอบ ${res.status} สำหรับ ${method} ${path.split('?')[0]}: ${(await res.json().catch(() => ({}))).error || ''}`)
  return res.json()
}
const q = (o) => '?' + new URLSearchParams(o)
// เหมือน call แต่ไม่จบโปรแกรมเมื่อเซิร์ฟเวอร์ตอบ error (ใช้ตอนต้องตัดสินใจเองว่าจะทำอะไรต่อ)
async function tryCall(method, path, body) {
  conn ??= await config()
  const res = await fetch(conn.url + path, {
    method,
    headers: { authorization: 'Bearer ' + conn.key, ...(body ? { 'content-type': 'application/json' } : {}) },
    body: body ? JSON.stringify(body) : undefined,
  }).catch((e) => fail(`ติดต่อ panya ที่ ${conn.url} ไม่ได้: ${e.cause?.code || e.message}`))
  return { ok: res.ok, status: res.status, data: await res.json().catch(() => ({})) }
}
const isSecretRefusal = (r) => r.status === 400 && /never stores secrets/.test(r.data?.error || '')
// ส่งเป็นชุด · ถ้าเซิร์ฟเวอร์ปฏิเสธเพราะเจอสิ่งที่ดูเหมือนความลับ ให้ส่งทีละรายการและข้ามเฉพาะรายการนั้น ไม่ทิ้งทั้งชุด
async function sendBatch(memories) {
  const r = await tryCall('POST', '/v1/memories/batch', { brain, memories })
  if (r.ok) return { sent: memories.length, refused: [] }
  if (!isSecretRefusal(r)) fail(`panya ตอบ ${r.status}: ${r.data?.error || ''}`)
  const refused = []
  let sent = 0
  for (const m of memories) {
    const one = await tryCall('POST', '/v1/memories', { brain, ...m })
    if (one.ok) sent++
    else if (isSecretRefusal(one)) refused.push(m.source || m.subject || m.text.slice(0, 40))
    else fail(`panya ตอบ ${one.status}: ${one.data?.error || ''}`)
  }
  return { sent, refused }
}

// ── แปลงไฟล์ความจำเป็นชิ้น (ตรงกับ src/import-md.ts ของ panya) ──────
function parse(raw, fallbackName) {
  const text = raw.replace(/^﻿/, '').replace(/\r\n/g, '\n')
  const m = text.match(/^---\n([\s\S]*?)\n---\n?([\s\S]*)$/)
  if (!m) return { name: fallbackName, description: '', type: '', body: text.trim() }
  const field = (k) => { const hit = m[1].match(new RegExp(`^\\s*${k}:\\s*(.+)$`, 'm')); return hit ? hit[1].trim().replace(/^["']|["']$/g, '') : '' }
  return { name: field('name') || fallbackName, description: field('description'), type: field('type'), body: m[2].trim() }
}
function chunk(body, max = 700, min = 40) {
  const out = []
  const push = (s) => {
    const t = s.trim()
    if (!t) return
    const last = out[out.length - 1]
    if (last !== undefined && last.length < min && last.length + t.length + 1 <= max) out[out.length - 1] = last + '\n' + t
    else out.push(t)
  }
  for (const para of body.split(/\n\s*\n/)) {
    if (para.length <= max) { push(para); continue }
    let buf = ''
    for (const line of para.split('\n')) {
      if (buf && buf.length + line.length + 1 > max) { push(buf); buf = '' }
      if (line.length > max) for (let i = 0; i < line.length; i += max) push(line.slice(i, i + max))
      else buf = buf ? buf + '\n' + line : line
    }
    push(buf)
  }
  return out
}
// โทเคนและ key ที่ติดมาในความจำถูกปิดก่อนส่งออกจากเครื่อง
const SECRETS = [
  /\b(?:sk|pk|rk)-[A-Za-z0-9_-]{16,}/g, /\b[a-z]{2,6}_(?:sk|pk|key|secret|token)_[A-Za-z0-9_-]{6,}(?:…|\.\.\.)?/gi, /\bgh[opsu]_[A-Za-z0-9]{20,}/g,
  /\bAKIA[0-9A-Z]{16}\b/g, /\bAIza[0-9A-Za-z_-]{30,}/g, /\bsm_[A-Za-z0-9_-]{16,}/g, /\beyJ[A-Za-z0-9_-]{20,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}/g,
  /\b[0-9a-f]{32,}\b/gi, /\b[A-Za-z0-9+/_-]{48,}={0,2}/g,
]
let redactions = 0
const redact = (text) => SECRETS.reduce((out, re) => out.replace(re, () => { redactions++; return '[redacted]' }), text)
const kindOf = (type) => (type === 'feedback' || type === 'user' ? 'preference' : 'fact')

// subject = claude-memory/<โปรเจกต์>/<ชื่อความจำ>
const split = (subject) => { const [, project, ...name] = subject.split('/'); return { project, name: name.join('/') } }
async function remote() {
  const { subjects } = await call('GET', '/v1/subjects' + q({ brain, prefix: PREFIX }))
  return subjects.map((s) => ({ ...s, ...split(s.subject) })).filter((s) => s.name)
}
async function rebuild(entry) {
  const { memories } = await call('GET', '/v1/memories' + q({ brain, subject: entry.subject }))
  const desc = memories.find((m) => m.attribute === 'description')?.text || ''
  const body = memories.filter((m) => m.attribute !== 'description').map((m) => m.text).join('\n\n')
  // ชนิดเดิมของความจำไม่ได้ถูกเก็บไว้ตรง ๆ: ความชอบ → feedback, นอกนั้น → project
  const type = memories[0]?.kind === 'preference' ? 'feedback' : 'project'
  return `---\nname: ${entry.name}\ndescription: ${desc}\nmetadata:\n  type: ${type}\n---\n\n${body}\n`
}

// ── คำสั่ง ─────────────────────────────────────────────────────────
const commands = {
  async setup() {
    if (!flags.key) fail('ใช้: setup --key <api key จากหน้า บัญชีและ API> [--url $PANYA_URL]')
    await mkdir(CLAUDE, { recursive: true })
    await writeFile(CONFIG, JSON.stringify({ url: (flags.url || DEFAULT_URL).replace(/\/+$/, ''), key: flags.key }, null, 2) + '\n', { mode: 0o600 })
    const s = await call('GET', '/v1/stats' + q({ brain }))
    console.log(`บันทึกการเชื่อมต่อไว้ที่ ${CONFIG} · brain "${brain}" มี ${s.memories} ความจำ`)
  },

  // ส่งไฟล์ความจำของ Claude Code ทุกโปรเจกต์ (หรือโปรเจกต์เดียว) ไฟล์ดัชนี MEMORY.md ถูกข้าม
  async push() {
    const root = join(CLAUDE, 'projects')
    const projects = (await readdir(root).catch(() => [])).filter((p) => !flags.project || p === flags.project)
    if (flags.project && !projects.length) fail(`ไม่พบโปรเจกต์ "${flags.project}" ใน ${root}`)
    const inputs = [], sources = []
    for (const project of projects) {
      const dir = join(root, project, 'memory')
      for (const file of (await readdir(dir).catch(() => [])).filter((f) => f.endsWith('.md') && f !== 'MEMORY.md')) {
        const parsed = parse(await readFile(join(dir, file), 'utf8'), file.replace(/\.md$/, ''))
        const source = `${project}/${file}`.slice(0, 191), subject = `${PREFIX}${project}/${parsed.name}`.slice(0, 191)
        const parts = [parsed.description, ...chunk(parsed.body)].filter(Boolean)
        if (!parts.length) continue
        sources.push(source)
        parts.forEach((raw, i) => inputs.push({ text: redact(raw).slice(0, 2000), subject, attribute: i === 0 && parsed.description ? 'description' : `p${i}`, kind: kindOf(parsed.type), source }))
      }
    }
    console.log(`พบ ${sources.length} ไฟล์ จาก ${projects.length} โปรเจกต์ · ${inputs.length} ชิ้น · ปิดข้อมูลลับ ${redactions} จุด → brain "${brain}"`)
    if (flags.dry) return console.log('โหมด --dry: ไม่ได้ส่งอะไร')
    // ส่งซ้ำได้: ของเดิมจากไฟล์เดียวกันถูกลบก่อน แล้วจึงใส่ใหม่
    for (const source of sources) await call('DELETE', '/v1/sources' + q({ brain, source }))
    const refused = []
    for (let i = 0; i < inputs.length; i += 100) {
      refused.push(...(await sendBatch(inputs.slice(i, i + 100))).refused)
      process.stdout.write(`\rส่งแล้ว ${Math.min(i + 100, inputs.length)}/${inputs.length}`)
    }
    console.log(inputs.length ? '\nเสร็จ' : 'ไม่มีอะไรให้ส่ง')
    // panya ไม่เก็บความลับ: ชิ้นที่ดูเหมือนรหัสผ่าน/key/token ถูกปฏิเสธ ให้แก้ไฟล์ต้นทางแล้วส่งใหม่ถ้าต้องการ
    if (refused.length) console.log(`ข้าม ${refused.length} ชิ้นที่ดูเหมือนมีความลับ:\n  ` + [...new Set(refused)].join('\n  '))
  },

  // บริบทตั้งต้น: ค่าปัจจุบันของทุกคีย์ ความชอบ และความจำล่าสุด (ข้อความพร้อมใช้)
  async context() {
    conn ??= await config()
    const res = await fetch(conn.url + '/v1/context' + q({ brain, format: 'text', days: flags.days || 30 }), { headers: { authorization: 'Bearer ' + conn.key } })
      .catch((e) => fail(`ติดต่อ panya ที่ ${conn.url} ไม่ได้: ${e.cause?.code || e.message}`))
    if (!res.ok) fail(`panya ตอบ ${res.status}: ${(await res.json().catch(() => ({}))).error || ''}`)
    console.log(await res.text())
  },

  // ทุกรุ่นของคีย์หนึ่ง ใหม่สุดก่อน รวมค่าที่ถูกแทนแล้ว
  async history() {
    if (words.length < 2) fail('ใช้: history <subject> <attribute>')
    const r = await call('GET', '/v1/history' + q({ brain, subject: words[0], attribute: words[1] }))
    if (!r.versions.length) return console.log('ไม่มีประวัติของคีย์นี้')
    for (const m of r.versions) console.log(`${new Date(m.createdAt).toISOString().slice(0, 10)} ${m.active ? '(ปัจจุบัน)' : `(ถูกแทน ${m.invalidAt ? new Date(m.invalidAt).toISOString().slice(0, 10) : ''})`} ${m.text}`)
  },

  async search() {
    const query = words.join(' ')
    if (!query) fail('ใช้: search <คำถาม>')
    const body = { brain, q: query, limit: Math.max(1, Math.min(20, Number(flags.limit) || 8)) }
    if (flags['as-of']) body.asOf = flags['as-of'] // ค้นเหมือนย้อนไป ณ วันนั้น
    const r = await call('POST', '/v1/search', body)
    if (r.abstained) return console.log(`panya เลือกไม่ตอบ: ไม่มีความจำที่เกี่ยวข้องพอ (${r.reason || 'no_match'}) · ถือว่าไม่รู้ อย่าเดา`)
    for (const h of r.hits) console.log(`[${h.score.toFixed(2)}] ${h.source || h.subject || '-'}\n${h.text}\n`)
  },

  // เก็บข้อเท็จจริงเดียว · ถ้าให้ --subject และ --attribute ค่าใหม่จะแทนค่าเดิมของคีย์เดียวกัน
  async remember() {
    const text = words.join(' ')
    if (!text) fail('ใช้: remember <ข้อความ> [--subject s --attribute a] [--kind fact|preference|event]')
    const r = await tryCall('POST', '/v1/memories', { brain, text, subject: flags.subject, attribute: flags.attribute, kind: flags.kind, source: flags.source })
    if (isSecretRefusal(r)) fail('panya ไม่เก็บ: ข้อความนี้ดูเหมือนมีรหัสผ่าน key หรือ token · เอาความลับออกแล้วส่งใหม่')
    if (!r.ok) fail(`panya ตอบ ${r.status}: ${r.data?.error || ''}`)
    r.action = r.data.action; r.memory = r.data.memory
    console.log(`${{ created: 'เก็บใหม่', superseded: 'แทนค่าเดิม', merged: 'รวมกับที่ซ้ำ' }[r.action]} · id ${r.memory.id}`)
  },

  async list() {
    const filter = (words[0] || '').toLowerCase()
    const all = (await remote()).filter((s) => !filter || s.subject.toLowerCase().includes(filter) || s.description.toLowerCase().includes(filter))
    let project = ''
    for (const s of all) {
      if (s.project !== project) console.log(`\n${(project = s.project)}`)
      console.log(`  ${s.name}  [${s.count} ชิ้น]  ${s.description.slice(0, 120)}`)
    }
    console.log(`\n${all.length} ความจำ จาก ${new Set(all.map((s) => s.project)).size} โปรเจกต์ ใน brain "${brain}"`)
  },

  async show() {
    if (!words[0]) fail('ใช้: show <โปรเจกต์>/<ชื่อความจำ>  (ดูชื่อจาก list)')
    const all = await remote(), want = words[0]
    const hit = all.filter((s) => `${s.project}/${s.name}` === want || s.name === want)
    if (!hit.length) fail(`ไม่พบความจำ "${want}" ใน brain "${brain}"`)
    for (const s of hit) console.log(`\n===== ${s.project}/${s.name} =====\n` + (await rebuild(s)))
  },

  // เขียนความจำของโปรเจกต์หนึ่งกลับเป็นไฟล์ .md ต้องระบุโฟลเดอร์ปลายทางเอง เพื่อไม่ให้ทับความจำที่ใช้อยู่โดยไม่ตั้งใจ
  async pull() {
    if (!words[0] || !flags.to) fail('ใช้: pull <โปรเจกต์> --to <โฟลเดอร์> [--force]')
    const all = (await remote()).filter((s) => s.project === words[0])
    if (!all.length) fail(`ไม่พบโปรเจกต์ "${words[0]}" ใน brain "${brain}" · ดูชื่อจาก list`)
    await mkdir(flags.to, { recursive: true })
    for (const s of all) {
      const path = join(flags.to, s.name.replace(/[\\/:*?"<>|]/g, '_') + '.md')
      if (!flags.force && (await stat(path).catch(() => null))) { console.log('ข้าม (มีอยู่แล้ว) ' + path); continue }
      await writeFile(path, await rebuild(s))
      console.log('เขียน ' + path)
    }
    console.log('หมายเหตุ: ข้อความที่ถูกปิดเป็น [redacted] กู้คืนไม่ได้ และไฟล์ดัชนี MEMORY.md ไม่ได้ถูกสร้างให้')
  },
}

if (!commands[cmd]) {
  console.error('คำสั่ง: setup | push | search | context | history | remember | list | show | pull   (ดูวิธีใช้ที่หัวไฟล์)')
  process.exitCode = 1
} else try {
  await commands[cmd]()
} catch (e) {
  console.error(e instanceof Fail ? e.message : e)
  process.exitCode = 1
}
