// Fill a new quotation in a fresh quotation-create tab (closes any unsaved create tab first). Does NOT save.
// Run it, check the printed read-back and the screenshot, then run save.js.
const { chromium } = require(process.env.PLAYWRIGHT_MODULE || 'playwright');
const norm = s => (s || '').replace(/เเ/g, 'แ').replace(/[\u200b-\u200d\ufeff]/g, '').replace(/\s+/g, ' ').trim();

// ---- edit these for each quotation (business id = the emi= value in your PEAK URL)
const EMI = '<EMI>';                                      // รหัส business (พารามิเตอร์ emi ใน URL ของ PEAK ของกิจการคุณ)
const CUSTOMER = { search: 'คำค้นชื่อลูกค้า', code: 'C000XX' }; // code = รหัสผู้ติดต่อที่เห็นในตัวเลือก
const VALID_UNTIL = '';                                   // 'dd/mm/yyyy' วันที่ใช้ได้ถึง (ค่าตั้งต้นของ PEAK คือ 7 วัน) ว่าง = ไม่แตะ
const ROWS = [                                            // price '0' = รายการแถมฟรี
  { code: 'P000XX', qty: '1', price: '100000', desc:
`Line 1 title
- detail` },
  { code: 'P000YY', qty: '10', price: '0', desc:
`Free item, included in the package at no charge` },
];
const NOTE =                                              // หมายเหตุสำหรับลูกค้า ไม่เกิน 1,000 ตัวอักษร
`Terms and conditions
1. Prices are in Thai Baht and exclude VAT 7%.
2. Payment within 30 days of the invoice date.
3. This quotation is valid for 30 days from the issue date.`;

async function pickOption(pg, want) {
  for (let k = 0; k < 24; k++) {
    await pg.waitForTimeout(500);
    const hit = await pg.evaluate(w => {
      const n = s => (s || '').replace(/เเ/g, 'แ').replace(/\s+/g, ' ').trim();
      const el = [...document.querySelectorAll('.multiselect__option')].find(e => e.getBoundingClientRect().width && new RegExp('(^|\\s)' + w + '(\\s|$)').test(n(e.innerText)));
      if (el) { el.click(); return n(el.innerText); }
      return null;
    }, want);
    if (hit) return hit;
  }
  throw new Error('option not found: ' + want);
}
async function setText(pg, handle, value) {
  await handle.evaluate((el, v) => {
    const proto = el.tagName === 'TEXTAREA' ? HTMLTextAreaElement.prototype : HTMLInputElement.prototype;
    Object.getOwnPropertyDescriptor(proto, 'value').set.call(el, v);
    ['input', 'change', 'blur'].forEach(t => el.dispatchEvent(new Event(t, { bubbles: true })));
  }, value);
}

