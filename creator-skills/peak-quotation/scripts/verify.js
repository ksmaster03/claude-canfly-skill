// Open a saved quotation in a fresh tab, read the stored values back, screenshot, and close that tab. Read-only.
const { chromium } = require(process.env.PLAYWRIGHT_MODULE || 'playwright');
(async () => {
  const url = process.argv[2];
  const b = await chromium.connectOverCDP('http://127.0.0.1:9222');
  const pg = await b.contexts()[0].newPage();
  await pg.goto(url, { waitUntil: 'domcontentloaded' }); await pg.waitForTimeout(8000);
  const r = await pg.evaluate(() => {
    const n = s => (s || '').replace(/เเ/g, 'แ').replace(/\s+/g, ' ').trim();
    const body = n(document.body.innerText);
    const rows = [...document.querySelectorAll('tr.tr-product')].map((tr, i) => ({
      product: n((tr.querySelector('.textSelectedDropdown p') || {}).innerText),
      vals: [...tr.querySelectorAll('input')].filter(e => e.getBoundingClientRect().width && !e.getAttribute('placeholder') && e.type !== 'checkbox').map(e => e.value),
      desc: (document.querySelectorAll('textarea[placeholder*="คำอธิบายรายการ"]')[i] || {}).value }));
    return { docno: (document.querySelector('input[placeholder="ระบุเลขที่เอกสาร"]') || {}).value,
      status: (body.match(/(ร่าง|รออนุมัติ|รอตอบรับ)/) || [])[1],
      customer: (body.match(/ชื่อลูกค้า (.{0,60})/) || [])[1],
      dates: [...document.querySelectorAll('input')].filter(e => /^\d\d\/\d\d\/\d{4}$/.test(e.value)).map(e => e.value),
      rows, summary: (body.match(/มูลค่าที่คำนวณภาษี 7%.{0,160}/) || [])[0],
      total: (body.match(/จำนวนเงินทั้งสิ้น ([0-9,.]+)/) || [])[1],
      note: (document.getElementById('หมายเหตุสำหรับลูกค้า') || {}).value };
  });
  console.log(JSON.stringify(r, null, 1));
  await pg.screenshot({ path: __dirname + '/verify.png', fullPage: true });
  await pg.close({ runBeforeUnload: false });
  process.exit(0);
})().catch(e => { console.log('ERR', e.message); process.exit(1); });
