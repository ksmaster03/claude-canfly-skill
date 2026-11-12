// วางใน javascript_tool ของ claude-in-chrome บนแท็บ luminatts.vercel.app (ต้องล็อกอินแล้ว และรัน lumina_bridge.py ไว้ก่อน)
// ดึงบทจากเครื่อง → วางลงช่องข้อความ → กด GENERATE → รอไฟล์เสียง → ส่งกลับเครื่อง
const PORT = 8799;
const T = (await (await fetch(`http://127.0.0.1:${PORT}/`)).json()).t;
if (!window.__hooked) {
  window.__hooked = 1; window.__blobs = [];
  const oc = URL.createObjectURL.bind(URL);
  URL.createObjectURL = (b) => { const u = oc(b); try { window.__blobs.push({ u, size: b.size, type: b.type, blob: b }); } catch (e) {} return u; };
}
const n0 = window.__blobs.filter(x => x.type === 'audio/mpeg').length;
const ta = document.querySelector('textarea');
Object.getOwnPropertyDescriptor(HTMLTextAreaElement.prototype, 'value').set.call(ta, T);
ta.dispatchEvent(new Event('input', { bubbles: true }));
await new Promise(r => setTimeout(r, 700));
[...document.querySelectorAll('button')].find(b => /G\s*E\s*N/.test(b.innerText)).click();
let b = null;
for (let i = 0; i < 90; i++) {
  await new Promise(r => setTimeout(r, 1000));
  const a = window.__blobs.filter(x => x.type === 'audio/mpeg');
  if (a.length > n0) { b = a.pop(); break; }
}
let out = 'no audio';
if (b) out = await (await fetch(`http://127.0.0.1:${PORT}/`, { method: 'POST', body: b.blob })).text();
JSON.stringify({ same: ta.value === T, len: T.length, out });
