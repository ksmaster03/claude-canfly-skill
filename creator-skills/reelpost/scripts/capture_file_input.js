// Kosin 17/10/2026 ดักช่องเลือกไฟล์ที่หน้าเว็บสร้างตอนกดปุ่ม (Facebook Reels: "เพิ่มวิดีโอ", "อัพโหลดภาพ")
// ห้ามคลิกปุ่มพวกนี้ตรง ๆ เพราะจะเปิดหน้าต่างเลือกไฟล์ของระบบที่เครื่องมือมองไม่เห็น
// สคริปต์นี้ครอบ HTMLInputElement.click/showPicker ให้แค่แนบ input เข้า DOM แล้วคืนค่า จากนั้นกดปุ่มตามข้อความ BUTTON_TEXT
// รันแล้วใช้ find หา "file input" แล้ว file_upload ไปที่ ref นั้น · รันซ้ำได้ (ติดตั้งตัวดักครั้งเดียว)
const BUTTON_TEXT = /^เพิ่มวิดีโอ$/;   // ภาพปก: /^(อัพโหลดภาพ|อัปโหลดภาพ)$/
if (!window.__fiHook) {
  window.__fiHook = 1; window.__fileInputs = [];
  const grab = (el) => { if (!el.isConnected) { el.style.display = 'none'; document.body.appendChild(el); } el.setAttribute('data-captured', '1'); window.__fileInputs.push(el); };
  const oc = HTMLInputElement.prototype.click;
  HTMLInputElement.prototype.click = function () { if (this.type === 'file') return grab(this); return oc.apply(this, arguments); };
  if (HTMLInputElement.prototype.showPicker) {
    const sp = HTMLInputElement.prototype.showPicker;
    HTMLInputElement.prototype.showPicker = function () { if (this.type === 'file') return grab(this); return sp.apply(this, arguments); };
  }
}
const n0 = window.__fileInputs.length;
const btn = [...document.querySelectorAll('div[role=button], button, a')].find(b => BUTTON_TEXT.test(b.innerText.trim()));
if (btn) btn.click();
await new Promise(r => setTimeout(r, 1200));
const fresh = window.__fileInputs.slice(n0);
JSON.stringify({ clicked: !!btn, newInputs: fresh.length, accept: fresh.map(i => i.accept.slice(0, 40)) });
