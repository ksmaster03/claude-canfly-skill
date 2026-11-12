// verify.mjs: ตรวจ repo ทุกตัวใน data.json กับ GitHub จริง เติมดาว (เช่น 190K) และเขียนแคปชันร่าง caption.txt
// ใช้: node verify.mjs <data.json>   (ต้องมี gh ที่ล็อกอินแล้ว) item ที่ไม่ใช่ repo ให้ใส่ "url" เองและไม่ต้องมี "repo"
import { execFileSync } from 'node:child_process';
import fs from 'node:fs'; import path from 'node:path';
const p = process.argv[2], d = JSON.parse(fs.readFileSync(p, 'utf8'));
const k = (n) => n >= 1000 ? (n / 1000).toFixed(n >= 100000 ? 0 : 1).replace(/\.0$/, '') + 'K' : String(n);
const months = (iso) => (Date.now() - Date.parse(iso)) / 2.63e9;
let bad = 0, sum = 0;
for (const it of d.items) {
  if (!it.repo) { console.log('·', it.name, '(ไม่ใช่ repo ข้ามการตรวจ)'); continue; }
  try {
    const r = JSON.parse(execFileSync('gh', ['api', `repos/${it.repo}`], { encoding: 'utf8' }));
    it.stars = k(r.stargazers_count); it.url = r.html_url; sum += r.stargazers_count;
    const warn = [r.archived && 'ARCHIVED', months(r.pushed_at) > 3 && `ไม่อัปเดต ${months(r.pushed_at).toFixed(0)} เดือน`, !r.license && 'ไม่มี license (ห้ามเรียก open source)'].filter(Boolean);
    console.log(warn.length ? '⚠' : '✓', r.full_name, '★', r.stargazers_count, r.license?.spdx_id || '-', warn.join(', '));
    if (r.full_name.toLowerCase() !== it.repo.toLowerCase()) console.log('  ↪ ย้ายชื่อเป็น', r.full_name);
  } catch { bad++; console.log('‼ ไม่พบ', it.repo); }
}
d.total_stars = k(sum);
fs.writeFileSync(p, JSON.stringify(d, null, 2));
const cap = [d.hook || d.title, '', ...(d.lead ? [d.lead, ''] : []),
  ...d.items.flatMap((it, i) => [`${i + 1}. ${it.label || it.name}${it.stars ? ` · ★${it.stars}` : ''}`, it.why || it.line, it.url || '', '']),
  ...(d.howto ? ['วิธีใช้:', ...d.howto.map((s, i) => `${i + 1}. ${s}`), ''] : []),
  d.cta || 'กดบันทึกไว้ แล้วส่งให้เพื่อนที่ยังทำทุกอย่างเองอยู่', '', (d.hashtags || ['#ClaudeCode', '#AI', '#GitHub', '#โกสินทร์ต้องบินได้']).join(' ')];
fs.writeFileSync(path.join(path.dirname(p), 'caption.txt'), cap.join('\n'));
console.log(bad ? `‼ ${bad} repo ไม่พบ แก้ก่อนเรนเดอร์` : `ครบ รวมดาว ${d.total_stars}`, '→ caption.txt');
process.exit(bad ? 1 : 0);
