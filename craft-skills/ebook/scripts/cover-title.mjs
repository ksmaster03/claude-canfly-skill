/**
 * cover-title.mjs <config.json> — วางตัวอักษรไทยลงบนภาพปกที่เจนมาแล้ว
 *
 * ทำไมต้องมี: ห้ามให้โมเดลภาพเขียนตัวอักษรไทย (เพี้ยนทุกครั้ง) จึงสั่ง "NO text" ตอนเจน
 * แล้วเอาชื่อเรื่องมาทับทีหลังด้วย Chromium ซึ่ง shape ภาษาไทยได้ถูกต้อง (เหตุผลเดียวกับที่ PDF ใช้ Chromium)
 *
 * ‼ ต้องรันจาก $CHATGPT_BRIDGE (node_modules ของ playwright อยู่ที่นั่น)
 *   cp <skill>/scripts/cover-title.mjs /d/Project/chatgpt-bridge/
 *   cd /d/Project/chatgpt-bridge && node cover-title.mjs /path/to/covers.json
 *
 * รูปแบบ config.json — เป็น array ทำได้หลายปกในรอบเดียว:
 * [{
 *   "image":   "$WORK/x-ebook/images/cover.jpg",   // ปกต้นฉบับ (ไม่มีตัวอักษร)
 *   "out":     "$WORK/x-ebook/images/cover.jpg",   // เขียนทับได้ (สำรอง cover-plain ให้อัตโนมัติ)
 *   "fontsDir":"$WORK/x-ebook/fonts",
 *   "kicker":  "E-BOOK 2026 · 16 บท",
 *   "title":   ["บรรทัดบน", "บรรทัดล่าง"],              // 1–3 บรรทัด
 *   "subtitle":"คำโปรยใต้ชื่อเรื่อง",
 *   "footer":  "แถบล่างสุด (ออปชัน)",
 *   "accent":  "#fbbf24",                               // สีของ kicker
 *   "scrim":   "rgba(10,6,3,.72)"                       // สีม่านหลังตัวอักษรด้านบน
 * }]
 */
import { chromium } from 'playwright';
import { readFile, writeFile, copyFile, access } from 'node:fs/promises';
import path from 'node:path';

const cfgPath = process.argv[2];
if (!cfgPath) { console.error('ใช้: node cover-title.mjs <config.json>'); process.exit(1); }
const items = JSON.parse(await readFile(cfgPath, 'utf-8'));

const b64 = async (p) => (await readFile(p)).toString('base64');
const exists = async (p) => access(p).then(() => true, () => false);
const mimeOf = (p) => (p.toLowerCase().endsWith('.png') ? 'image/png' : 'image/jpeg');

const browser = await chromium.launch();

for (const it of items) {
  const W = it.width ?? 1024, H = it.height ?? 1536;
  const accent = it.accent ?? '#fbbf24';
  const scrim = it.scrim ?? 'rgba(10,6,3,.72)';

  // สำรองต้นฉบับไว้เสมอถ้าจะเขียนทับ
  if (path.resolve(it.out) === path.resolve(it.image)) {
    const plain = it.image.replace(/(\.[a-z]+)$/i, '-plain$1');
    if (!(await exists(plain))) await copyFile(it.image, plain);
  }

  const fonts = it.fontsDir;
  const face = async (w, weight) =>
    `@font-face{font-family:'Sarabun';font-weight:${weight};font-style:normal;` +
    `src:url(data:font/ttf;base64,${await b64(path.join(fonts, `Sarabun-${w}.ttf`))}) format('truetype');}`;
  const fontCss = [await face('SemiBold', 600), await face('Bold', 700), await face('ExtraBold', 800)].join('\n');

  const bg = `data:${mimeOf(it.image)};base64,${await b64(it.image)}`;
  const titleHtml = (it.title ?? []).map((l) => `<div>${l}</div>`).join('');

  const html = `<!doctype html><html><head><meta charset="utf-8"><style>
${fontCss}
*{margin:0;padding:0;box-sizing:border-box}
html,body{width:${W}px;height:${H}px;overflow:hidden}
.wrap{position:relative;width:${W}px;height:${H}px;font-family:'Sarabun',sans-serif}
.bg{position:absolute;inset:0;background:url('${bg}') center/cover no-repeat}
.top{position:absolute;top:0;left:0;right:0;padding:56px 64px 90px;text-align:center;
  background:linear-gradient(180deg,${scrim} 0%,${scrim} 55%,rgba(0,0,0,0) 100%)}
.kicker{font-weight:700;font-size:26px;letter-spacing:.28em;color:${accent};text-transform:uppercase;margin-bottom:18px}
.title{font-weight:800;font-size:${it.titleSize ?? 76}px;line-height:1.16;color:#fff;letter-spacing:-.01em;
  text-shadow:0 4px 24px rgba(0,0,0,.55)}
.sub{margin-top:20px;font-weight:600;font-size:${it.subSize ?? 30}px;line-height:1.45;color:#f2e9e0;
  text-shadow:0 2px 12px rgba(0,0,0,.5)}
.foot{position:absolute;left:0;right:0;bottom:0;padding:26px 64px 34px;text-align:center;
  background:linear-gradient(0deg,${scrim} 0%,${scrim} 60%,rgba(0,0,0,0) 100%);
  font-weight:700;font-size:27px;color:#fff;letter-spacing:.02em;text-shadow:0 2px 12px rgba(0,0,0,.5)}
</style></head><body>
<div class="wrap"><div class="bg"></div>
  <div class="top">
    ${it.kicker ? `<div class="kicker">${it.kicker}</div>` : ''}
    <div class="title">${titleHtml}</div>
    ${it.subtitle ? `<div class="sub">${it.subtitle}</div>` : ''}
  </div>
  ${it.footer ? `<div class="foot">${it.footer}</div>` : ''}
</div></body></html>`;

  const page = await browser.newPage({ viewport: { width: W, height: H }, deviceScaleFactor: 1 });
  await page.setContent(html, { waitUntil: 'load' });
  await page.waitForTimeout(600);
  const buf = await page.screenshot({ type: it.out.toLowerCase().endsWith('.png') ? 'png' : 'jpeg', quality: it.out.toLowerCase().endsWith('.png') ? undefined : 88 });
  await writeFile(it.out, buf);
  await page.close();
  console.log('WROTE', it.out);
}

await browser.close();
console.log('DONE', items.length, 'ปก');
