// เรนเดอร์โปสเตอร์ HTML เป็น PNG ด้วย Chromium + ตรวจในตัว (ฟอนต์โหลดจริงไหม / ข้อความ / ตำแหน่งกล่อง)
// ใช้: node render.mjs <poster.html> <out.png> [scale=2] [height=1350] [--check "คำ1|คำ2"] [--boxes ".a,.b"]
// playwright: ใช้ของ $CHATGPT_BRIDGE (ตั้ง env CHATGPT_BRIDGE) ถ้าไม่ตั้ง จะใช้ playwright ที่ติดตั้งในโปรเจกต์ปัจจุบัน
import { createRequire } from 'node:module';
import { pathToFileURL } from 'node:url';
const require = createRequire(process.env.CHATGPT_BRIDGE ? process.env.CHATGPT_BRIDGE.replace(/[\/]+$/, '') + '/package.json' : process.cwd() + '/package.json');
const { chromium } = require('playwright');

const args = process.argv.slice(2);
const flag = (n) => { const i = args.indexOf(n); return i >= 0 ? args.splice(i, 2)[1] : null; };
const check = flag('--check');
const boxes = flag('--boxes');
const [html, out, scale = '2', height = '1350'] = args;
if (!html || !out) { console.error('usage: node render.mjs <html> <out.png> [scale] [height] [--check "a|b"] [--boxes ".x,.y"]'); process.exit(1); }

const b = await chromium.launch();
const p = await b.newPage({ viewport: { width: 1080, height: Number(height) }, deviceScaleFactor: Number(scale) });
await p.goto(pathToFileURL(html).href, { waitUntil: 'load' });
await p.evaluate(() => document.fonts.ready);
const fonts = await p.evaluate(() => [...document.fonts].map(f => `${f.family}:${f.weight}:${f.status}`));
console.log('fonts', fonts.join(' '));
if (fonts.some(f => f.endsWith(':error'))) console.log('!! มีฟอนต์โหลดไม่ขึ้น ภาพจะออกมาเป็นฟอนต์สำรอง');
if (check) {
  const text = await p.evaluate(() => document.body.innerText);
  for (const w of check.split('|')) console.log(text.includes(w) ? 'OK  ' : 'MISS', w);
}
if (boxes) {
  const r = await p.evaluate((sel) => sel.split(',').map(s => {
    const e = document.querySelector(s.trim()); if (!e) return s + ' (ไม่พบ)';
    const c = e.getBoundingClientRect(); return `${s.trim()} x ${Math.round(c.left)}-${Math.round(c.right)} y ${Math.round(c.top)}-${Math.round(c.bottom)}`;
  }), boxes);
  console.log(r.join('\n'));
}
await p.screenshot({ path: out });
await b.close();
console.log('saved', out);
