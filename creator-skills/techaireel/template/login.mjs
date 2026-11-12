// เปิดเบราว์เซอร์ให้ผู้ใช้ล็อกอิน claude.ai หนึ่งครั้ง แล้วเก็บ profile ไว้ใช้ซ้ำ
const { chromium } = await import('file:///$PROJECTS/chatgpt-bridge/node_modules/playwright/index.mjs');

const PROFILE = '__ROOT__/claude-data';
const TARGET = 'https://claude.ai/settings/schedule';

const ctx = await chromium.launchPersistentContext(PROFILE, {
  headless: false,
  viewport: { width: 1440, height: 900 },
  args: ['--disable-blink-features=AutomationControlled'],
});

const page = ctx.pages()[0] || await ctx.newPage();
await page.goto('https://claude.ai/', { waitUntil: 'domcontentloaded' }).catch(() => {});

console.log('รอผู้ใช้ล็อกอิน ... (สูงสุด 6 นาที)');

const deadline = Date.now() + 6 * 60 * 1000;
let ok = false;
while (Date.now() < deadline) {
  await page.waitForTimeout(3000);
  const url = page.url();
  // ล็อกอินแล้วจะไม่อยู่หน้า login และมี composer หรือ sidebar
  const signedIn = await page.evaluate(() => {
    const t = document.body ? document.body.innerText : '';
    return !/Sign in|Log in|เข้าสู่ระบบ/i.test(t.slice(0, 2000)) && t.length > 200;
  }).catch(() => false);
  if (signedIn && !/login|auth/i.test(url)) {
    console.log('ดูเหมือนล็อกอินแล้วที่', url);
    ok = true;
    break;
  }
}

if (ok) {
  await page.goto(TARGET, { waitUntil: 'domcontentloaded' }).catch(() => {});
  await page.waitForTimeout(4000);
  await page.screenshot({ path: '__ROOT__/rec/schedule-page.png', fullPage: false });
  const text = await page.evaluate(() => document.body.innerText.slice(0, 3000)).catch(() => '');
  console.log('--- PAGE TEXT ---');
  console.log(text);
}

await ctx.close();
console.log(ok ? 'DONE' : 'TIMEOUT');
