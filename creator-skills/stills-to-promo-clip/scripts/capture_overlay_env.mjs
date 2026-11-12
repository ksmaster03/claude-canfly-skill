// Render a promo overlay page frame by frame to transparent PNGs.
// Usage: OV_HTML=overlay_villain.html OV_OUT=overlay_villain node _mp_capture2.mjs [fromFrame] [toFrame]
// (kept in this folder because playwright is installed here; the pages live in the promo folder)
import { chromium } from 'playwright';
import { mkdirSync } from 'node:fs';
import path from 'node:path';
import { pathToFileURL } from 'node:url';

const HERE = '$PROJECTS/ASUS_X9_Mission Possible/promo';
const FPS = 24, TOTAL = 32 * FPS;
const from = Number(process.argv[2] || 1), to = Number(process.argv[3] || TOTAL);
const out = path.join(HERE, process.env.OV_OUT || 'overlay');
mkdirSync(out, { recursive: true });

const browser = await chromium.launch();
const page = await browser.newPage({ viewport: { width: 1920, height: 1080 } });
await page.goto(pathToFileURL(path.join(HERE, process.env.OV_HTML || 'overlay.html')).href);
await page.evaluate(() => document.fonts.ready);
await page.waitForTimeout(800);
for (let f = from; f <= to; f++) {
  await page.evaluate(t => window.render(t), (f - 1) / FPS);
  await page.screenshot({ path: path.join(out, `ov_${String(f).padStart(4, '0')}.png`), omitBackground: true });
  if (f % 96 === 0) console.log('frame', f);
}
await browser.close();
console.log('done', from, to);
