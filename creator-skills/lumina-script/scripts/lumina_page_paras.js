// Kosin 17/10/2026 สร้างเสียงรายย่อหน้า ใช้คู่กับ lumina_paras.py (วางใน javascript_tool บนแท็บ luminatts.vercel.app)
// แก้ PORT ให้ตรงกับที่เปิด lumina_paras.py และ NAMES เป็นย่อหน้าที่จะสร้าง (ทีละ 2 ถึง 4 ย่อหน้าต่อครั้ง ไม่งั้นเครื่องมือหมดเวลา)
// สร้างซ้ำย่อหน้าเดิมโดยไม่ทับไฟล์: ตั้งชื่อ 'p05_r2' จะอ่านบท p05.txt แต่เก็บเสียงเป็น p05_r2.mp3
const PORT = 8823;
const NAMES = ['p02', 'p03'];
if (!window.__hooked) {
  window.__hooked = 1; window.__blobs = [];
  const oc = URL.createObjectURL.bind(URL);
  URL.createObjectURL = (b) => { const u = oc(b); try { window.__blobs.push({ u, size: b.size, type: b.type, blob: b }); } catch (e) {} return u; };
}
window.__gen = async (name) => {
  const T = (await (await fetch(`http://127.0.0.1:${PORT}/${name.split('_')[0]}`)).json()).t;
  const n0 = window.__blobs.filter(x => x.type === 'audio/mpeg').length;
  const ta = document.querySelector('textarea');
  Object.getOwnPropertyDescriptor(HTMLTextAreaElement.prototype, 'value').set.call(ta, T);
  ta.dispatchEvent(new Event('input', { bubbles: true }));
  await new Promise(r => setTimeout(r, 700));
  [...document.querySelectorAll('button')].find(b => /G\s*E\s*N/.test(b.innerText)).click();
  let b = null;
  for (let i = 0; i < 80; i++) {
    await new Promise(r => setTimeout(r, 1000));
    const a = window.__blobs.filter(x => x.type === 'audio/mpeg');
    if (a.length > n0) { b = a.pop(); break; }
  }
  if (!b) return name + ': no audio';
  const out = await (await fetch(`http://127.0.0.1:${PORT}/${name}`, { method: 'POST', body: b.blob })).text();
  return name + ': ' + out + ' len ' + T.length + ' same ' + (ta.value === T);
};
const res = [];
for (const n of NAMES) res.push(await window.__gen(n));
res.join(' | ');