(async () => {
  if (NOTE.length > 1000) throw new Error('customer note is ' + NOTE.length + ' chars, PEAK allows 1,000');
  const b = await chromium.connectOverCDP('http://127.0.0.1:9222');
  // start from a clean form: close any unsaved create tab without its leave-page prompt, then open a fresh one
  for (const old of b.contexts()[0].pages().filter(p => p.url().includes('quotationCreate'))) await old.close({ runBeforeUnload: false });
  const pg = await b.contexts()[0].newPage();
  pg.on('dialog', d => d.dismiss().catch(() => {}));
  await pg.goto('https://secure.peakaccount.com/income/quotationCreate?emi=' + EMI, { waitUntil: 'domcontentloaded' }); await pg.waitForTimeout(7000);
  const hideChat = () => pg.evaluate(() => document.querySelectorAll('#intercom-container,.intercom-lightweight-app').forEach(e => e.style.display = 'none'));
  await hideChat();

  // customer
  // the search input can be hidden until its box is clicked, so click the visible box by position, then type
  const cbox = await pg.evaluate(() => { const i = document.querySelector('input[placeholder*="ค้นหาผู้ติดต่อ"]'); let c = i; while (c && c.getBoundingClientRect().width < 50) c = c.parentElement; c.scrollIntoView({ block: 'center' }); const r = c.getBoundingClientRect(); return { x: r.x + 40, y: r.y + r.height / 2 }; });
  await pg.mouse.click(cbox.x, cbox.y); await pg.waitForTimeout(800);
  await pg.keyboard.type(CUSTOMER.search, { delay: 50 });
  console.log('customer picked:', await pickOption(pg, CUSTOMER.code));
  await pg.waitForTimeout(1500);

  // rows
  while (await pg.locator('tr.tr-product').count() < ROWS.length) {
    await pg.evaluate(() => [...document.querySelectorAll('button')].find(e => e.innerText.trim() === 'เพิ่มรายการใหม่' && e.getBoundingClientRect().width).click());
    await pg.waitForTimeout(800);
  }
  for (let i = 0; i < ROWS.length; i++) {
    const r = ROWS[i], tr = pg.locator('tr.tr-product').nth(i);
    await hideChat();
    await tr.locator('.selectInputDropdown').first().click(); await pg.waitForTimeout(500);
    await tr.locator('input[placeholder*="สินค้า"]').first().type(r.code, { delay: 40 });
    console.log('row', i + 1, 'product picked:', await pickOption(pg, r.code));
    await pg.waitForTimeout(1200);
    const nums = await tr.locator('input').evaluateAll(els => els.map((e, j) => ({ j, vis: !!e.getBoundingClientRect().width, ph: e.getAttribute('placeholder'), type: e.type })).filter(x => x.vis && !x.ph && x.type !== 'checkbox').map(x => x.j));
    const [qi, pi] = nums;
    for (const [idx, val] of [[qi, r.qty], [pi, r.price]]) {
      const inp = tr.locator('input').nth(idx);
      await inp.click({ clickCount: 3 }); await inp.press('Control+A'); await inp.type(val, { delay: 30 }); await inp.press('Tab'); await pg.waitForTimeout(400);
    }
    await setText(pg, pg.locator('textarea[placeholder*="คำอธิบายรายการ"]').nth(i), r.desc);
    await pg.waitForTimeout(400);
  }
  await setText(pg, pg.locator('textarea[id="หมายเหตุสำหรับลูกค้า"]'), NOTE);
  await pg.waitForTimeout(1500);
  if (VALID_UNTIL) {
    // type over the second date field, then click the empty page margin to close the calendar (never click inside the form)
    const di = await pg.evaluate(() => [...document.querySelectorAll('input')].map((e, i) => ({ i, v: e.value, w: e.getBoundingClientRect().width })).filter(x => x.w && /^\d\d\/\d\d\/\d{4}$/.test(x.v)).map(x => x.i));
    const vu = pg.locator('input').nth(di[1]);
    await vu.scrollIntoViewIfNeeded(); await vu.click({ clickCount: 3 }); await vu.press('Control+A'); await vu.type(VALID_UNTIL, { delay: 60 }); await pg.waitForTimeout(500);
    await pg.mouse.click(60, 600); await pg.waitForTimeout(1200);
  }

  // read back
  const back = await pg.evaluate(() => {
    const n = s => (s || '').replace(/เเ/g, 'แ').replace(/\s+/g, ' ').trim();
    const rows = [...document.querySelectorAll('tr.tr-product')].map((tr, i) => {
      const sel = tr.querySelector('.textSelectedDropdown p');
      const vals = [...tr.querySelectorAll('input')].filter(e => e.getBoundingClientRect().width && !e.getAttribute('placeholder') && e.type !== 'checkbox').map(e => e.value);
      const ta = document.querySelectorAll('textarea[placeholder*="คำอธิบายรายการ"]')[i];
      return { product: sel ? n(sel.innerText) : n(tr.innerText).slice(0, 80), vals, desc: ta ? ta.value : null, text: n(tr.innerText).slice(0, 160) };
    });
    const body = n(document.body.innerText);
    const grab = k => { const m = body.match(new RegExp(k + ' ([0-9,.]+)')); return m ? m[1] : null; };
    return { rows, cust: n((document.querySelector('input[placeholder*="ค้นหาผู้ติดต่อ"]') || {}).value) || n(body.match(/ชื่อลูกค้า (.{0,80})/) ? body.match(/ชื่อลูกค้า (.{0,80})/)[1] : ''),
      dates: [...document.querySelectorAll('input')].filter(e => /^\d\d\/\d\d\/\d{4}$/.test(e.value)).map(e => e.value),
      docno: (document.querySelector('input[placeholder="ระบุเลขที่เอกสาร"]') || {}).value,
      net: grab('มูลค่าที่คำนวณภาษี 7%'), vat: grab('ภาษีมูลค่าเพิ่ม 7%'), total: grab('จำนวนเงินทั้งสิ้น'),
      note: (document.getElementById('หมายเหตุสำหรับลูกค้า') || {}).value };
  });
  console.log(JSON.stringify(back, null, 1));
  await pg.screenshot({ path: __dirname + '/filled.png', fullPage: true });
  process.exit(0);
})().catch(e => { console.log('ERR', e.message); process.exit(1); });
