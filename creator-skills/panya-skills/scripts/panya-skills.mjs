#!/usr/bin/env node
// รับ-ส่ง skill ของ Claude Code กับ panya ผ่าน HTTP API · ใช้ Node 18+ อย่างเดียว ไม่มี dependency
//   node panya-skills.mjs setup --key <api key> [--url $PANYA_URL]
//   node panya-skills.mjs push [--only <ชื่อ>] [--plugins] [--dry]
//   node panya-skills.mjs list [คำกรอง]
//   node panya-skills.mjs search <คำถาม>
//   node panya-skills.mjs show <ชื่อ>
//   node panya-skills.mjs pull <ชื่อ> [--to <โฟลเดอร์>] [--force]
// ทุกคำสั่งรับ --brain <ชื่อ> (ค่าตั้งต้น claude-skills)
import { mkdir, readdir, readFile, stat, writeFile } from 'node:fs/promises'
import { homedir } from 'node:os'
import { basename, dirname, join, relative } from 'node:path'

const CLAUDE = join(homedir(), '.claude')
const CONFIG = join(CLAUDE, 'panya.json')
// panya บนคลาวด์ (AWS กรุงเทพ ผ่าน Cloudflare) · เปลี่ยนได้ด้วย setup --url หรือตัวแปร PANYA_URL
const DEFAULT_URL = '$PANYA_URL'
const PREFIX = 'claude-skill/'

// ── อาร์กิวเมนต์ ──────────────────────────────────────────────────
const argv = process.argv.slice(2)
const cmd = argv[0]
const VALUE_FLAGS = new Set(['--url', '--key', '--brain', '--only', '--to'])
const flags = {}, words = []
for (let i = 1; i < argv.length; i++) {
  if (VALUE_FLAGS.has(argv[i])) flags[argv[i].slice(2)] = argv[++i]
  else if (argv[i].startsWith('--')) flags[argv[i].slice(2)] = true
  else words.push(argv[i])
}
const brain = flags.brain || 'claude-skills'
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
// เหมือน call แต่ไม่จบโปรแกรมเมื่อเซิร์ฟเวอร์ตอบ error
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
    else if (isSecretRefusal(one)) refused.push(m.source || m.subject)
    else fail(`panya ตอบ ${one.status}: ${one.data?.error || ''}`)
  }
  return { sent, refused }
}

