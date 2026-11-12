// Keep a headed Chromium with the saved PEAK login open; other scripts attach over CDP on 127.0.0.1:9222.
const { chromium } = require(process.env.PLAYWRIGHT_MODULE || 'playwright');
(async () => {
  const ctx = await chromium.launchPersistentContext(process.env.PEAK_PROFILE || './playwright-peak-profile', {
    headless: false, viewport: null,
    // if Playwright cannot find its own Chromium build, set CHROMIUM_PATH to a Chromium/Chrome you already have (undefined = Playwright default)
    executablePath: process.env.CHROMIUM_PATH || undefined, args: ['--remote-debugging-port=9222', '--start-maximized'],
  });
  const pg = ctx.pages()[0] || await ctx.newPage();
  await pg.goto('https://secure.peakaccount.com/', { waitUntil: 'domcontentloaded' }).catch(e => console.log('goto', e.message));
  console.log('ready', pg.url());
  ctx.on('close', () => { console.log('closed'); process.exit(0); });
  await new Promise(() => {});
})();
