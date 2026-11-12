// Click "บันทึกร่าง" (save as draft) on the filled quotation-create tab, then reload the saved document and read it back.
// Never touches "อนุมัติใบเสนอราคา".
const { chromium } = require(process.env.PLAYWRIGHT_MODULE || 'playwright');
(async () => {
  const b = await chromium.connectOverCDP('http://127.0.0.1:9222');
  const pg = b.contexts()[0].pages().find(p => p.url().includes('quotationCreate'));
  await pg.evaluate(() => document.querySelectorAll('#intercom-container,.intercom-lightweight-app').forEach(e => e.style.display = 'none'));
  await pg.keyboard.press('Escape');
  const clicked = await pg.evaluate(() => {
    const els = [...document.querySelectorAll('button,div,span,a')].filter(e => e.innerText && e.innerText.trim() === 'บันทึกร่าง' && e.getBoundingClientRect().width);
    const el = els.filter(e => !els.some(o => o !== e && e.contains(o))).pop();
    if (!el) return null; el.click(); return el.tagName + '.' + el.className;
  });
  console.log('clicked', clicked);
  await pg.waitForURL(/quotationEdit|quotationDetail|eii=/, { timeout: 30000 }).catch(() => {});
  await pg.waitForTimeout(3000);
  console.log('after save URL', pg.url());
  // no reload here: the edit page has a beforeunload prompt and reload() crashes Playwright ("No dialog is showing").
  // check the saved values with verify.js, which opens the document in a fresh tab
  console.log('next: node verify.js "' + pg.url() + '"');
  process.exit(0);
})().catch(e => { console.log('ERR', e.message); process.exit(1); });