// ── แปลงไฟล์ markdown เป็นชิ้นความจำ (ตรงกับ src/import-md.ts ของ panya) ──
function parse(raw, fallbackName) {
  const text = raw.replace(/^﻿/, '').replace(/\r\n/g, '\n')
  const m = text.match(/^---\n([\s\S]*?)\n---\n?([\s\S]*)$/)
  if (!m) return { name: fallbackName, description: '', body: text.trim() }
  const field = (k) => { const hit = m[1].match(new RegExp(`^\\s*${k}:\\s*(.+)$`, 'm')); return hit ? hit[1].trim().replace(/^["']|["']$/g, '') : '' }
  return { name: field('name') || fallbackName, description: field('description'), body: m[2].trim() }
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
// โทเคนและ key ที่ติดมาในเนื้อหาถูกปิดก่อนส่งออกจากเครื่อง
const SECRETS = [
  /\b(?:sk|pk|rk)-[A-Za-z0-9_-]{16,}/g, /\b[a-z]{2,6}_(?:sk|pk|key|secret|token)_[A-Za-z0-9_-]{6,}(?:…|\.\.\.)?/gi, /\bgh[opsu]_[A-Za-z0-9]{20,}/g,
  /\bAKIA[0-9A-Z]{16}\b/g, /\bAIza[0-9A-Za-z_-]{30,}/g, /\bsm_[A-Za-z0-9_-]{16,}/g, /\beyJ[A-Za-z0-9_-]{20,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}/g,
  /\b[0-9a-f]{32,}\b/gi, /\b[A-Za-z0-9+/_-]{48,}={0,2}/g,
]
let redactions = 0
const redact = (text) => SECRETS.reduce((out, re) => out.replace(re, () => { redactions++; return '[redacted]' }), text)

// ── หา skill บนเครื่องนี้ ──────────────────────────────────────────
async function walk(dir, out = []) {
  for (const e of await readdir(dir, { withFileTypes: true }).catch(() => [])) {
    if (e.name === '.trash' || e.name === 'node_modules' || e.name === '.git') continue
    const p = join(dir, e.name)
    if (e.isDirectory()) await walk(p, out)
    else if (e.name.toLowerCase().endsWith('.md')) out.push(p)
  }
  return out
}
async function localSkills() {
  const skills = new Map()
  const roots = [['user', join(CLAUDE, 'skills')], ...(flags.plugins ? [['plugin', join(CLAUDE, 'plugins')]] : [])]
  for (const [origin, root] of roots) {
    const mds = await walk(root)
    for (const file of mds.filter((f) => basename(f) === 'SKILL.md')) {
      const dir = dirname(file), parsed = parse(await readFile(file, 'utf8'), basename(dir))
      const key = `${origin}/${parsed.name}`, mtime = (await stat(file)).mtimeMs
      // ชื่อซ้ำ (เช่น plugin หลายรุ่นในแคช) เอาไฟล์ที่ใหม่กว่า
      if (skills.get(key)?.mtime >= mtime) continue
      skills.set(key, { origin, name: parsed.name, dir, mtime, files: mds.filter((f) => f.startsWith(dir + '\\') || f.startsWith(dir + '/')) })
    }
  }
  for (const f of (await readdir(join(CLAUDE, 'commands')).catch(() => [])).filter((n) => n.endsWith('.md'))) {
    const name = f.replace(/\.md$/, '')
    skills.set(`command/${name}`, { origin: 'command', name, dir: join(CLAUDE, 'commands'), mtime: 0, files: [join(CLAUDE, 'commands', f)] })
  }
  return [...skills.values()].filter((s) => !flags.only || s.name === flags.only)
}

// ── ชื่อ subject ↔ skill ───────────────────────────────────────────
// subject = claude-skill/<origin>/<ชื่อ skill>/<ทางของไฟล์ใน skill>
const split = (subject) => { const [, origin, name, ...rel] = subject.split('/'); return { origin, name, rel: rel.join('/') } }
const ORDER = { user: 0, command: 1, plugin: 2 }
async function remoteSkills() {
  const { subjects } = await call('GET', '/v1/subjects' + q({ brain, prefix: PREFIX }))
  const by = new Map()
  for (const s of subjects) {
    const { origin, name, rel } = split(s.subject)
    if (!name) continue
    const k = `${origin}/${name}`, e = by.get(k) ?? { origin, name, description: '', files: [], chunks: 0 }
    e.files.push({ subject: s.subject, rel }); e.chunks += s.count
    if (s.description && (rel === 'SKILL.md' || !e.description)) e.description = s.description
    by.set(k, e)
  }
  return [...by.values()].sort((a, b) => a.name.localeCompare(b.name) || ORDER[a.origin] - ORDER[b.origin])
}
async function findRemote(name) {
  if (!name) fail('ต้องระบุชื่อ skill')
  const hit = (await remoteSkills()).filter((s) => s.name === name)
  if (!hit.length) fail(`ไม่พบ skill ชื่อ "${name}" ใน brain "${brain}" · ลอง: list ${name}`)
  return hit[0]
}
// ประกอบไฟล์กลับจากชิ้นความจำตามลำดับ
async function rebuild(skill, file) {
  const { memories } = await call('GET', '/v1/memories' + q({ brain, subject: file.subject }))
  const desc = memories.find((m) => m.attribute === 'description')?.text
  const body = memories.filter((m) => m.attribute !== 'description').map((m) => m.text).join('\n\n')
  const front = file.rel === 'SKILL.md' ? `---\nname: ${skill.name}\ndescription: ${desc || ''}\n---\n\n` : desc ? `---\ndescription: ${desc}\n---\n\n` : ''
  return front + body + '\n'
}
const mainFirst = (files) => files.slice().sort((a, b) => (b.rel === 'SKILL.md') - (a.rel === 'SKILL.md') || a.rel.localeCompare(b.rel))

// ── คำสั่ง ─────────────────────────────────────────────────────────
const commands = {
  async setup() {
    if (!flags.key) fail('ใช้: setup --key <api key จากหน้า บัญชีและ API> [--url $PANYA_URL]')
    await mkdir(CLAUDE, { recursive: true })
    await writeFile(CONFIG, JSON.stringify({ url: (flags.url || DEFAULT_URL).replace(/\/+$/, ''), key: flags.key }, null, 2) + '\n', { mode: 0o600 })
    const s = await call('GET', '/v1/stats' + q({ brain }))
    console.log(`บันทึกการเชื่อมต่อไว้ที่ ${CONFIG} · brain "${brain}" มี ${s.memories} ความจำ`)
  },

  async push() {
    const skills = await localSkills()
    const inputs = [], sources = []
    let skipped = 0
    for (const s of skills) {
      for (const file of s.files) {
        const rel = relative(s.dir, file).replace(/\\/g, '/'), source = `${PREFIX}${s.origin}/${s.name}/${rel}`
        if (source.length > 191) { skipped++; continue }
        const parsed = parse(await readFile(file, 'utf8'), rel)
        const parts = [parsed.description, ...chunk(parsed.body)].filter(Boolean)
        if (!parts.length) continue
        sources.push(source)
        parts.forEach((raw, i) => inputs.push({ text: redact(raw).slice(0, 2000), subject: source, attribute: i === 0 && parsed.description ? 'description' : `p${i}`, kind: 'fact', source }))
      }
    }
    console.log(`พบ ${skills.length} skill · ${sources.length} ไฟล์ · ${inputs.length} ชิ้น · ปิดข้อมูลลับ ${redactions} จุด${skipped ? ` · ข้าม ${skipped} ไฟล์ที่ทางยาวเกิน` : ''} → brain "${brain}"`)
    if (flags.dry) return console.log('โหมด --dry: ไม่ได้ส่งอะไร')
    // ส่งซ้ำได้: ของเดิมจากไฟล์เดียวกันถูกลบก่อน แล้วจึงใส่ใหม่
    for (const source of sources) await call('DELETE', '/v1/sources' + q({ brain, source }))
    const refused = []
    for (let i = 0; i < inputs.length; i += 100) {
      refused.push(...(await sendBatch(inputs.slice(i, i + 100))).refused)
      process.stdout.write(`\rส่งแล้ว ${Math.min(i + 100, inputs.length)}/${inputs.length}`)
    }
    console.log(inputs.length ? '\nเสร็จ' : 'ไม่มีอะไรให้ส่ง')
    // panya ไม่เก็บความลับ: ชิ้นที่ถูกปฏิเสธจะขาดหายจากไฟล์ที่ดึงกลับ ให้แก้ไฟล์ต้นทางแล้วส่งใหม่
    if (refused.length) console.log(`ข้าม ${refused.length} ชิ้นที่ดูเหมือนมีความลับ (ไฟล์เหล่านี้จะดึงกลับได้ไม่ครบ):\n  ` + [...new Set(refused)].join('\n  '))
  },

  async list() {
    const filter = (words[0] || '').toLowerCase()
    const skills = (await remoteSkills()).filter((s) => !filter || s.name.toLowerCase().includes(filter) || s.description.toLowerCase().includes(filter))
    for (const s of skills) console.log(`${s.name}  [${s.origin} · ${s.files.length} ไฟล์ · ${s.chunks} ชิ้น]\n    ${s.description.slice(0, 160) || '(ไม่มีคำอธิบาย)'}`)
    console.log(`\n${skills.length} skill ใน brain "${brain}"`)
  },

  async search() {
    const query = words.join(' ')
    if (!query) fail('ใช้: search <คำถาม>')
    const r = await call('POST', '/v1/search', { brain, q: query, limit: 20 })
    if (r.abstained) return console.log(`ไม่พบ skill ที่เกี่ยวข้องพอ (${r.reason || 'no_match'})`)
    const by = new Map()
    for (const h of r.hits.filter((h) => h.subject.startsWith(PREFIX))) {
      const { name } = split(h.subject)
      if (!by.has(name)) by.set(name, h)
    }
    for (const [name, h] of by) console.log(`${name}  (คะแนน ${h.score.toFixed(2)})\n    ${h.text.replace(/\s+/g, ' ').slice(0, 200)}`)
    console.log(`\nเปิดอ่านทั้งตัวด้วย: show <ชื่อ>`)
  },

  async show() {
    const skill = await findRemote(words[0])
    for (const file of mainFirst(skill.files)) console.log(`\n===== ${skill.name}/${file.rel} =====\n` + (await rebuild(skill, file)))
  },

  async pull() {
    const skill = await findRemote(words[0])
    const to = flags.to || join(CLAUDE, skill.origin === 'command' ? 'commands' : join('skills', skill.name))
    if (skill.origin !== 'command' && !flags.force && (await stat(to).catch(() => null))) fail(`มีโฟลเดอร์ ${to} อยู่แล้ว · ใส่ --force เพื่อเขียนทับ หรือ --to <โฟลเดอร์อื่น>`)
    for (const file of skill.files) {
      const path = join(to, file.rel)
      if (skill.origin === 'command' && !flags.force && (await stat(path).catch(() => null))) fail(`มีไฟล์ ${path} อยู่แล้ว · ใส่ --force เพื่อเขียนทับ`)
      await mkdir(dirname(path), { recursive: true })
      await writeFile(path, await rebuild(skill, file))
      console.log('เขียน ' + path)
    }
    console.log('หมายเหตุ: panya เก็บเฉพาะไฟล์ .md · สคริปต์และไฟล์ประกอบอื่นของ skill ไม่ได้มาด้วย และข้อความที่ถูกปิดเป็น [redacted] กู้คืนไม่ได้')
  },
}

if (!commands[cmd]) {
  console.error('คำสั่ง: setup | push | list | search | show | pull   (ดูวิธีใช้ที่หัวไฟล์)')
  process.exitCode = 1
} else try {
  await commands[cmd]()
} catch (e) {
  console.error(e instanceof Fail ? e.message : e)
  process.exitCode = 1
}
