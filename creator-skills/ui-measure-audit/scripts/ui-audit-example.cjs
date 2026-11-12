// ตรวจ UX/UI ตามวิธีของ prom-design: วัดจริงทุกหน้า หลายความกว้าง แล้วรายงานเป็นตัวเลข
//   เลนส์ภาพ: screens (scrollHeight / viewport), ล้นแนวนอน, ข้อความถูกตัด, เป้าแตะเล็กกว่า 44px, ขีดยาวในข้อความที่แสดง
//   เลนส์ contrast: วัดจากพิกเซลที่เรนเดอร์จริง ไม่ใช่จากค่า token
const fs = require('fs'), path = require('path')
const { chromium } = require('$WORK/pwtest/node_modules/playwright')
const { PNG } = require('$WORK/pwtest/node_modules/playwright-core/lib/utilsBundle')
const key = fs.readFileSync('$PROJECTS/panya/.env', 'utf8').match(/^PANYA_API_KEYS=([^,@\r\n]+)/m)[1]
const base = 'http://127.0.0.1:6800', out = path.join(__dirname, 'audit')
fs.mkdirSync(out, { recursive: true })
const WIDTHS = [[320, 640], [375, 812], [768, 1024], [1280, 800], [1440, 900]]

const lum = ([r, g, b]) => { const f = (v) => { v /= 255; return v <= 0.03928 ? v / 12.92 : ((v + 0.055) / 1.055) ** 2.4 }; return 0.2126 * f(r) + 0.7152 * f(g) + 0.0722 * f(b) }
const ratio = (a, b) => { const x = lum(a), y = lum(b); return (Math.max(x, y) + 0.05) / (Math.min(x, y) + 0.05) }
// พื้น = สีที่พบมากที่สุดในกรอบ, ตัวอักษร = พิกเซลที่ต่างจากพื้นมากที่สุด (แกนกลางของเส้นตัวอักษร)
function contrastOf(buf) {
  const png = PNG.sync.read(buf), count = new Map()
  for (let i = 0; i < png.data.length; i += 4) { const k = (png.data[i] >> 2) + ',' + (png.data[i + 1] >> 2) + ',' + (png.data[i + 2] >> 2); count.set(k, (count.get(k) || 0) + 1) }
  const bg = [...count.entries()].sort((a, b) => b[1] - a[1])[0][0].split(',').map((v) => v * 4 + 2)
  let best = 1
  for (let i = 0; i < png.data.length; i += 4) best = Math.max(best, ratio(bg, [png.data[i], png.data[i + 1], png.data[i + 2]]))
  return best
}

// วัดในหน้า: ข้อมูลที่มาจากความจำ (ข้อความ คำถาม ชื่อแหล่ง) ไม่นับเป็นข้อความของหน้า
const measure = (dataSel) => {
  const vis = (el) => { const r = el.getBoundingClientRect(), s = getComputedStyle(el); return r.width > 0 && r.height > 0 && s.visibility !== 'hidden' && s.display !== 'none' && el.offsetParent !== null }
  const own = Array.from(document.querySelectorAll('body *')).filter((el) => vis(el) && !el.closest(dataSel))
  const small = Array.from(document.querySelectorAll('button, a, input, [role="button"], th[tabindex], tr[tabindex]')).filter(vis).map((el) => {
    const r = el.getBoundingClientRect(), row = el.tagName === 'TR' || el.tagName === 'TH'
    return { el: (el.id ? '#' + el.id : el.className ? '.' + String(el.className).split(' ')[0] : el.tagName.toLowerCase()) + (el.dataset.range ? `[${el.dataset.range}]` : ''), w: Math.round(r.width), h: Math.round(r.height), bad: r.height < 43.5 || (!row && r.width < 43.5) }
  }).filter((x) => x.bad)
  const uniq = (a) => [...new Map(a.map((x) => [x.el + x.h, x])).values()]
  return {
    screens: +(document.documentElement.scrollHeight / innerHeight).toFixed(2),
    overflowX: document.documentElement.scrollWidth - innerWidth,
    dashes: [...new Set(own.filter((el) => el.children.length === 0 && /[\u2013\u2014]/.test(el.textContent)).map((el) => el.textContent.trim().slice(0, 40)))],
    truncated: [...new Set(own.filter((el) => el.scrollWidth > el.clientWidth + 1 && getComputedStyle(el).overflow.includes('hidden') && el.children.length === 0).map((el) => (el.id ? '#' + el.id : '.' + (el.className || el.tagName)) + ' "' + el.textContent.trim().slice(0, 28) + '"'))],
    small: uniq(small).map((x) => `${x.el} ${x.w}x${x.h}`),
    letterSpacedThai: [...new Set(own.filter((el) => el.children.length === 0 && /[\u0E00-\u0E7F]/.test(el.textContent) && parseFloat(getComputedStyle(el).letterSpacing) > 0).map((el) => (el.id ? '#' + el.id : el.tagName.toLowerCase() + (el.className ? '.' + String(el.className).split(' ')[0] : '')) + ' ' + getComputedStyle(el).letterSpacing))],
  }
}

