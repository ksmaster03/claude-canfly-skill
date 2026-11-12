/**
 * Reusable Playwright helpers for driving seller.fastwork.co via CDP.
 * Run with: NODE_PATH="$APPDATA/npm/node_modules/@playwright/mcp/node_modules" node <script-using-this>.js
 * (playwright isn't installed standalone on this box — it's borrowed from the global @playwright/mcp install.)
 *
 * Usage pattern in a one-off script:
 *   const { chromium } = require('playwright');
 *   const fw = require('<path-to-this-file>/fw-lib.js');
 *   const { browser, page } = await fw.connect();
 *   ... do stuff ...
 *   await browser.close();
 */
const { chromium } = require('playwright');

const DEFAULT_PORT = 9224;
const DEFAULT_PROFILE = '$WORK/tmp\\pw-fastwork-profile';
const CHROMIUM_EXE = '~\\AppData\\Local\\ms-playwright\\chromium-1234\\chrome-win64\\chrome.exe';
// ^ pin this — the bundled playwright asks for a chromium revision that isn't installed.
// If this path 404s, run `ls "$LOCALAPPDATA/ms-playwright"` and update to whatever chromium-XXXX exists.

/** Connect to the already-running persistent Fastwork browser (launch it first with launchPersistent). */
async function connect(port = DEFAULT_PORT) {
  const browser = await chromium.connectOverCDP(`http://127.0.0.1:${port}`);
  const ctx = browser.contexts()[0];
  const page = ctx.pages()[0] || await ctx.newPage();
  page.on('dialog', async d => { await d.accept().catch(() => {}); });
  return { browser, page };
}

/**
 * Launch a long-lived, headed, persistent-profile Chrome for the user to log into once.
 * Run this in a BACKGROUND bash task (it never exits — holds the browser open).
 * First launch after a while sometimes exits immediately with exitCode=21 for no logged reason —
 * just retry once, no fix needed (seen and confirmed transient on 2026-08-30).
 */
async function launchPersistent({ profileDir = DEFAULT_PROFILE, port = DEFAULT_PORT, url = 'https://seller.fastwork.co/my-services' } = {}) {
  const context = await chromium.launchPersistentContext(profileDir, {
    headless: false,
    executablePath: CHROMIUM_EXE,
    args: [`--remote-debugging-port=${port}`],
    viewport: { width: 1400, height: 900 },
  });
  const page = context.pages()[0] || await context.newPage();
  await page.goto(url, { waitUntil: 'domcontentloaded' });
  console.log('Browser launched, debug port', port);
  await new Promise(() => {}); // hold forever
}

/** Fill the first VISIBLE match of a selector. Fastwork keeps every package/tab's fields in the DOM at
 *  once (hidden ones just get display:none), so plain selectors silently hit the wrong hidden package. */
async function fillVisible(page, selector, value) {
  await page.locator(`${selector}:visible`).first().fill(value);
}

/** Native DOM click via evaluate — required for Fastwork's custom radio/checkbox inputs. A real
 *  Playwright .click({force:true}) on the <input> does NOT trigger their React state (tested, fails
 *  silently); only element.click() from inside the page does. */
async function nativeClick(page, selector) {
  await page.evaluate((sel) => {
    const el = document.querySelector(sel);
    if (el) el.click();
  }, selector);
}

/** Set a checkbox (by selector) to a boolean state, first VISIBLE match only, via native click. */
async function setCheckboxVisible(page, selector, want) {
  await page.evaluate(({ selector, want }) => {
    const els = Array.from(document.querySelectorAll(selector));
    const el = els.find(e => e.offsetParent !== null);
    if (el && el.checked !== want) el.click();
  }, { selector, want });
}

/** Click "บันทึกแบบร่าง" (save draft) and wait for the toast. ALWAYS call this immediately after
 *  filling a field and BEFORE any page.goto() — an unsaved-changes confirm dialog fires on navigation
 *  and gets auto-accepted by the page.on('dialog') handler in connect(), silently discarding the edit. */
async function saveDraft(page) {
  await page.evaluate(() => window.scrollTo(0, document.body.scrollHeight));
  await page.waitForTimeout(300);
  await page.getByText('บันทึกแบบร่าง', { exact: false }).first().click({ timeout: 8000, force: true });
  await page.waitForTimeout(1800);
}

/** Click "ส่งตรวจสอบ" (submit for review), then confirm the "ยืนยันการบันทึกข้อมูล?" modal that follows. */
async function submitForReview(page) {
  await page.getByText('ส่งตรวจสอบ', { exact: true }).first().click({ timeout: 8000, force: true });
  await page.waitForTimeout(1200);
  await page.getByText('ยืนยัน', { exact: true }).first().click({ timeout: 8000, force: true });
  await page.waitForTimeout(2000);
}

/**
 * Click an "add row/package" button repeatedly until the target row count is reached, verifying the
 * count after each click (a single blind loop over-adds or under-adds — the UI needs settle time and
 * sometimes swallows a click). `containerSelector` selects the element whose immediate <button> child
 * is the real add control — Fastwork's visible "+ text" is a <span> with NO onClick of its own.
 */
async function addRowsUntil(page, { containerSelector, rowsSelector, target }) {
  for (let attempt = 0; attempt < 20; attempt++) {
    const count = await page.evaluate((sel) => {
      const t = document.querySelector(sel);
      return t ? t.querySelectorAll('tbody tr').length : 0;
    }, rowsSelector);
    if (count >= target) return count;
    await page.evaluate((sel) => {
      const btn = document.querySelector(sel + ' button');
      if (btn) btn.click();
    }, containerSelector);
    await page.waitForTimeout(700);
  }
  throw new Error('addRowsUntil: target not reached after 20 attempts');
}

/**
 * Fill one row of the "สิ่งที่ลูกค้าจะได้รับ" deliverables checkbox matrix (table-mode packages only).
 * rowIndex is 0-based, checks is an array of booleans matching the package column order left-to-right.
 */
async function setDeliverableRow(page, { tableSelector = '.Style_deliverable-table__LiDzZ', rowIndex, title, checks }) {
  await page.evaluate(({ tableSelector, rowIndex, title, checks }) => {
    const table = document.querySelector(tableSelector);
    const row = table.querySelectorAll('tbody tr')[rowIndex];
    const input = row.querySelector('input.Style_deliverable-input__iNwOe');
    input.value = title;
    input.dispatchEvent(new Event('input', { bubbles: true }));
    input.dispatchEvent(new Event('change', { bubbles: true }));
    const boxes = Array.from(row.querySelectorAll('input[type="checkbox"]'));
    boxes.forEach((cb, idx) => { if (cb.checked !== checks[idx]) cb.click(); });
  }, { tableSelector, rowIndex, title, checks });
}

/** Read back the full deliverables matrix for verification. */
async function readDeliverables(page, tableSelector = '.Style_deliverable-table__LiDzZ') {
  return page.evaluate((sel) => {
    const t = document.querySelector(sel);
    if (!t) return [];
    return Array.from(t.querySelectorAll('tbody tr')).map(row => {
      const input = row.querySelector('input.Style_deliverable-input__iNwOe');
      const boxes = Array.from(row.querySelectorAll('input[type="checkbox"]')).map(cb => cb.checked);
      return { title: input.value, boxes };
    });
  }, tableSelector);
}

module.exports = {
  DEFAULT_PORT, DEFAULT_PROFILE, CHROMIUM_EXE,
  connect, launchPersistent, fillVisible, nativeClick, setCheckboxVisible,
  saveDraft, submitForReview, addRowsUntil, setDeliverableRow, readDeliverables,
};
