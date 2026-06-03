# -*- coding: utf-8 -*-
# แปลงสกิลชุด A-D (ไฟล์ .md) เป็นโครงสร้างมาตรฐาน Claude Code: standard/<slug>/SKILL.md
# - ใช้ค่า frontmatter `name:` เป็นชื่อโฟลเดอร์ (slug)
# - ข้าม README, draft, ไฟล์ pointer (status: merged), โฟลเดอร์ personal-skills และ standard เอง
# - ตรวจ slug ซ้ำ (เติม -2, -3 ... ถ้าชน)
import os, re

ROOT = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(ROOT, "standard")
SKIP_DIRS = {"standard", "personal-skills"}
SKIP_FILES = {"README.md", "output-modes-draft.md"}

def read_frontmatter_name(text):
    # ดึงค่า name: จาก frontmatter (บล็อก --- ... --- ด้านบน)
    m = re.search(r"^---\s*\n(.*?)\n---", text, re.DOTALL)
    if not m:
        return None, False
    fm = m.group(1)
    merged = bool(re.search(r"^status:\s*merged", fm, re.MULTILINE))
    nm = re.search(r"^name:\s*(.+?)\s*$", fm, re.MULTILINE)
    name = nm.group(1).strip() if nm else None
    return name, merged

def src_label(rel):
    if os.sep not in rel:
        return "A (อาชีพ_skill)"
    top = rel.split(os.sep)[0]
    return {"pro-bundle": "B (Pro Bundle)", "commands": "C (คำสั่งลัด)",
            "jobsdb-ai-skills": "D (JobsDB AI)"}.get(top, top)

count, skipped_merged, collisions = 0, [], []
used = {}
report = []

for dirpath, dirnames, filenames in os.walk(ROOT):
    dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
    for fn in filenames:
        if not fn.endswith(".md") or fn in SKIP_FILES:
            continue
        full = os.path.join(dirpath, fn)
        rel = os.path.relpath(full, ROOT)
        with open(full, encoding="utf-8") as f:
            text = f.read()
        name, merged = read_frontmatter_name(text)
        if merged:
            skipped_merged.append(rel)
            continue
        if not name:
            report.append(f"  ⚠️ ไม่มี name: {rel}")
            continue
        slug = name
        if slug in used:
            collisions.append((slug, used[slug], rel))
            n = 2
            while f"{slug}-{n}" in used:
                n += 1
            slug = f"{slug}-{n}"
        used[slug] = rel
        d = os.path.join(OUT, slug)
        os.makedirs(d, exist_ok=True)
        with open(os.path.join(d, "SKILL.md"), "w", encoding="utf-8") as f:
            f.write(text)
        count += 1

print(f"แปลงเป็น standard/<slug>/SKILL.md : {count} skills")
print(f"ข้าม pointer (merged) : {len(skipped_merged)} ไฟล์")
if collisions:
    print(f"\n⚠️ slug ซ้ำ {len(collisions)} คู่ (เติมเลขท้ายให้):")
    for slug, first, dup in collisions:
        print(f"  - '{slug}': {first}  <->  {dup}")
else:
    print("ไม่มี slug ซ้ำ")
for line in report:
    print(line)
