// node --test panya-sync.test.mjs
// ใช้เซิร์ฟเวอร์จำลองที่ทำตัวเหมือน panya ในจุดที่สคริปต์พึ่ง: ตัดช่องว่างหัวท้าย ทับด้วย subject+attribute ลบตาม source ส่งออกทั้ง brain
import assert from 'node:assert/strict'
import { mkdtemp, mkdir, readFile, rm, writeFile } from 'node:fs/promises'
import { createServer } from 'node:http'
import { tmpdir } from 'node:os'
import { join } from 'node:path'
import { after, before, test } from 'node:test'
import { buildFile, decodeSep, encodeSep, indexRemote, joinParts, pull, push, redact, safeRel, sha256, splitText } from './panya-sync.mjs'

const KEY = 'test-key'
let server
let base
let tmp
const brains = new Map()
const calls = []
let clock = 1

function mock(req, res) {
  const url = new URL(req.url, 'http://x')
  const hosted = url.pathname.startsWith('/api/brain/v1')
  const path = hosted ? url.pathname.slice('/api/brain/v1'.length) : url.pathname.replace(/^\/v1/, '')
  const send = (status, body) => { res.writeHead(status, { 'content-type': 'application/json' }); res.end(JSON.stringify(body)) }
  if (req.headers.authorization !== `Bearer ${KEY}`) return send(401, { error: 'unauthorized' })
  let raw = ''
  req.on('data', (c) => (raw += c))
  req.on('end', () => {
    const b = raw ? JSON.parse(raw) : {}
    const brain = (req.method === 'GET' || req.method === 'DELETE' ? url.searchParams.get('brain') : b.brain) || 'default'
    if (!brains.has(brain)) brains.set(brain, [])
    const rows = brains.get(brain)
    calls.push(`${req.method} ${path}`)
    if (req.method === 'GET' && path === '/export') return send(200, { format: 'panya-export', version: 1, memories: rows.filter((m) => m.active) })
    if (req.method === 'POST' && path === (hosted ? '/memories' : '/memories/batch')) {
      if (!Array.isArray(b.memories) || !b.memories.length || b.memories.length > 200) return send(400, { error: 'bad batch' })
      for (const m of b.memories) {
        if (typeof m.text !== 'string' || !m.text.trim() || m.text.length > 2000) return send(400, { error: 'bad text' })
        for (const f of ['subject', 'attribute', 'source', 'ref']) if (m[f] !== undefined && (typeof m[f] !== 'string' || m[f].length > 191)) return send(400, { error: `invalid ${f}` })
      }
      for (const m of b.memories) {
        for (const old of rows) if (old.active && old.subject === m.subject && old.attribute === m.attribute) old.active = false
        rows.push({ text: m.text.trim(), subject: m.subject, attribute: m.attribute, kind: m.kind, source: m.source ?? '', ref: m.ref ?? '', createdAt: clock++, active: true })
      }
      return send(201, { results: [] })
    }
    if (!hosted && req.method === 'DELETE' && path === '/sources') {
      const source = url.searchParams.get('source')
      brains.set(brain, rows.filter((m) => m.source !== source))
      return send(200, { ok: true })
    }
    send(404, { error: 'not found' })
  })
}

const cfgFor = (hosted, name) => ({ url: base + (hosted ? '/api/brain/v1' : ''), key: KEY, hosted, brains: { memory: name, skill: name }, file: 'test' })
const quiet = async (fn) => {
  // ปิดเฉพาะ console.log: ถ้าปิด process.stdout.write ผลของเทสต์ข้อก่อนหน้าจะหายไปด้วย
  const orig = console.log
  console.log = () => {}
  try { return await fn() } finally { console.log = orig }
}
const put = async (dir, rel, data) => { await mkdir(join(dir, rel, '..'), { recursive: true }); await writeFile(join(dir, rel), data) }

const fakeKey = 'sk-' + 'a1B2c3D4'.repeat(4)
const TRICKY = {
  'SKILL.md': '---\nname: demo\ndescription: สกิลทดลอง\n---\n\n# หัวข้อ\n\nย่อหน้าภาษาไทย สระ วรรณยุกต์ น้ำ ก็ ผู้\n\n' + 'บรรทัดยาว '.repeat(300) + '\n\n```js\n    indented()\n\tตัวแท็บ\n```\n',
  'crlf.md': '\uFEFF---\r\nname: crlf\r\n---\r\n\r\nline one\r\n\r\n\r\n   line two with lead\r\n' + 'x'.repeat(40) + '\r\n' + ('row of text here\r\n'.repeat(120)) + '\r\n\r\n',
  'scripts/long.py': 'x = "' + 'ก😀b'.repeat(900) + '"\n' + '    def f():\n        return 1\n'.repeat(80),
  'nospace.txt': 'Z'.repeat(5000),
  'ws-edge.txt': '\n\n   \t\nbody\n   \n\n',
  'deep/a/b/c.json': JSON.stringify({ a: [1, 2, 3], s: 'ข้อความ' }, null, 2),
}

