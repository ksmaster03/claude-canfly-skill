// Search the customer and product pickers on the open quotation-create tab and print the matching options. Saves nothing.
// usage: node search.js customer|product term1 term2 ...
const { chromium } = require(process.env.PLAYWRIGHT_MODULE || 'playwright');
const norm = s => (s || '').replace(/เเ/g, 'แ').replace(/[\u200b-\u200d\ufeff]/g, '').trim();
(async () => {
  const [kind, ...terms] = process.argv.slice(2);
  const b = await chromium.connectOverCDP('http://127.0.0.1:9222');
  const pg = b.contexts()[0].pages().find(p => p.url().includes('quotationCreate'));
  await pg.evaluate(() => document.querySelectorAll('#intercom-container,.intercom-lightweight-app').forEach(e => e.style.display = 'none'));
  const box = kind === 'customer'
    ? pg.locator('input[placeholder*="ค้นหาผู้ติดต่อ"]').first()
    : pg.locator('tr.tr-product').first().locator('.selectInputDropdown').first();
  for (const t of terms) {
    await box.click(); await pg.waitForTimeout(600);
    const input = kind === 'customer' ? box : pg.locator('tr.tr-product').first().locator('input[placeholder*="สินค้า"]').first();
    await input.fill(''); await input.type(t, { delay: 40 });
    let opts = [];
    for (let k = 0; k < 20; k++) {
      await pg.waitForTimeout(500);
      opts = await pg.evaluate(() => [...document.querySelectorAll('span.multiselect__option, .multiselect__option, li.multiselect__element')]
        .filter(e => e.getBoundingClientRect().width).map(e => e.innerText.replace(/\s+/g, ' ').trim()).filter(Boolean));
      if (opts.length && k > 3) break;
    }
    console.log('== ' + kind + ' "' + t + '": ' + opts.length);
    [...new Set(opts.map(norm))].slice(0, 25).forEach(o => console.log('   ' + o));
    await input.fill(''); await pg.keyboard.press('Escape'); await pg.waitForTimeout(300);
  }
  await pg.screenshot({ path: __dirname + '/search.png' });
  process.exit(0);
})().catch(e => { console.log('ERR', e.message); process.exit(1); });
