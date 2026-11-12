// fb-page-read.mjs: อ่านอย่างเดียว เปิดเพจ/ลิงก์แชร์ เลื่อนฟีด เก็บข้อความโพสต์ ลิงก์ และภาพหน้าจอ
// ใช้: node fb-page-read.mjs <url> <outdir> [--scrolls 80]
import { openContext, loginState, arg, log, sleep } from './common.mjs';
import fs from 'node:fs'; import path from 'node:path';
const [url, out] = process.argv.slice(2).filter((a) => !a.startsWith('--'));
const N = Number(arg('scrolls', '80'));
const ctx = await openContext({ headless: true });
const page = ctx.pages()[0] || await ctx.newPage();
try {
  if (!(await loginState(ctx)).facebook) throw new Error('ยังไม่ล็อกอิน Facebook');
  await page.goto(url, { waitUntil: 'domcontentloaded', timeout: 90000 }); await sleep(8000);
  log('page', 'url', page.url());
  await page.screenshot({ path: path.join(out, 'top.png') });
  fs.writeFileSync(path.join(out, 'top.txt'), await page.evaluate(() => document.body.innerText.slice(0, 6000)));
  const posts = new Map();
  for (let i = 0; i < N; i++) {
    const got = await page.evaluate(() => [...document.querySelectorAll('[role="article"], div[aria-posinset]')].map((a) => {
      a.querySelectorAll('div[role="button"]').forEach((b) => { if (/^(ดูเพิ่มเติม|See more)$/.test(b.innerText.trim())) b.click(); });
      const links = [...a.querySelectorAll('a[href]')].map((x) => x.href).filter((h) => /\/(posts|reel|videos|photo|permalink|watch)/.test(h));
      return { text: a.innerText.slice(0, 4000), link: links[0] || '' };
    }));
    for (const g of got) { const k = g.text.slice(0, 200); if (!posts.has(k) || posts.get(k).text.length < g.text.length) posts.set(k, g); }
    await page.mouse.wheel(0, 2500); await sleep(2200);
    if (i % 10 === 9) { log('page', `scroll ${i + 1} posts ${posts.size}`); fs.writeFileSync(path.join(out, 'posts.json'), JSON.stringify([...posts.values()], null, 1)); }
  }
  fs.writeFileSync(path.join(out, 'posts.json'), JSON.stringify([...posts.values()], null, 1));
  await page.screenshot({ path: path.join(out, 'end.png') });
  log('page', 'done', posts.size);
} finally { await ctx.close(); }