before(async () => {
  tmp = await mkdtemp(join(tmpdir(), 'panya-sync-'))
  server = createServer(mock)
  await new Promise((r) => server.listen(0, '127.0.0.1', r))
  base = `http://127.0.0.1:${server.address().port}`
})
after(async () => {
  server.close()
  await rm(tmp, { recursive: true, force: true })
})

test('ตัดแล้วประกอบได้เท่าเดิม แม้ทุกชิ้นถูกตัดช่องว่างหัวท้าย', () => {
  for (const [name, text] of Object.entries(TRICKY)) {
    const core = text.trim()
    const parts = splitText(core)
    for (const p of parts) {
      assert.ok(p.text.length <= 900 && p.text === p.text.trim() && p.text, name)
      assert.ok(encodeSep(p.sep).length <= 180 && decodeSep(encodeSep(p.sep)) === p.sep, name)
    }
    assert.equal(joinParts('', parts, ''), core, name)
  }
})

test('ไม่ตัดกลางอักขระคู่ (emoji)', () => {
  for (const p of splitText('😀'.repeat(2000))) assert.ok(!/^[\uDC00-\uDFFF]/.test(p.text) && !/[\uD800-\uDBFF]$/.test(p.text))
})

test('ส่งแล้วดึงกลับได้ตรงทุกไบต์ และส่งซ้ำไม่มีอะไรต้องส่ง', async () => {
  const src = join(tmp, 'a-skills')
  for (const [rel, data] of Object.entries(TRICKY)) await put(join(src, 'demo'), rel, data)
  await put(join(src, 'demo'), 'font.bin', Buffer.from([0, 255, 254, 0, 1]))
  await put(join(src, 'demo'), 'old.py.bak-20260101', 'x')
  await put(join(src, 'demo'), 'node_modules/x/index.js', 'x')
  const cfg = cfgFor(false, 'rt')

  const dry = await quiet(() => push('skill', cfg, { names: [], root: src }))
  assert.equal(dry.sent, 0)
  assert.equal(brains.get('rt')?.length ?? 0, 0, 'ไม่ใส่ --go ต้องไม่เขียนอะไร')

  const r1 = await quiet(() => push('skill', cfg, { names: [], root: src, go: true }))
  assert.deepEqual([r1.changed, r1.skipped, r1.missing], [6, 2, 0])
  const r2 = await quiet(() => push('skill', cfg, { names: [], root: src, go: true }))
  assert.deepEqual([r2.changed, r2.unchanged, r2.sent], [0, 6, 0])

  const dst = join(tmp, 'b-skills')
  const p0 = await quiet(() => pull('skill', cfg, { names: [], root: dst }))
  assert.deepEqual([p0.fresh, p0.written], [6, 0])
  await assert.rejects(readFile(join(dst, 'demo', 'SKILL.md')), 'ไม่ใส่ --go ต้องไม่เขียนไฟล์')
  const p1 = await quiet(() => pull('skill', cfg, { names: [], root: dst, go: true }))
  assert.deepEqual([p1.written, p1.broken], [6, 0])
  for (const rel of Object.keys(TRICKY)) assert.ok((await readFile(join(dst, 'demo', rel))).equals(await readFile(join(src, 'demo', rel))), rel)
  await assert.rejects(readFile(join(dst, 'demo', 'font.bin')))
})

