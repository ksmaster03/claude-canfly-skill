// fb-reels-list.mjs: อ่านอย่างเดียว เลื่อนแท็บ Reels ของเพจ เก็บลิงก์ /reel/ พร้อมยอดวิวที่ขึ้นบนการ์ด
// ใช้: node fb-reels-list.mjs <reels_tab_url> <outdir> [--scrolls 60]
import { openContext, loginState, arg, log, sleep } from './common.mjs';
import fs from 'node:fs'; import path from 'node:path';
const [url, out] = process.argv.slice(2).filter((a) => !a.startsWith('--'));
const N = Number(arg('scrolls', '60'));
const ctx = await openContext({ headless: true });
const page = ctx.pages()[0] || await ctx.newPage();
try {
  if (!(await loginState(ctx)).facebook) throw new Error('ยังไม่ล็อกอิน Facebook');
  await page.goto(url, { waitUntil: 'domcontentloaded', timeout: 90000 }); await sleep(8000);
  const reels = new Map(); let still = 0;
  for (let i = 0; i < N && still < 6; i++) {
    const got = await page.evaluate(() => [...document.querySelectorAll('a[href*="/reel/"]')].map((a) => ({ href: a.href.split('?')[0], views: a.innerText.trim() })));
    const before = reels.size;
    for (const g of got) if (!reels.has(g.href) || (!reels.get(g.href).views && g.views)) reels.set(g.href, g);
    still = reels.size === before ? still + 1 : 0;
    await page.mouse.wheel(0, 3000); await sleep(2000);
    if (i % 10 === 9) log('reels', `scroll ${i + 1} reels ${reels.size}`);
  }
  fs.writeFileSync(path.join(out, 'reels.json'), JSON.stringify([...reels.values()], null, 1));
  log('reels', 'done', reels.size);
} finally { await ctx.close(); }
