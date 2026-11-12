#!/usr/bin/env node
// รับส่งความจำและสกิลของ Claude Code กับ panya ผ่าน HTTP · ไม่มี dependency รันด้วย node 18+ หรือ bun
//
//   node panya-sync.mjs status
//   node panya-sync.mjs push memory <โฟลเดอร์ memory ...> | --all   [--go] [--prune] [--no-redact]
//   node panya-sync.mjs push skills [ชื่อสกิล ...]                    [--go] [--prune] [--no-redact]
//   node panya-sync.mjs pull memory <โฟลเดอร์ memory> [--project slug] [--go] [--force]
//   node panya-sync.mjs pull skills [ชื่อสกิล ...]                    [--go] [--force]
//   node panya-sync.mjs list memory|skills
//   node panya-sync.mjs search "<คำถาม>" | --q-file <ไฟล์ utf-8>      [--memory|--skills] [--limit 5]
//
// ไม่ใส่ --go = แสดงแผนอย่างเดียว ไม่ส่ง ไม่เขียนไฟล์
// ตั้งค่าที่ ~/.claude/panya.env (PANYA_URL, PANYA_KEY, PANYA_BRAIN_MEMORY, PANYA_BRAIN_SKILLS) ตัวแปรแวดล้อมชนะไฟล์
//
// รูปแบบที่เก็บ: หนึ่งไฟล์ = ชิ้นข้อความ p1..pn (ตัดตรงขึ้นบรรทัดใหม่ ชิ้นละไม่เกิน 900 ตัวอักษร) + ใบกำกับ attribute "file"
// panya ตัดช่องว่างหัวท้ายของทุกข้อความ ช่องว่างระหว่างชิ้นจึงเก็บไว้ใน ref ของชิ้นถัดไป และของหัวท้ายไฟล์เก็บในใบกำกับ
// ใบกำกับมี sha256 ตอนดึงกลับจะประกอบแล้วเทียบ ไม่ตรงไม่เขียน
import { createHash } from 'node:crypto'
import { mkdir, readFile, readdir, stat, writeFile } from 'node:fs/promises'
import { homedir } from 'node:os'
import { basename, dirname, join, resolve } from 'node:path'
import { pathToFileURL } from 'node:url'

export const MAX_PART = 900
const MAX_FILE_BYTES = 256 * 1024
const BATCH = 100
const SKIP_DIRS = new Set(['node_modules', '.git', '__pycache__', '.venv'])
// synced = สกิลที่ Claude ซิงก์มาเองจากบัญชี ไม่ใช่ของที่เขียนในเครื่อง
const SKIP_SKILLS = new Set(['synced'])
const SKIP_FILE = /(\.pyc$|\.bak($|[-.])|^\.DS_Store$|^Thumbs\.db$)/i

export const sha256 = (data) => createHash('sha256').update(data).digest('hex')

// ── ตัดและประกอบ ─────────────────────────────────────────────────

const isWs = (ch) => ch !== undefined && /\s/.test(ch)
const isLowSurrogate = (ch) => ch !== undefined && ch >= '\uDC00' && ch <= '\uDFFF'

/** ตัด core (ไม่มีช่องว่างหัวท้าย) เป็นชิ้น ทุกชิ้นขึ้นต้นและลงท้ายด้วยตัวอักษรจริง sep = ช่องว่างที่อยู่ก่อนชิ้นนั้น */
export function splitText(core, max = MAX_PART) {
  const out = []
  let pos = 0
  let sepBefore = ''
  while (core.length - pos > max) {
    const limit = pos + max
    let best = null
    let bestPara = null
    const re = /\s*\n\s*/g
    re.lastIndex = pos + 1
    for (let m; (m = re.exec(core)) && m.index <= limit; ) {
      // ref ของ panya ยาวได้ 191 ตัวอักษร
      if (encodeSep(m[0]).length > 180) continue
      best = m
      if (/\n[^\S\n]*\n/.test(m[0]) && m.index >= pos + max / 2) bestPara = m
    }
    const m = bestPara ?? best
    let a
    let b
    if (m) {
      a = m.index
      b = a + m[0].length
    } else {
      // บรรทัดเดียวยาวเกิน: ตัดกลางบรรทัด ตรงที่สองฝั่งเป็นตัวอักษรจริง
      let c = limit
      while (c > pos && (isWs(core[c - 1]) || isWs(core[c]) || isLowSurrogate(core[c]))) c--
      if (c <= pos) throw new Error('ช่องว่างยาวเกินกว่าจะตัดได้')
      a = b = c
    }
    out.push({ text: core.slice(pos, a), sep: sepBefore })
    sepBefore = core.slice(a, b)
    pos = b
  }
  out.push({ text: core.slice(pos), sep: sepBefore })
  return out
}