test('ไฟล์ที่แก้ถูกส่งใหม่ไฟล์เดียว ปลายทางที่ต่างกันไม่ถูกทับจนกว่าจะสั่ง --force', async () => {
  const src = join(tmp, 'a-skills')
  const dst = join(tmp, 'b-skills')
  const cfg = cfgFor(false, 'rt')
  await put(join(src, 'demo'), 'nospace.txt', 'สั้นลง')
  const r = await quiet(() => push('skill', cfg, { names: ['demo'], root: src, go: true }))
  assert.deepEqual([r.changed, r.unchanged, r.missing], [1, 5, 0])
  assert.equal(brains.get('rt').filter((m) => m.source.endsWith('nospace.txt')).length, 2, 'ชิ้นเก่าต้องถูกลบ เหลือ 1 ชิ้น + ใบกำกับ')

  const p = await quiet(() => pull('skill', cfg, { names: [], root: dst, go: true }))
  assert.deepEqual([p.conflict, p.written], [1, 0])
  assert.equal(await readFile(join(dst, 'demo', 'nospace.txt'), 'utf8'), 'Z'.repeat(5000))
  const f = await quiet(() => pull('skill', cfg, { names: [], root: dst, go: true, force: true }))
  assert.equal(f.written, 1)
  assert.equal(await readFile(join(dst, 'demo', 'nospace.txt'), 'utf8'), 'สั้นลง')
})

test('--prune ลบไฟล์ที่ไม่มีในเครื่องแล้ว เฉพาะชุดที่กำลังส่ง', async () => {
  const src = join(tmp, 'p-skills')
  await put(join(src, 'one'), 'SKILL.md', 'one')
  await put(join(src, 'one'), 'gone.md', 'gone')
  await put(join(src, 'two'), 'SKILL.md', 'two')
  const cfg = cfgFor(false, 'prune')
  await quiet(() => push('skill', cfg, { names: [], root: src, go: true }))
  await rm(join(src, 'one', 'gone.md'))
  await rm(join(src, 'two'), { recursive: true })
  await quiet(() => push('skill', cfg, { names: ['one'], root: src, go: true }))
  assert.equal(indexRemote(brains.get('prune')).manifests.size, 3, 'ไม่ใส่ --prune ต้องไม่ลบ')
  const r = await quiet(() => push('skill', cfg, { names: ['one'], root: src, go: true, prune: true }))
  assert.equal(r.pruned, 1)
  assert.deepEqual([...indexRemote(brains.get('prune')).manifests.keys()].sort(), ['claude-skill/user/one/SKILL.md', 'claude-skill/user/two/SKILL.md'])
})

test('ความจำ: ข้อมูลลับถูกปิดก่อนส่ง และฉบับเต็มในเครื่องไม่ถูกทับ', async () => {
  const dir = join(tmp, 'projects', 'd--Project-x', 'memory')
  const body = `---\nname: ref_key\ndescription: ที่เก็บ key\nmetadata:\n  type: feedback\n---\n\nkey คือ ${fakeKey} ห้ามหลุด\n`
  await put(dir, 'ref_key.md', body)
  await put(dir, 'MEMORY.md', '- [key](ref_key.md)\n')
  const cfg = cfgFor(false, 'mem')
  const r = await quiet(() => push('memory', cfg, { names: [dir], go: true }))
  assert.deepEqual([r.changed, r.missing], [2, 0])
  const rows = brains.get('mem')
  assert.ok(!JSON.stringify(rows).includes(fakeKey), 'key ต้องไม่ถึงเซิร์ฟเวอร์')
  assert.ok(rows.some((m) => m.text.includes('[redacted]')))
  assert.equal(rows.find((m) => m.attribute === 'p1' && m.source.endsWith('ref_key.md')).kind, 'preference')
  assert.equal(rows.find((m) => m.attribute === 'description').text, 'ที่เก็บ key')
  assert.equal((await quiet(() => push('memory', cfg, { names: [dir], go: true }))).changed, 0, 'ไฟล์ที่ถูกปิดข้อมูลลับต้องไม่ถูกส่งซ้ำทุกรอบ')

  const p = await quiet(() => pull('memory', cfg, { names: [dir], go: true, force: true }))
  assert.equal(p.written, 0)
  assert.equal(await readFile(join(dir, 'ref_key.md'), 'utf8'), body)

  // ในเครื่องแก้ต่อไปแล้ว (ไม่ตรงทั้งฉบับเต็มและฉบับที่ถูกปิด): --force ก็ต้องไม่ทับด้วยฉบับที่มี [redacted]
  await writeFile(join(dir, 'ref_key.md'), body + 'แก้เพิ่ม\n')
  const p2 = await quiet(() => pull('memory', cfg, { names: [dir], go: true, force: true }))
  assert.deepEqual([p2.conflict, p2.written], [1, 0])
  assert.equal(await readFile(join(dir, 'ref_key.md'), 'utf8'), body + 'แก้เพิ่ม\n')

  // เครื่องใหม่ที่ slug ต่างกัน: ระบุ --project แล้วได้ไฟล์ที่มี [redacted]
  const other = join(tmp, 'projects', 'other-slug', 'memory')
  assert.equal((await quiet(() => pull('memory', cfg, { names: [other], go: true }))).fresh, 0)
  const q = await quiet(() => pull('memory', cfg, { names: [other], project: 'd--Project-x', go: true }))
  assert.equal(q.written, 2)
  assert.equal(await readFile(join(other, 'ref_key.md'), 'utf8'), body.replace(fakeKey, '[redacted]'))
})

