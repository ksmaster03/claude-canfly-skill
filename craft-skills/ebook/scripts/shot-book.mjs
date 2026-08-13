/**
 * shot-book.mjs <file-url> <out.png> [scrollY] — screenshot หนังสือที่ build แล้ว
 *
 * ใช้ตรวจด้วยตาว่าฟอนต์ไทย ตาราง โค้ด และภาพหัวบทเรนเดอร์ถูก ก่อนส่งมอบ
 * (อ่าน PDF ตรง ๆ ไม่ได้เพราะเครื่องนี้ไม่มี pdftoppm/poppler)
 *
 * ‼ ต้องคัดลอกไฟล์นี้ไปวางใน $CHATGPT_BRIDGE ก่อนรัน
 *   เพราะ node_modules ของ playwright อยู่ที่นั่น รันจากที่อื่นจะ ERR_MODULE_NOT_FOUND
 *
 *   cp <skill>/scripts/shot-book.mjs /d/Project/chatgpt-bridge/
 *   cd /d/Project/chatgpt-bridge
 *   node shot-book.mjs "file:///$WORK/x-ebook/dist/x.html" out.png 42000
 */
import { chromium } from 'playwright';

const [, , url, out, y] = process.argv;
if (!url || !out) {
  console.error('ใช้: node shot-book.mjs <file-url> <out.png> [scrollY]');
  process.exit(1);
}

const browser = await chromium.launch();
const page = await browser.newPage({
  viewport: { width: 900, height: 1200 },
  deviceScaleFactor: 1,
});
await page.goto(url, { waitUntil: 'load', timeout: 180_000 });
if (y) await page.evaluate((n) => window.scrollTo(0, Number(n)), y);
await page.waitForTimeout(1500);
await page.screenshot({ path: out });
await browser.close();
console.log('WROTE', out);
