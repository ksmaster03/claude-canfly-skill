// ตรวจหน้าเว็บหลังใส่ component ใหม่ อ่านอย่างเดียว ไม่เขียนอะไรลงเว็บ
// ใช้: node verify-widths.cjs <base-url> <path,path> [ตัวเลือก css ของสิ่งที่ต้องซ่อนเมื่อไม่มี JS] [เขียนภาพไปโฟลเดอร์]
// ตัวอย่าง: node verify-widths.cjs http://127.0.0.1:8765 /,/th/ .gf-root ./shots
// ตั้ง PW_PATH ถ้า Playwright อยู่ที่อื่น ใช้ Chrome ของเครื่องจึงไม่ต้องดาวน์โหลด browser เพิ่ม
const path = require('path');
const fs = require('fs');
const PW = process.env.PW_PATH || '@playwright/test';
const { chromium } = require(PW);

const [base, paths = '/', noJsHidden = '', outDir = ''] = process.argv.slice(2);
if (!base) { console.error('ต้องระบุ base url'); process.exit(2); }
// Git Bash แปลง /,/th/ เป็น path ของ Windows ก่อนถึงสคริปต์ จึงต้องรันจาก PowerShell
if (paths.split(',').some(u => !u.startsWith('/'))) { console.error('path ถูก Git Bash แปลง: ' + paths + ' ให้รันจาก PowerShell'); process.exit(2); }
const WIDTHS = [320, 390, 768, 900, 901, 950, 1000, 1001, 1024, 1100, 1139, 1140, 1341, 1440, 1920];
const IGNORE = /\/cdn-cgi\//; // สคริปต์ที่ Cloudflare ฉีดเอง ไม่มีบนเครื่อง

let fails = 0;
const fail = m => { console.log('FAIL ' + m); fails++; };

(async () => {
  const b = await chromium.launch({ channel: 'chrome' });
  if (outDir) fs.mkdirSync(outDir, { recursive: true });
  for (const url of paths.split(',')) {
    let checked = 0;
    for (const w of WIDTHS) {
      const ctx = await b.newContext({ viewport: { width: w, height: 800 } });
      const p = await ctx.newPage();
      const errs = [];
      p.on('pageerror', e => errs.push('js: ' + e.message));
      p.on('response', r => { if (r.status() >= 400 && !IGNORE.test(r.url())) errs.push(r.status() + ' ' + r.url()); });
      await p.goto(base + url, { waitUntil: 'load' });
      await p.waitForTimeout(150);
      const m = await p.evaluate(() => {
        const head = document.querySelector('header');
        const kids = head ? [...head.querySelectorAll('*')].filter(e => e.getClientRects().length) : [];
        return {
          ox: document.documentElement.scrollWidth - innerWidth,
          headOver: kids.length ? Math.round(Math.max(...kids.map(e => e.getBoundingClientRect().right)) - innerWidth) : 0,
        };
      });
      checked++;
      if (m.ox > 0) fail(`${url} @${w} ล้นแนวนอน ${m.ox}px`);
      if (m.headOver > 0) fail(`${url} @${w} header ล้นขอบ ${m.headOver}px`);
      if (errs.length) fail(`${url} @${w} ${errs.slice(0, 3).join(' | ')}`);
      await ctx.close();
    }
    console.log(`${url}: ตรวจ ${checked} ความกว้าง`);

    const ctx = await b.newContext({ viewport: { width: 1440, height: 900 }, javaScriptEnabled: false });
    const p = await ctx.newPage();
    await p.goto(base + url, { waitUntil: 'load' });
    if (noJsHidden) {
      const seen = await p.locator(noJsHidden + ':visible').count();
      if (seen) fail(`${url} ไม่มี JS แต่ยังเห็น ${noJsHidden} ${seen} ชิ้น`);
    }
    if (outDir) await p.screenshot({ path: path.join(outDir, `nojs${url.replace(/\W+/g, '-')}.png`), fullPage: true });
    await ctx.close();
  }
  await b.close();
  console.log(fails ? `\n${fails} FAILED` : '\nALL PASSED');
  process.exit(fails ? 1 : 0);
})().catch(e => { console.error(e); process.exit(1); });