test('ตัวจับข้อมูลลับไม่ทำลาย path ยาว', () => {
  const path = '$PROJECTS/some-long-folder/another-long-folder/yet-another-folder/file-name-here'
  assert.equal(redact(path).count, 0)
  assert.equal(redact('AKIA' + 'ABCDEFGHIJKLMNOP').count, 1)
  assert.equal(redact('mw_br_' + 'Z2nLRs9xQ').count, 1)
})

test('ใบกำกับที่ชี้ออกนอกโฟลเดอร์ถูกทิ้ง ชิ้นที่ถูกแก้ไม่ถูกเขียน', async () => {
  assert.ok(!safeRel('../evil') && !safeRel('/abs') && !safeRel('a//b') && !safeRel('C:/x') && !safeRel('a\\..\\b') && safeRel('a/b.md'))
  const cfg = cfgFor(false, 'evil')
  const mk = (scope, rel, source) => {
    const b = buildFile({ type: 'skill', scope, rel: 'ok.md', bytes: Buffer.from('payload') })
    const mf = { ...b.manifest, scope, rel }
    return [{ text: 'payload', subject: source, attribute: 'p1', source, active: true }, { text: JSON.stringify(mf), subject: source, attribute: 'file', source, active: true }]
  }
  brains.set('evil', [
    ...mk('demo', '../../escaped.md', 'claude-skill/user/demo/../../escaped.md'),
    ...mk('..', 'x.md', 'claude-skill/user/../x.md'),
    ...mk('demo', 'moved.md', 'claude-skill/user/other/moved.md'),
    ...mk('demo', 'good.md', 'claude-skill/user/demo/good.md'),
    ...mk('demo', 'tampered.md', 'claude-skill/user/demo/tampered.md').map((m) => (m.attribute === 'p1' ? { ...m, text: 'rm -rf' } : m)),
  ])
  const dst = join(tmp, 'e-skills')
  const r = await quiet(() => pull('skill', cfg, { names: [], root: dst, go: true }))
  assert.deepEqual([r.written, r.broken], [1, 1])
  assert.equal(await readFile(join(dst, 'demo', 'good.md'), 'utf8'), 'payload')
  await assert.rejects(readFile(join(tmp, 'escaped.md')))
  await assert.rejects(readFile(join(dst, 'demo', 'tampered.md')))
})

test('บริการฝากสมอง (ไม่มีคำสั่งลบ): ไฟล์ที่สั้นลงยังดึงกลับได้ตรง', async () => {
  const src = join(tmp, 'h-skills')
  const cfg = cfgFor(true, 'hosted')
  const long = Object.values(TRICKY)[0]
  await put(join(src, 'demo'), 'SKILL.md', long)
  calls.length = 0
  assert.equal((await quiet(() => push('skill', cfg, { names: [], root: src, go: true }))).missing, 0)
  await put(join(src, 'demo'), 'SKILL.md', '# สั้น\n\nเหลือสองบรรทัด\n')
  assert.equal((await quiet(() => push('skill', cfg, { names: [], root: src, go: true }))).missing, 0)
  assert.ok(!calls.some((c) => c.startsWith('DELETE')), 'ต้องไม่เรียกคำสั่งลบ')
  assert.ok(brains.get('hosted').filter((m) => m.active && /^p\d+$/.test(m.attribute)).length > 1, 'ชิ้นเก่ายังค้างอยู่ที่ปลายทาง')
  const dst = join(tmp, 'h-out')
  await quiet(() => pull('skill', cfg, { names: [], root: dst, go: true }))
  assert.equal(await readFile(join(dst, 'demo', 'SKILL.md'), 'utf8'), '# สั้น\n\nเหลือสองบรรทัด\n')
})

test('key ผิดต้องล้มพร้อมข้อความ ไม่เงียบ', async () => {
  await assert.rejects(quiet(() => pull('skill', { ...cfgFor(false, 'rt'), key: 'wrong' }, { names: [] })), /401/)
  assert.equal(sha256(Buffer.from('a')).length, 64)
})
