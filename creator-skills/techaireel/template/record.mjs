// อัดหน้าจอ claude.ai Scheduled tasks พร้อมสเลทและ event log
import { writeFile, mkdir } from 'node:fs/promises';
const { chromium } = await import('file:///$PROJECTS/chatgpt-bridge/node_modules/playwright/index.mjs');

const ROOT = '__ROOT__';
const VIEW = { width: 1440, height: 900 };
const TASK_NAME = 'สรุปข่าว AI ประจำวัน';
const TASK_INSTR = 'ค้นข่าว AI ที่สำคัญของเมื่อวาน แล้วสรุปเป็นข้อ ๆ ไม่เกิน 5 ข้อ พร้อมลิงก์ต้นทาง';

await mkdir(ROOT + '/rec/video', { recursive: true });

const ctx = await chromium.launchPersistentContext(ROOT + '/claude-data', {
  headless: false, viewport: VIEW,
  recordVideo: { dir: ROOT + '/rec/video', size: VIEW },
  args: ['--disable-blink-features=AutomationControlled'],
});
const page = ctx.pages()[0] || await ctx.newPage();

const events = [];
const t0 = Date.now();
const stamp = () => (Date.now() - t0) / 1000;
const note = (o) => { events.push({ t: +stamp().toFixed(3), ...o }); console.log(`[${stamp().toFixed(2)}] ${o.type} ${o.label || ''}`); };

async function slate() {
  await page.evaluate(() => {
    const d = document.createElement('div');
    d.id = '__slate__';
    Object.assign(d.style, { position: 'fixed', inset: '0', background: '#FF0000', zIndex: '2147483647' });
    document.body.appendChild(d);
  });
  note({ type: 'slate' });
  await page.waitForTimeout(200);
  await page.evaluate(() => document.getElementById('__slate__')?.remove());
  await page.waitForTimeout(500);
}

async function boxOf(sel) {
  const loc = page.locator(sel).first();
  await loc.waitFor({ state: 'visible', timeout: 15000 });
  return { loc, box: await loc.boundingBox() };
}

async function clickAt(label, sel, wait = 1500) {
  try {
    const { loc, box } = await boxOf(sel);
    const before = stamp();
    await loc.click();
    const after = stamp();
    events.push({ t: +before.toFixed(3), tAfter: +after.toFixed(3), type: 'click', label, x: box.x, y: box.y, w: box.width, h: box.height, cx: box.x + box.width / 2, cy: box.y + box.height / 2 });
    console.log(`[${after.toFixed(2)}] click ${label}`);
    await page.waitForTimeout(wait);
    return true;
  } catch (e) { console.log(`!! click ${label}: ${e.message.split('\n')[0]}`); note({ type: 'miss', label }); return false; }
}

async function focusOn(label, sel, hold = 2200) {
  try {
    const { box } = await boxOf(sel);
    events.push({ t: +stamp().toFixed(3), tAfter: +stamp().toFixed(3), type: 'focus', label, x: box.x, y: box.y, w: box.width, h: box.height, cx: box.x + box.width / 2, cy: box.y + box.height / 2, hold: hold / 1000 });
    console.log(`[${stamp().toFixed(2)}] focus ${label}`);
    await page.waitForTimeout(hold);
    return true;
  } catch (e) { console.log(`!! focus ${label}: ${e.message.split('\n')[0]}`); note({ type: 'miss', label }); return false; }
}

async function typeInto(label, sel, text, delay = 55) {
  try {
    const { loc, box } = await boxOf(sel);
    await loc.click();
    const before = stamp();
    await loc.type(text, { delay });
    events.push({ t: +before.toFixed(3), tAfter: +stamp().toFixed(3), type: 'type', label, x: box.x, y: box.y, w: box.width, h: box.height, cx: box.x + box.width / 2, cy: box.y + box.height / 2 });
    console.log(`[${stamp().toFixed(2)}] type ${label}`);
    await page.waitForTimeout(900);
    return true;
  } catch (e) { console.log(`!! type ${label}: ${e.message.split('\n')[0]}`); note({ type: 'miss', label }); return false; }
}

