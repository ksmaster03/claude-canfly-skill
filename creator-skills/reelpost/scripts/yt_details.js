// Kosin 17/10/2026 กรอกหน้า Details ของ YouTube Studio (หลังอัปไฟล์เสร็จ) วางใน javascript_tool
// แทน TITLE กับ DESC ด้วยข้อความจาก <proj>/youtube.txt ก่อนรัน
//   ใน template literal ต้องเขียน \ เป็น \\ และห้ามมี ` ในข้อความ · YouTube ไม่รับ < > ในคำอธิบาย
//   ช่องตั้งค่าเริ่มต้นไว้ (ชื่อ "Kosin Finsure 「Official Music」" คำอธิบาย "สนับสนุนผลงาน + ลิงก์ join") สคริปต์นี้เขียนทับทั้งคู่
//   ให้ต่อบรรทัด "สนับสนุนผลงาน" กับลิงก์ join ไว้ท้าย DESC เอง
const TITLE = 'ชื่อคลิป #Shorts';
const DESC = `คำอธิบาย`;
const d = document.querySelector('ytcp-uploads-dialog');
const boxes = [...d.querySelectorAll('#textbox[contenteditable="true"]')];
async function setBox(b, text) {
  b.focus();
  document.execCommand('selectAll', false, null);
  document.execCommand('insertText', false, text);
  b.dispatchEvent(new Event('input', { bubbles: true }));
  await new Promise(r => setTimeout(r, 400));
  b.blur();
}
await setBox(boxes[0], TITLE);
await setBox(boxes[1], DESC);
// เปิด Show more แล้วตอบ: ไม่มีเนื้อหาสังเคราะห์ที่ทำให้เข้าใจผิด, ไม่มีโฆษณาแฝง (ค่าที่ผู้ใช้ใช้มาทุกคลิป)
const tog = d.querySelector('#toggle-button');
if (tog && /show more|แสดงเพิ่มเติม/i.test(tog.innerText)) tog.click();
await new Promise(r => setTimeout(r, 1200));
for (const n of ['VIDEO_HAS_ALTERED_CONTENT_NO', 'VIDEO_PAID_PRODUCT_PLACEMENT_NO']) {
  const r = d.querySelector(`tp-yt-paper-radio-button[name="${n}"]`); if (r) r.click();
}
await new Promise(r => setTimeout(r, 800));
const radios = [...d.querySelectorAll('tp-yt-paper-radio-button')].filter(r => r.hasAttribute('checked')).map(r => r.getAttribute('name'));
JSON.stringify({
  titleOk: boxes[0].innerText.trim() === TITLE,
  descLen: boxes[1].innerText.length,
  blankLines: (boxes[1].innerText.match(/\n\n/g) || []).length,
  checked: radios,   // ต้องมี VIDEO_MADE_FOR_KIDS_NOT_MFK, VIDEO_HAS_ALTERED_CONTENT_NO, VIDEO_PAID_PRODUCT_PLACEMENT_NO
});
