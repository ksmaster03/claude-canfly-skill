// usage: node list.js <customer text>   (set env PEAK_EMI to your business emi from the PEAK URL)
// Read the quotation list in a throwaway tab and print rows that mention the given text. Read-only.
const { chromium } = require(process.env.PLAYWRIGHT_MODULE || 'playwright');
const norm = s => (s || '').replace(/เเ/g, 'แ').replace(/[\u200b-\u200d\ufeff]/g, '');
(async () => {
  const want = process.argv[2] || '';
  const b = await chromium.connectOverCDP('http://127.0.0.1:9222');
  const pg = await b.contexts()[0].newPage();
  await pg.goto('https://secure.peakaccount.com/income/quotation?emi=' + (process.env.PEAK_EMI || '<EMI>'), { waitUntil: 'domcontentloaded' });
  await pg.waitForTimeout(8000);
  console.log('URL', pg.url());
  const t = norm(await pg.evaluate(() => document.body.innerText));
  const lines = t.split('\n').map(x => x.trim()).filter(Boolean);
  lines.forEach((l, i) => { if (l.includes(want)) console.log(lines.slice(Math.max(0, i - 3), i + 4).join(' | ')); });
  console.log('total lines', lines.length, '| first rows:', lines.slice(0, 80).join(' / ').slice(0, 1800));
  await pg.close();
  process.exit(0);
})().catch(e => { console.log('ERR', e.message); process.exit(1); });
