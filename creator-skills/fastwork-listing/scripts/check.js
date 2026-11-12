/**
 * Quick status check: is the persistent browser up, and is it logged in?
 *   NODE_PATH="$APPDATA/npm/node_modules/@playwright/mcp/node_modules" node check.js
 */
const fw = require('./fw-lib.js');
(async () => {
  const { browser, page } = await fw.connect();
  await page.goto('https://seller.fastwork.co/my-services', { waitUntil: 'domcontentloaded' });
  await page.waitForTimeout(1500);
  console.log('URL:', page.url());
  console.log('TITLE:', await page.title());
  const loggedIn = page.url().includes('seller.fastwork.co') && !page.url().includes('auth2.fastwork.co');
  console.log('LOGGED_IN:', loggedIn);
  if (loggedIn) {
    console.log(await page.evaluate(() => {
      const m = document.body.innerText.match(/งานของฉัน \((\d+)\/(\d+)\)/);
      return m ? `Jobs: ${m[1]}/${m[2]}` : 'Could not read job count';
    }));
  }
  await browser.close();
})().catch(e => { console.error('CHECK_ERROR', e.message); process.exit(1); });
