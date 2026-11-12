// สำรวจ UI ของหน้า Scheduled ก่อนอัดจริง
const { chromium } = await import('file:///$PROJECTS/chatgpt-bridge/node_modules/playwright/index.mjs');
import { writeFile } from 'node:fs/promises';

const ROOT = '__ROOT__';
const ctx = await chromium.launchPersistentContext(ROOT + '/claude-data', {
  headless: false,
  viewport: { width: 1440, height: 900 },
  args: ['--disable-blink-features=AutomationControlled'],
});
const page = ctx.pages()[0] || await ctx.newPage();

const log = [];
const say = (s) => { console.log(s); log.push(s); };

for (const url of ['https://claude.ai/scheduled', 'https://claude.ai/schedule']) {
  try {
    await page.goto(url, { waitUntil: 'domcontentloaded', timeout: 30000 });
    await page.waitForTimeout(3500);
    const t = await page.evaluate(() => document.body.innerText.slice(0, 600));
    say(`\n=== ${url} -> ${page.url()}`);
    say(t);
    if (/Scheduled tasks|No scheduled tasks/i.test(t)) { say('>> MATCH'); break; }
  } catch (e) { say(`${url} ERROR ${e.message}`); }
}

await page.screenshot({ path: ROOT + '/rec/probe-list.png' });

// ปุ่มและองค์ประกอบที่คลิกได้
const els = await page.evaluate(() => {
  const out = [];
  document.querySelectorAll('button, a[href], [role="button"]').forEach((el) => {
    const r = el.getBoundingClientRect();
    const txt = (el.innerText || el.getAttribute('aria-label') || '').trim().slice(0, 45);
    if (r.width > 8 && r.height > 8 && txt) {
      out.push({ txt, x: Math.round(r.x), y: Math.round(r.y), w: Math.round(r.width), h: Math.round(r.height), tag: el.tagName });
    }
  });
  return out.slice(0, 60);
});
say('\n=== CLICKABLE ===');
els.forEach((e) => say(`${e.tag.padEnd(7)} ${String(e.x).padStart(5)},${String(e.y).padStart(4)} ${String(e.w).padStart(4)}x${String(e.h).padStart(3)}  ${e.txt}`));

// ลองกด New task
try {
  await page.locator('button:has-text("New task")').first().click({ timeout: 8000 });
  await page.waitForTimeout(3000);
  await page.screenshot({ path: ROOT + '/rec/probe-newtask.png' });
  const t2 = await page.evaluate(() => document.body.innerText.slice(0, 1500));
  say('\n=== AFTER New task ===');
  say(t2);
  const els2 = await page.evaluate(() => {
    const out = [];
    document.querySelectorAll('button,[role="menuitem"],[role="option"],input,textarea').forEach((el) => {
      const r = el.getBoundingClientRect();
      const txt = (el.innerText || el.placeholder || el.getAttribute('aria-label') || '').trim().slice(0, 45);
      if (r.width > 8 && r.height > 8 && txt) out.push(`${el.tagName.padEnd(9)} ${String(Math.round(r.x)).padStart(5)},${String(Math.round(r.y)).padStart(4)}  ${txt}`);
    });
    return out.slice(0, 40);
  });
  say('\n=== MENU ITEMS ===');
  els2.forEach(say);
} catch (e) { say('New task click failed: ' + e.message); }

await writeFile(ROOT + '/rec/probe.txt', log.join('\n'), 'utf8');
await ctx.close();
console.log('PROBE DONE');
