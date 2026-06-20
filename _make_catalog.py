# -*- coding: utf-8 -*-
# สร้าง skill-catalog.md — ดัชนีสกิลทั้งหมด (slug + คำอธิบายย่อ + กลุ่ม) จาก standard/
# ใช้โดยสกิล /skill-router เพื่อแมตช์ประโยคผู้ใช้กับสกิลที่เกี่ยวข้อง
import os, re

ROOT = os.path.dirname(os.path.abspath(__file__))
STD = os.path.join(ROOT, "standard")
OUT = os.path.join(ROOT, "skill-catalog.md")

def frontmatter(text):
    m = re.search(r"^---\s*\n(.*?)\n---", text, re.DOTALL)
    return m.group(1) if m else ""

def field(fm, key):
    m = re.search(rf"^{key}:\s*(.+?)\s*$", fm, re.MULTILINE)
    return m.group(1).strip() if m else None

def short_desc(desc):
    # ตัดส่วน "Trigger..." ออก เหลือแก่นงาน
    d = re.split(r"\.?\s*[Tt]rigger", desc)[0].strip()
    d = re.split(r"\s*[—–-]\s*โทน", d)[0].strip()  # ตัดหางยาวบางแบบ
    return d[:160]

C_CATS = {"output-modes", "career-job"}

def group_of(fm):
    fw = field(fm, "framework")
    role = field(fm, "role")
    cat = field(fm, "category")
    job = field(fm, "อาชีพ")
    if fw:   return ("E", f"ชุด E · People Skills · {fw}")
    if role: return ("D", f"ชุด D · JobsDB AI · {role}")
    if cat:
        if cat == "sdlc": return ("F", "ชุด F · SDLC & Agile (Dev)")
        if cat in C_CATS: return ("C", f"ชุด C · คำสั่งลัด · {cat}")
        return ("B", f"ชุด B · Pro Bundle · {cat}")
    if job:  return ("A", "ชุด A · อาชีพ_skill (ไทย)")
    return ("Z", "เครื่องมือ (Meta)")

groups = {}
total = 0
for name in sorted(os.listdir(STD)):
    f = os.path.join(STD, name, "SKILL.md")
    if not os.path.isfile(f):
        continue
    with open(f, encoding="utf-8") as fh:
        text = fh.read()
    fm = frontmatter(text)
    slug = field(fm, "name") or name
    desc = field(fm, "description") or ""
    key, label = group_of(fm)
    groups.setdefault((key, label), []).append((slug, short_desc(desc)))
    total += 1

order = ["Z", "A", "B", "C", "D", "E", "F"]
lines = [
 "# Skill Catalog — ดัชนีสกิลสำหรับ /skill-router",
 "",
 f"คลังสกิลทั้งหมด {total} ตัว (สร้างอัตโนมัติจาก `standard/` ด้วย `python _make_catalog.py`)",
 "ใช้โดย `/skill-router` เพื่อแมตช์ประโยคผู้ใช้กับสกิลที่เกี่ยวข้อง — เลือกจากรายการนี้เท่านั้น ห้ามแต่งชื่อสกิลที่ไม่มี",
 "",
]
for k in order:
    for (key, label), items in sorted(groups.items()):
        if key != k:
            continue
        lines.append(f"## {label}  ({len(items)})")
        for slug, sd in sorted(items):
            lines.append(f"- `/{slug}` — {sd}")
        lines.append("")

with open(OUT, "w", encoding="utf-8") as fh:
    fh.write("\n".join(lines))
print(f"สร้าง skill-catalog.md : {total} สกิล, {len(groups)} กลุ่ม")