// ช่องว่างถูกเก็บเป็นตัวอักษรธรรมดา (n r s t หรือ u+รหัส 4 หลัก) ไม่มี backslash หรือเครื่องหมายคำพูดให้ฐานข้อมูลแปลงผิด
const WS_CODE = { '\n': 'n', '\r': 'r', ' ': 's', '\t': 't' }
const WS_CHAR = { n: '\n', r: '\r', s: ' ', t: '\t' }
export const encodeSep = (sep) => [...sep].map((ch) => WS_CODE[ch] ?? 'u' + ch.charCodeAt(0).toString(16).padStart(4, '0')).join('')
export function decodeSep(code) {
  if (typeof code !== 'string' || !/^([nrst]|u[0-9a-f]{4})*$/.test(code)) return null
  const out = code.replace(/u([0-9a-f]{4})|[nrst]/g, (m, hex) => (hex ? String.fromCharCode(parseInt(hex, 16)) : WS_CHAR[m]))
  return /\S/.test(out) ? null : out
}

export const joinParts = (lead, parts, trail) => lead + parts.map((p, i) => (i ? p.sep : '') + p.text).join('') + trail

// ── ปิดข้อมูลลับ ─────────────────────────────────────────────────

const SECRET_PATTERNS = [
  /\b(?:sk|pk|rk)-[A-Za-z0-9_-]{16,}/g,
  /\b[a-z]{2,6}_(?:sk|pk|br|ag|key|secret|token)_[A-Za-z0-9_-]{6,}(?:…|\.\.\.)?/gi,
  /\bgh[opsu]_[A-Za-z0-9]{20,}/g,
  /\bgithub_pat_[A-Za-z0-9_]{20,}/g,
  /\bxox[abprs]-[A-Za-z0-9-]{10,}/g,
  /\bAKIA[0-9A-Z]{16}\b/g,
  /\bAIza[0-9A-Za-z_-]{30,}/g,
  /\bsm_[A-Za-z0-9_-]{16,}/g,
  /\beyJ[A-Za-z0-9_-]{20,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}/g,
  /-----BEGIN [A-Z ]*PRIVATE KEY-----[\s\S]*?-----END [A-Z ]*PRIVATE KEY-----/g,
  /\b[0-9a-f]{32,}\b/gi,
]
// สายอักขระยาวที่หน้าตาเหมือน key: ต้องมีทั้งตัวเลข ตัวเล็ก ตัวใหญ่ และไม่ใช่ path (มี / ไม่เกิน 2 ตัว)
const LONG_RUN = /\b[A-Za-z0-9+/_-]{48,}={0,2}/g
const looksLikeKey = (s) => /[0-9]/.test(s) && /[a-z]/.test(s) && /[A-Z]/.test(s) && (s.match(/\//g) ?? []).length <= 2

export function redact(text) {
  let count = 0
  let out = text
  for (const re of SECRET_PATTERNS) out = out.replace(re, () => (count++, '[redacted]'))
  out = out.replace(LONG_RUN, (s) => (looksLikeKey(s) ? (count++, '[redacted]') : s))
  return { text: out, count }
}

// ── แปลงไฟล์เป็นรายการที่จะส่ง ───────────────────────────────────

const frontField = (raw, key) => {
  const fm = raw.replace(/^﻿/, '').match(/^---\r?\n([\s\S]*?)\r?\n---/)
  const hit = fm?.[1].match(new RegExp(`^\\s*${key}:\\s*(.+)$`, 'm'))
  return hit ? hit[1].trim().replace(/^["']|["']$/g, '') : ''
}

export const sourceOf = (type, scope, rel) => (type === 'skill' ? `claude-skill/user/${scope}/${rel}` : `${scope}/${rel}`)
const subjectOf = (type, scope, rel) => (type === 'skill' ? `claude-skill/user/${scope}/${rel}` : `claude-memory/${scope}/${rel}`)

/** คืน { items, manifest } หรือ { skip: เหตุผล } · bytes = เนื้อไฟล์ดิบ */
export function buildFile({ type, scope, rel, bytes, doRedact = true, now = new Date().toISOString() }) {
  if (bytes.length > MAX_FILE_BYTES) return { skip: 'ใหญ่เกิน 256 KB' }
  let raw
  try {
    raw = new TextDecoder('utf-8', { fatal: true, ignoreBOM: true }).decode(bytes)
  } catch {
    return { skip: 'ไม่ใช่ข้อความ UTF-8' }
  }
  if (raw.includes('\0')) return { skip: 'ไฟล์ไบนารี' }
  const source = sourceOf(type, scope, rel)
  const subject = subjectOf(type, scope, rel)
  if (subject.length > 191) return { skip: 'ชื่อไฟล์ยาวเกิน 191 ตัวอักษร' }

  const lead = raw.slice(0, raw.length - raw.trimStart().length)
  const trail = raw.slice(raw.trimEnd().length)
  const core0 = raw.trim()
  if (!core0) return { skip: 'ไฟล์ว่าง' }
  const r = doRedact ? redact(core0) : { text: core0, count: 0 }
  let parts
  try {
    parts = splitText(r.text)
  } catch (e) {
    return { skip: e.message }
  }
  const stored = lead + r.text + trail
  // ตรวจย้อนกลับทันที: จำลองการตัดช่องว่างของ panya แล้วประกอบ ต้องได้ของเดิมทุกตัวอักษร
  if (joinParts(lead, parts.map((p) => ({ text: p.text.trim(), sep: p.sep })), trail) !== stored) return { skip: 'ตรวจย้อนกลับไม่ผ่าน' }

  const kind = type === 'memory' && /^(feedback|user)$/.test(frontField(raw, 'type')) ? 'preference' : 'fact'
  const base = { subject, source, kind }
  const items = []
  const description = rel.endsWith('.md') ? frontField(raw, 'description') : ''
  if (description) items.push({ ...base, attribute: 'description', text: (doRedact ? redact(description).text : description).slice(0, 2000) })
  parts.forEach((p, i) => items.push({ ...base, attribute: `p${i + 1}`, text: p.text, ...(i ? { ref: 'sep:' + encodeSep(p.sep) } : {}) }))
  const manifest = { v: 1, type, scope, rel, parts: parts.length, sha: sha256(stored), src: sha256(bytes), bytes: bytes.length, redacted: r.count, lead, trail, at: now }
  const text = JSON.stringify(manifest)
  if (text.length > 1900) return { skip: 'ช่องว่างหัวท้ายไฟล์ยาวเกิน' }
  // ใบกำกับอยู่ท้ายสุดเสมอ: ถ้าส่งขาดกลางทาง ใบกำกับจะไม่ถึง แล้วตอนดึงจะเห็นว่าไฟล์ไม่ครบ
  items.push({ ...base, attribute: 'file', text })
  return { items, manifest, source }
}

// ── อ่านสิ่งที่อยู่ใน panya ──────────────────────────────────────

const SAFE_SEGMENT = /^[^\\/:*?"<>|\0]+$/
export const safeRel = (rel) => typeof rel === 'string' && rel.length > 0 && rel.split('/').every((s) => s && s !== '.' && s !== '..' && SAFE_SEGMENT.test(s))
const safeScope = (s) => typeof s === 'string' && s !== '.' && s !== '..' && SAFE_SEGMENT.test(s)

/** จัดความจำที่ส่งออกมาเป็น ใบกำกับ + ชิ้น ต่อหนึ่งไฟล์ */
export function indexRemote(memories) {
  const live = memories.filter((m) => m && m.active !== false).sort((a, b) => (a.createdAt ?? 0) - (b.createdAt ?? 0))
  const manifests = new Map()
  const parts = new Map()
  const sources = new Map()
  for (const m of live) {
    const src = m.source ?? ''
    sources.set(src, (sources.get(src) ?? 0) + 1)
    const pn = /^p(\d+)$/.exec(m.attribute ?? '')
    if (pn) {
      if (!parts.has(src)) parts.set(src, new Map())
      parts.get(src).set(Number(pn[1]), m)
    } else if (m.attribute === 'file') {
      try {
        const mf = JSON.parse(m.text)
        // ข้อมูลจากเซิร์ฟเวอร์ไม่น่าไว้ใจเท่าไฟล์ในเครื่อง: path ต้องผ่านด่านก่อนถูกใช้เขียนไฟล์
        if (mf?.v === 1 && (mf.type === 'memory' || mf.type === 'skill') && safeScope(mf.scope) && safeRel(mf.rel) && sourceOf(mf.type, mf.scope, mf.rel) === src) manifests.set(src, mf)
      } catch {}
    }
  }
  return { manifests, parts, sources }
}

/** ประกอบไฟล์จากชิ้น คืน { text } หรือ { error } */
export function assemble(mf, partMap) {
  const list = []
  for (let i = 1; i <= mf.parts; i++) {
    const m = partMap?.get(i)
    if (!m) return { error: `ขาดชิ้นที่ ${i}/${mf.parts}` }
    let sep = ''
    if (i > 1) {
      sep = decodeSep(String(m.ref ?? '').startsWith('sep:') ? m.ref.slice(4) : null)
      if (sep === null) return { error: `ชิ้นที่ ${i} ข้อมูลช่องว่างผิดรูป` }
    }
    list.push({ text: m.text, sep })
  }
  const text = joinParts(String(mf.lead ?? ''), list, String(mf.trail ?? ''))
  if (sha256(Buffer.from(text, 'utf8')) !== mf.sha) return { error: 'ประกอบแล้ว sha256 ไม่ตรงกับใบกำกับ' }
  return { text }
}

// ── เรียก panya ──────────────────────────────────────────────────

export async function loadConfig(env = process.env, file = join(homedir(), '.claude', 'panya.env')) {
  const conf = {}
  const raw = await readFile(file, 'utf8').catch(() => '')
  for (const line of raw.replace(/^﻿/, '').split(/\r?\n/)) {
    const m = /^\s*([A-Z_]+)\s*=\s*(.*?)\s*$/.exec(line)
    if (m) conf[m[1]] = m[2].replace(/^["']|["']$/g, '')
  }
  const get = (k) => env[k] ?? conf[k] ?? ''
  const url = get('PANYA_URL').replace(/\/+$/, '')
  // บริการฝากสมองของ myWeekend ครอบ panya ไว้อีกชั้น เส้นทางและสิทธิ์ต่างจาก panya ตรง ๆ
  const hosted = /\/api\/brain\/v1$/.test(url)
  return {
    url,
    key: get('PANYA_KEY'),
    hosted,
    brains: { memory: get('PANYA_BRAIN_MEMORY') || (hosted ? '' : 'claude-memory'), skill: get('PANYA_BRAIN_SKILLS') || (hosted ? '' : 'claude-skills') },
    file,
  }
}

const sleep = (ms) => new Promise((r) => setTimeout(r, ms))

export function client(cfg) {
  if (!cfg.url || !cfg.key) throw new Error(`ยังไม่ได้ตั้ง PANYA_URL และ PANYA_KEY (ใส่ในไฟล์ ${cfg.file})`)
  const call = async (method, path, body) => {
    for (let attempt = 0; ; attempt++) {
      let res
      try {
        res = await fetch(cfg.url + path, {
          method,
          headers: { authorization: `Bearer ${cfg.key}`, ...(body === undefined ? {} : { 'content-type': 'application/json' }) },
          body: body === undefined ? undefined : JSON.stringify(body),
        })
      } catch (e) {
        throw new Error(`ต่อ ${new URL(cfg.url).host} ไม่ได้: ${e.cause?.code ?? e.message}`)
      }
      if (res.status === 429 && attempt < 5) {
        await sleep((Number(res.headers.get('retry-after')) || 5) * 1000)
        continue
      }
      const text = await res.text()
      if (!res.ok) throw new Error(`${method} ${path.split('?')[0]} ตอบ ${res.status}: ${text.slice(0, 300)}`)
      try {
        return JSON.parse(text)
      } catch {
        throw new Error(`${method} ${path.split('?')[0]} ตอบ ${res.status} แต่ไม่ใช่ JSON (URL ถูกไหม): ${text.slice(0, 120)}`)
      }
    }
  }
  const v = cfg.hosted ? '' : '/v1'
  const q = (brain, extra = '') => `?brain=${encodeURIComponent(brain)}${extra}`
  return {
    export: async (brain) => (await call('GET', `${v}/export${q(brain)}`)).memories ?? [],
    // panya ปฏิเสธทั้งชุดถ้ามีชิ้นที่ดูเหมือนความลับ: ส่งทีละชิ้นแทน ข้ามเฉพาะชิ้นนั้น แล้วแจ้ง (การตรวจ sha256 หลังส่งจะฟ้องไฟล์ที่ไม่ครบ)
    write: async (brain, memories) => {
      try {
        return await call('POST', cfg.hosted ? '/memories' : '/v1/memories/batch', { ...(brain ? { brain } : {}), memories })
      } catch (e) {
        if (cfg.hosted || !/never stores secrets/.test(e.message)) throw e
        const refused = []
        for (const m of memories) {
          try { await call('POST', '/v1/memories', { brain, ...m }) } catch (e2) {
            if (/never stores secrets/.test(e2.message)) refused.push(m.source)
            else throw e2
          }
        }
        console.error(`\n‼ panya ไม่เก็บ ${refused.length} ชิ้นที่ดูเหมือนข้อมูลลับ (ไฟล์ ${[...new Set(refused)].join(', ')}) · แก้ไฟล์ต้นทางให้เป็นค่าสมมุติแล้ว push ใหม่`)
        return { refused }
      }
    },
    search: (brain, text, limit) => call('POST', `${v}/search`, { ...(brain ? { brain } : {}), q: text, limit }),
    // บริการฝากสมองไม่มีคำสั่งลบ: ของเดิมถูกทับด้วย subject+attribute เดียวกันแทน
    forgetSource: cfg.hosted ? null : (brain, source) => call('DELETE', `/v1/sources${q(brain, `&source=${encodeURIComponent(source)}`)}`),
    health: cfg.hosted ? null : async () => (await fetch(cfg.url + '/health')).status,
  }
}

// ── ไฟล์ในเครื่อง ────────────────────────────────────────────────

async function walk(dir, prefix = '') {
  const out = []
  for (const e of await readdir(dir, { withFileTypes: true }).catch(() => [])) {
    const rel = prefix ? `${prefix}/${e.name}` : e.name
    if (e.isDirectory()) {
      if (!SKIP_DIRS.has(e.name)) out.push(...(await walk(join(dir, e.name), rel)))
    } else if (e.isFile()) out.push(rel)
  }
  return out
}

const isDir = async (p) => (await stat(p).catch(() => null))?.isDirectory() ?? false

/** คืน [{ scope, dir }] ตามที่ผู้ใช้ระบุ */
async function localScopes(type, o) {
  if (type === 'skill') {
    const root = resolve(o.root ?? join(homedir(), '.claude', 'skills'))
    const names = o.names.length ? o.names : (await readdir(root, { withFileTypes: true }).catch(() => [])).filter((e) => e.isDirectory() && !e.name.startsWith('.') && !SKIP_SKILLS.has(e.name)).map((e) => e.name)
    return names.map((n) => ({ scope: n, dir: join(root, n) }))
  }
  let dirs = o.names.map((d) => resolve(d))
  if (o.all) {
    const root = resolve(o.root ?? join(homedir(), '.claude', 'projects'))
    for (const p of await readdir(root).catch(() => [])) if (await isDir(join(root, p, 'memory'))) dirs.push(join(root, p, 'memory'))
  }
  if (!dirs.length) throw new Error('ต้องระบุโฟลเดอร์ memory หรือใส่ --all')
  if (o.project && dirs.length > 1) throw new Error('--project ใช้ได้กับโฟลเดอร์เดียว')
  return dirs.map((dir) => ({ scope: o.project ?? basename(dirname(dir)), dir }))
}

// ── คำสั่ง ───────────────────────────────────────────────────────

const log = (...a) => console.log(...a)
const showList = (title, list, max = 15) => {
  if (!list.length) return
  log(`\n${title} (${list.length})`)
  for (const x of list.slice(0, max)) log(`  ${x}`)
  if (list.length > max) log(`  ... อีก ${list.length - max} รายการ`)
}

export async function push(type, cfg, o) {
  const scopes = await localScopes(type, o)
  for (const s of scopes) if (!safeScope(s.scope) || !(await isDir(s.dir))) throw new Error(`ไม่พบโฟลเดอร์ ${s.dir}`)
  const brain = cfg.brains[type]
  const api = cfg.url && cfg.key ? client(cfg) : null
  if (!api && o.go) client(cfg)
  const remote = api ? indexRemote(await api.export(brain)) : null

  const changed = []
  const skipped = []
  const redacted = []
  const local = new Set()
  let unchanged = 0
  for (const { scope, dir } of scopes) {
    for (const rel of await walk(dir)) {
      if (SKIP_FILE.test(basename(rel))) { skipped.push(`${scope}/${rel} : ไฟล์สำรองหรือไฟล์ชั่วคราว`); continue }
      const built = buildFile({ type, scope, rel, bytes: await readFile(join(dir, rel)), doRedact: !o.noRedact })
      if (built.skip) { skipped.push(`${scope}/${rel} : ${built.skip}`); continue }
      local.add(built.source)
      if (built.manifest.redacted) redacted.push(`${scope}/${rel} : ${built.manifest.redacted} จุด`)
      if (remote?.manifests.get(built.source)?.src === built.manifest.src) unchanged++
      else changed.push(built)
    }
  }
  const inScope = new Set(scopes.map((s) => s.scope))
  const gone = remote ? [...remote.manifests].filter(([src, mf]) => mf.type === type && inScope.has(mf.scope) && !local.has(src)).map(([src]) => src) : []
  const total = changed.reduce((n, b) => n + b.items.length, 0)

  log(`${type === 'skill' ? 'สกิล' : 'ความจำ'} ${scopes.length} ชุด · ไฟล์ที่ต้องส่ง ${changed.length} (${total} ความจำ) · ตรงกับใน panya แล้ว ${unchanged} · ข้าม ${skipped.length} · brain "${brain || '(ค่าตั้งต้นของบัญชี)'}"`)
  if (!remote) log('ยังไม่ได้ตั้งค่า panya: นับจากไฟล์ในเครื่องอย่างเดียว ยังไม่ได้เทียบกับปลายทาง')
  showList('จะส่ง', changed.map((b) => `${b.source} (${b.manifest.parts} ชิ้น)`))
  showList('ปิดข้อมูลลับก่อนส่ง ไฟล์ที่ดึงกลับจะมีคำว่า [redacted] แทน', redacted)
  showList('ข้าม ไม่ถูกส่ง', skipped)
  showList(`อยู่ใน panya แต่ไม่มีในเครื่องแล้ว${o.prune ? ' จะลบออกจาก panya' : ' (ใส่ --prune เพื่อลบ)'}`, gone)
  if (!o.go) return log('\nยังไม่ได้ส่งอะไร ใส่ --go เพื่อส่งจริง'), { changed: changed.length, unchanged, skipped: skipped.length, sent: 0 }

  let queue = []
  let sent = 0
  const flush = async () => {
    if (!queue.length) return
    await api.write(brain, queue)
    sent += queue.length
    queue = []
    if (process.stdout.isTTY) process.stdout.write(`\rส่งแล้ว ${sent}/${total}`)
  }
  for (const b of changed) {
    // ต้องส่งของที่ค้างก่อนลบ ไม่งั้นลำดับลบกับเขียนของไฟล์อื่นสลับกันได้
    if (queue.length + b.items.length > BATCH) await flush()
    if (api.forgetSource && remote.sources.has(b.source)) await api.forgetSource(brain, b.source)
    for (let i = 0; i < b.items.length; i += BATCH) {
      queue.push(...b.items.slice(i, i + BATCH))
      if (queue.length >= BATCH) await flush()
    }
  }
  await flush()
  if (total && process.stdout.isTTY) log('')
  let pruned = 0
  if (o.prune && gone.length) {
    if (!api.forgetSource) log('บริการฝากสมองไม่มีคำสั่งลบ: ข้ามการลบ ต้องลบจากหน้า /account/brain เอง')
    else for (const src of gone) { await api.forgetSource(brain, src); pruned++ }
  }
  // ยืนยันจากปลายทางจริง ไม่เชื่อแค่ว่าคำขอตอบ 2xx
  const after = indexRemote(await api.export(brain))
  const missing = changed.filter((b) => after.manifests.get(b.source)?.src !== b.manifest.src || assemble(after.manifests.get(b.source), after.parts.get(b.source)).error)
  log(`ส่ง ${changed.length} ไฟล์ ${sent} ความจำ · ลบ ${pruned} ไฟล์ · ตรวจกลับจาก panya: ครบ ${changed.length - missing.length}/${changed.length}`)
  showList('‼ ส่งแล้วแต่ตรวจกลับไม่ผ่าน', missing.map((b) => b.source))
  if (missing.length) process.exitCode = 1
  return { changed: changed.length, unchanged, skipped: skipped.length, sent, pruned, missing: missing.length }
}

export async function pull(type, cfg, o) {
  const brain = cfg.brains[type]
  const remote = indexRemote(await client(cfg).export(brain))
  let targets // scope → โฟลเดอร์ปลายทาง
  if (type === 'skill') {
    const root = resolve(o.root ?? join(homedir(), '.claude', 'skills'))
    const want = new Set(o.names)
    targets = (scope) => (!want.size || want.has(scope) ? join(root, scope) : null)
  } else {
    if (o.names.length !== 1) throw new Error('ต้องระบุโฟลเดอร์ memory ปลายทางหนึ่งโฟลเดอร์')
    const dir = resolve(o.names[0])
    const project = o.project ?? basename(dirname(dir))
    targets = (scope) => (scope === project ? dir : null)
  }

  const fresh = []
  const conflict = []
  const broken = []
  const keepLocal = []
  let same = 0
  for (const [src, mf] of remote.manifests) {
    if (mf.type !== type) continue
    const dir = targets(mf.scope)
    if (!dir) continue
    const dest = resolve(dir, mf.rel)
    // ซ้ำกับด่านใน indexRemote โดยตั้งใจ: จุดที่เขียนไฟล์ต้องตรวจเองว่าไม่หลุดออกนอกโฟลเดอร์ปลายทาง
    if (!dest.startsWith(resolve(dir) + (process.platform === 'win32' ? '\\' : '/'))) { broken.push(`${src} : path ออกนอกโฟลเดอร์ปลายทาง`); continue }
    const got = assemble(mf, remote.parts.get(src))
    if (got.error) { broken.push(`${src} : ${got.error}`); continue }
    const item = { src, dest, text: got.text, mf }
    const cur = await readFile(dest).catch(() => null)
    if (cur === null) fresh.push(item)
    else {
      const h = sha256(cur)
      if (h === mf.sha) same++
      else if (h === mf.src) keepLocal.push(src)
      else conflict.push(item)
    }
  }
  const legacy = [...remote.sources.keys()].filter((s) => !remote.manifests.has(s) && s.startsWith('claude-skill/') === (type === 'skill')).length
  const label = (i) => `${i.src}${i.mf.redacted ? `  ‼ มี [redacted] ${i.mf.redacted} จุด` : ''}  (ส่งเมื่อ ${String(i.mf.at).slice(0, 16)})`
  log(`ใน panya brain "${brain || '(ค่าตั้งต้นของบัญชี)'}": ไฟล์ใหม่ ${fresh.length} · ตรงกับในเครื่อง ${same + keepLocal.length} · เนื้อหาต่างจากในเครื่อง ${conflict.length} · ประกอบไม่ได้ ${broken.length}`)
  showList('ไฟล์ใหม่ จะเขียนลงเครื่อง', fresh.map(label))
  showList(`ต่างจากในเครื่อง${o.force ? ' จะเขียนทับ (ยกเว้นไฟล์ที่มี [redacted])' : ' ไม่แตะ (ใส่ --force เพื่อเขียนทับ)'}`, conflict.map(label))
  showList('ในเครื่องเป็นฉบับเต็ม ใน panya ถูกปิดข้อมูลลับ ไม่แตะ', keepLocal)
  showList('‼ ประกอบไม่ได้ ไม่เขียน', broken)
  if (legacy) log(`\nมีอีก ${legacy} แหล่งที่ส่งด้วยสคริปต์รุ่นก่อน (ไม่มีใบกำกับ) ค้นได้ แต่ดึงกลับเป็นไฟล์ไม่ได้`)
  if (!o.go) return log('\nยังไม่ได้เขียนไฟล์ ใส่ --go เพื่อเขียนจริง'), { fresh: fresh.length, conflict: conflict.length, same, broken: broken.length, written: 0 }

  // ไฟล์ที่ถูกปิดข้อมูลลับไม่เขียนทับของในเครื่องไม่ว่ากรณีใด: ของในเครื่องอาจเป็นฉบับเดียวที่มีค่าจริง
  const todo = [...fresh, ...(o.force ? conflict.filter((i) => !i.mf.redacted) : [])]
  for (const i of todo) {
    await mkdir(dirname(i.dest), { recursive: true })
    await writeFile(i.dest, Buffer.from(i.text, 'utf8'))
  }
  let bad = 0
  for (const i of todo) if (sha256(await readFile(i.dest)) !== i.mf.sha) bad++
  log(`เขียน ${todo.length} ไฟล์ · อ่านกลับแล้ว sha256 ตรง ${todo.length - bad}/${todo.length}`)
  if (bad) process.exitCode = 1
  return { fresh: fresh.length, conflict: conflict.length, same, broken: broken.length, written: todo.length }
}

export async function list(type, cfg) {
  const remote = indexRemote(await client(cfg).export(cfg.brains[type]))
  const by = new Map()
  for (const mf of remote.manifests.values()) {
    if (mf.type !== type) continue
    const s = by.get(mf.scope) ?? { files: 0, bytes: 0, redacted: 0, at: '' }
    s.files++
    s.bytes += mf.bytes
    s.redacted += mf.redacted ? 1 : 0
    if (String(mf.at) > s.at) s.at = String(mf.at)
    by.set(mf.scope, s)
  }
  log(`brain "${cfg.brains[type] || '(ค่าตั้งต้นของบัญชี)'}" มี ${by.size} ชุด`)
  for (const [scope, s] of [...by].sort((a, b) => a[0].localeCompare(b[0]))) log(`  ${scope}  ${s.files} ไฟล์  ${(s.bytes / 1024).toFixed(1)} KB  ล่าสุด ${s.at.slice(0, 16)}${s.redacted ? `  มี [redacted] ${s.redacted} ไฟล์` : ''}`)
  return by
}

export async function search(cfg, o) {
  const text = (o.qFile ? await readFile(o.qFile, 'utf8') : o.names.join(' ')).replace(/^﻿/, '').trim()
  if (!text) throw new Error('ต้องระบุคำถาม หรือ --q-file <ไฟล์>')
  const types = o.only ? [o.only] : ['memory', 'skill']
  const brains = [...new Set(types.map((t) => cfg.brains[t]))]
  const api = client(cfg)
  for (const brain of brains) {
    const r = await api.search(brain, text, o.limit)
    // ใบกำกับไม่ใช่เนื้อหา ตัดออกจากผลค้น
    const hits = (r.hits ?? []).filter((h) => h.attribute !== 'file')
    log(`\nbrain "${brain || '(ค่าตั้งต้นของบัญชี)'}" : ${hits.length ? `${hits.length} รายการ` : `ไม่มีคำตอบ${r.reason ? ` (${r.reason})` : ''}`}${r.queriesLeft !== undefined ? ` · โควตาคำถามเหลือ ${r.queriesLeft}` : ''}`)
    for (const h of hits) log(`\n[${Number(h.score ?? 0).toFixed(2)}] ${h.source || h.subject || ''}${h.attribute ? ` #${h.attribute}` : ''}\n${h.text}`)
  }
}

export async function status(cfg) {
  log(`ไฟล์ตั้งค่า: ${cfg.file}`)
  if (!cfg.url || !cfg.key) return log(`ยังไม่ได้ตั้ง ${[!cfg.url && 'PANYA_URL', !cfg.key && 'PANYA_KEY'].filter(Boolean).join(' และ ')}`), false
  log(`ปลายทาง: ${cfg.url} (${cfg.hosted ? 'บริการฝากสมอง myWeekend' : 'panya ตรง'}) · key ลงท้าย ...${cfg.key.slice(-4)}`)
  const api = client(cfg)
  if (api.health) log(`/health ตอบ ${await api.health().catch((e) => `ไม่ได้ (${e.cause?.code ?? e.message})`)}`)
  for (const type of ['memory', 'skill']) {
    const brain = cfg.brains[type]
    if (type === 'skill' && brain === cfg.brains.memory) break
    const r = indexRemote(await api.export(brain))
    const n = (t) => [...r.manifests.values()].filter((m) => m.type === t).length
    log(`brain "${brain || '(ค่าตั้งต้นของบัญชี)'}": ${[...r.sources.values()].reduce((a, b) => a + b, 0)} ความจำ · ไฟล์ความจำ ${n('memory')} · ไฟล์สกิล ${n('skill')} · แหล่งรุ่นก่อนที่ไม่มีใบกำกับ ${[...r.sources.keys()].filter((s) => !r.manifests.has(s)).length}`)
  }
  return true
}

// ── บรรทัดคำสั่ง ─────────────────────────────────────────────────

export function parseArgs(argv) {
  const o = { names: [], limit: 5 }
  const valued = { '--project': 'project', '--root': 'root', '--q-file': 'qFile', '--limit': 'limit' }
  const flags = { '--go': 'go', '--force': 'force', '--prune': 'prune', '--no-redact': 'noRedact', '--all': 'all' }
  for (let i = 0; i < argv.length; i++) {
    const a = argv[i]
    if (valued[a]) o[valued[a]] = argv[++i]
    else if (flags[a]) o[flags[a]] = true
    else if (a === '--memory') o.only = 'memory'
    else if (a === '--skills') o.only = 'skill'
    else if (a.startsWith('--')) throw new Error(`ไม่รู้จักตัวเลือก ${a}`)
    else o.names.push(a)
  }
  o.limit = Math.max(1, Math.min(20, Number(o.limit) || 5))
  return o
}

const TYPES = { memory: 'memory', skills: 'skill', skill: 'skill' }

async function main(argv) {
  const [cmd, ...rest] = argv
  const cfg = await loadConfig()
  if (cmd === 'status') return status(cfg)
  if (cmd === 'search') return search(cfg, parseArgs(rest))
  if (cmd === 'push' || cmd === 'pull' || cmd === 'list') {
    const type = TYPES[rest[0]]
    if (!type) throw new Error(`ต้องระบุ memory หรือ skills ต่อจาก ${cmd}`)
    const o = parseArgs(rest.slice(1))
    return cmd === 'push' ? push(type, cfg, o) : cmd === 'pull' ? pull(type, cfg, o) : list(type, cfg)
  }
  log('ใช้: panya-sync.mjs status | push memory|skills | pull memory|skills | list memory|skills | search  (ดูหัวไฟล์)')
  process.exitCode = 2
}

if (process.argv[1] && import.meta.url === pathToFileURL(resolve(process.argv[1])).href) {
  main(process.argv.slice(2)).catch((e) => {
    console.error(`ผิดพลาด: ${e.message}`)
    process.exitCode = 1
  })
}