try {
  // เริ่มจากหน้าแชทปกติ เพื่อให้เห็นว่าเข้าเมนูจากไหน
  await page.goto('https://claude.ai/new', { waitUntil: 'domcontentloaded' });
  await page.waitForTimeout(4000);
  await slate();

  note({ type: 'scene', label: 'หน้าแรก' });
  await page.waitForTimeout(1800);

  // L4-L5 ชี้เมนูซ้าย แล้วกด Scheduled
  await focusOn('เมนู Scheduled', 'a:has-text("Scheduled"), button:has-text("Scheduled")', 2400);
  await clickAt('กด Scheduled', 'a:has-text("Scheduled"), button:has-text("Scheduled")', 3000);

  // L6 หน้าว่าง
  await focusOn('ยังไม่มีงาน', 'text=No scheduled tasks yet', 2600);

  // L7-L13 เทมเพลตสำเร็จรูป
  await focusOn('เทมเพลตทั้งหมด', 'text=Daily briefing', 1500);
  await focusOn('Daily briefing', 'text=Daily briefing', 3600);
  await focusOn('Inbox triage', 'text=Inbox triage', 3400);
  await focusOn('Meeting prep', 'text=Meeting prep', 2600);
  await focusOn('Weekly review', 'text=Weekly review', 2600);

  // L15 กด New task
  await clickAt('ปุ่ม New task', 'button:has-text("New task")', 1800);

  // L17-L18 เมนูสองทาง
  await focusOn('Create with Claude', 'text=Create with Claude', 3000);
  await focusOn('Set up manually', 'text=Set up manually', 2600);
  await clickAt('เลือก Set up manually', 'text=Set up manually', 2500);

  // L19 ชื่องาน
  await typeInto('ช่องชื่องาน', 'input[placeholder*="Daily briefing"], dialog input[type="text"]', TASK_NAME, 60);

  // L20-L21 คำสั่ง
  await typeInto('ช่องคำสั่ง', 'textarea', TASK_INSTR, 35);

  // L22 โปรเจกต์กับโมเดล
  await focusOn('เลือกโปรเจกต์และโมเดล', 'text=Work in a project', 3200);

  // L23-L25 ความถี่
  await focusOn('ช่อง Frequency', 'text=Frequency', 1800);
  await clickAt('เปิดเมนูความถี่', 'button:has-text("Manual")', 1600);
  await page.screenshot({ path: ROOT + '/rec/freq-menu.png' });
  const freqText = await page.evaluate(() => document.body.innerText.slice(0, 1200));
  await writeFile(ROOT + '/rec/freq-menu.txt', freqText, 'utf8');
  await clickAt('เลือก Daily', '[role="option"]:has-text("Daily"), [role="menuitem"]:has-text("Daily"), text=Daily', 2200);

  // L26 สิทธิ์
  await focusOn('ช่อง Permissions', 'text=Permissions', 2800);

  // L27 ชี้ปุ่มบันทึก แต่ไม่กด เพื่อไม่ให้ไปสร้างข้อมูลจริงในบัญชี
  await page.screenshot({ path: ROOT + '/rec/before-save.png' });
  await focusOn('ปุ่ม Save', 'button:has-text("Save")', 3200);

  await page.waitForTimeout(1500);
  await clickAt('ปิดหน้าต่าง', 'button:has-text("Cancel")', 2000);
  await page.waitForTimeout(2000);
} catch (e) {
  console.log('ERROR:', e.message);
  note({ type: 'error', message: e.message });
}

const video = page.video();
await ctx.close();
const videoPath = await video.path();
await writeFile(ROOT + '/rec/events.json', JSON.stringify({ viewport: VIEW, videoPath, taskName: TASK_NAME, events }, null, 2), 'utf8');
console.log('VIDEO:', videoPath);
console.log('EVENTS:', events.length);
