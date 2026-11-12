// Attach to the open PEAK window, report the URL and visible text, and save a screenshot. Never closes the browser.
const { chromium } = require(process.env.PLAYWRIGHT_MODULE || 'playwright');
(async () => {
  const b = await chromium.connectOverCDP('http://127.0.0.1:9222');
  const pg = b.contexts()[0].pages().find(p => p.url().includes('peakaccount')) || b.contexts()[0].pages()[0];
  if (process.argv[2]) { await pg.goto(process.argv[2], { waitUntil: 'domcontentloaded' }); }
  await pg.waitForTimeout(+process.argv[3] || 3000);
  console.log('URL', pg.url());
  const t = await pg.evaluate(() => document.body.innerText.replace(/\n{2,}/g, '\n').slice(0, 2500));
  console.log(t);
  await pg.screenshot({ path: __dirname + '/peek.png' });
  process.exit(0);
})().catch(e => { console.log('ERR', e.message); process.exit(1); });