async function contrast(page, selectors) {
  const rows = []
  for (const sel of selectors) {
    const el = page.locator(sel).first()
    if (!(await el.count()) || !(await el.isVisible().catch(() => false))) continue
    await el.scrollIntoViewIfNeeded().catch(() => {})
    const box = await el.boundingBox()
    if (!box || box.width < 4 || box.height < 4) continue
    const size = await el.evaluate((e) => parseFloat(getComputedStyle(e).fontSize))
    const shot = await page.screenshot({ clip: { x: Math.max(0, box.x), y: Math.max(0, box.y), width: Math.min(box.width, 400), height: Math.min(box.height, 60) } })
    const c = contrastOf(shot), need = size >= 24 ? 3 : 4.5
    rows.push({ sel, size, c: +c.toFixed(2), ok: c >= need })
  }
  return rows
}

;(async () => {
  const browser = await chromium.launch({ executablePath: '~/AppData/Local/ms-playwright/chromium-1217/chrome-win64/chrome.exe' })
  const report = []
  const pages = {
    'brain:gate': { url: '/brain', data: '.hit, #tip' },
    'brain:open': { url: '/brain', data: '.hit, #tip, .legend', login: async (p) => { await p.fill('#container', 'claude-memory'); await p.fill('#key', key); await p.click('#enter'); await p.waitForSelector('#gate', { state: 'hidden' }); await p.fill('#q', 'Stock Aging Report'); await p.click('#go'); await p.waitForTimeout(1800) } },
    'dashboard:gate': { url: '/dashboard', data: '.ev p, .ev strong, #strips, tbody td:first-child' },
    'dashboard:open': { url: '/dashboard', data: '.ev p, .ev strong, .strip .lab span, tbody td:first-child', login: async (p) => { await p.fill('#key', key); await p.click('#enter'); await p.waitForSelector('#gate', { state: 'hidden' }); await p.waitForTimeout(2500) } },
  }
  for (const [name, def] of Object.entries(pages)) {
    for (const [w, h] of WIDTHS) {
      const ctx = await browser.newContext({ viewport: { width: w, height: h }, locale: 'th-TH', hasTouch: w < 800, isMobile: w < 800 })
      const page = await ctx.newPage(), errors = []
      page.on('pageerror', (e) => errors.push(e.message))
      page.on('console', (m) => { if (m.type() === 'error') errors.push(m.text().slice(0, 80) + ' @ ' + m.location().url.replace(base, '')) })
      await page.goto(base + def.url); await page.waitForTimeout(700)
      if (def.login) await def.login(page)
      const m = await page.evaluate(measure, def.data)
      await page.screenshot({ path: path.join(out, `${name.replace(':', '-')}-${w}.png`), fullPage: true })
      report.push({ page: name, w, ...m, errors })
      await ctx.close()
    }
  }
  for (const r of report) console.log(`${r.page} @${r.w}: screens ${r.screens} | overflowX ${r.overflowX} | dashes ${JSON.stringify(r.dashes)} | truncated ${r.truncated.length} | small targets ${r.small.length} | thai letter-spacing ${r.letterSpacedThai.length} | errors ${r.errors.length}`)
  const at = (p, w) => report.find((r) => r.page === p && r.w === w)
  for (const p of ['brain:open', 'dashboard:open', 'dashboard:gate', 'brain:gate']) {
    const r = at(p, 375)
    console.log(`\n--- ${p} @375 detail ---\nsmall: ${r.small.join(' | ') || 'none'}\ntruncated: ${r.truncated.join(' | ') || 'none'}\nthai letter-spacing: ${r.letterSpacedThai.join(' | ') || 'none'}\nerrors: ${[...new Set(r.errors)].join(' | ') || 'none'}`)
  }
  console.log(`\n--- dashboard:open @1440 ---\ntruncated: ${at('dashboard:open', 1440).truncated.join(' | ') || 'none'}\nsmall: ${at('dashboard:open', 1440).small.join(' | ') || 'none'}`)

  // contrast จากพิกเซลจริง ที่ 1440 และ 375
  for (const w of [1440, 375]) {
    const ctx = await browser.newContext({ viewport: { width: w, height: 900 }, locale: 'th-TH' })
    const page = await ctx.newPage()
    await page.goto(base + '/dashboard'); await pages['dashboard:open'].login(page)
    const d = await contrast(page, ['.kpi small', '.kpi em', '#writes-sub', '#search-sub', '.strip .lab span', '.strip .lab b', '.ev time', '.ev small', '.ev p', '.ev .dir', 'thead th', 'tfoot td', 'tbody td:nth-child(3)', '#hud-line', '#hud-foot span', '.flow span', '#flow-in i', '#flow-out i', '#feed-panel .legend span', '#live-text', '.tabs button[aria-pressed="false"]', '.tabs button[aria-pressed="true"]', '.state', '#pause', '#lang', 'h2', '#enter', '.nav a[aria-current="page"]', '.nav a:not([aria-current])', '#scroll-hint'])
    await page.goto(base + '/brain'); await page.waitForTimeout(800)
    await pages['brain:open'].login(page)
    const b = await contrast(page, ['#stats', '#hud span', 'aside h2', '.hit small', '.hit p', '.legend span', '#go', '.nav a[aria-current="page"]', '.nav a:not([aria-current])', '#export', '#spin', 'h1 span'])
    console.log(`\n--- contrast from rendered pixels @${w} (need 4.5:1, or 3:1 at 24px+) ---`)
    for (const [pg, rows] of [['dashboard', d], ['brain', b]]) for (const r of rows) console.log(`${r.ok ? 'pass' : 'FAIL'} ${r.c.toFixed(2).padStart(5)}  ${pg} ${r.sel} (${r.size}px)`)
    await ctx.close()
  }
  await browser.close()
})().catch((e) => { console.error('FAILED', e.stack); process.exit(1) })
