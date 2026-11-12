# -*- coding: utf-8 -*-
"""สลับฟอนต์ทั้งเล่มจาก Sarabun เป็น Kanit ในโปรเจกต์ ebook (สร้างด้วยสกิล ebook) แล้วให้ build ใหม่

  python to_kanit.py <project-dir>          แก้ไฟล์ + คัดลอกฟอนต์ (สำรองไฟล์เดิมเป็น .sarabun.bak ครั้งแรกครั้งเดียว)
  python to_kanit.py <project-dir> --undo   คืนไฟล์จาก .sarabun.bak

ไม่แตะ raw/ (เนื้อหา) · ลบแคชแผนภาพ diagrams/*.png เพื่อให้วาดใหม่ด้วยฟอนต์ใหม่
Kanit มีน้ำหนัก Light/Regular/Medium/SemiBold/Bold/ExtraBold/Italic ชื่อไฟล์ตรงกับที่สคริปต์เดิมเรียก Sarabun-<w>.ttf
"""
import glob, io, os, re, shutil, sys, pathlib

SK = pathlib.Path(__file__).resolve().parent.parent
KANIT = SK / 'fonts' / 'kanit'
proj = pathlib.Path(sys.argv[1]).resolve()
undo = '--undo' in sys.argv

files = [f for pat in ('*.mjs', '*.js', '*.css', '*.py', '*.html') for f in glob.glob(str(proj / pat))]
files = [f for f in files if not f.endswith('.bak')]

if undo:
    n = 0
    for b in glob.glob(str(proj / '*.sarabun.bak')):
        shutil.copyfile(b, b[:-len('.sarabun.bak')]); n += 1
    print('คืนไฟล์', n)
    sys.exit(0)

(proj / 'fonts').mkdir(exist_ok=True)
for f in KANIT.glob('*.ttf'):
    shutil.copyfile(f, proj / 'fonts' / f.name)
shutil.copyfile(KANIT / 'OFL.txt', proj / 'fonts' / 'Kanit-OFL.txt')

changed = []
for f in files:
    s = io.open(f, encoding='utf-8').read()
    if 'Sarabun' not in s:
        continue
    t = s.replace('Sarabun-', 'Kanit-').replace("'Sarabun'", "'Kanit'").replace('"Sarabun"', '"Kanit"')
    t = re.sub(r'font-family\s*:\s*Sarabun\b', 'font-family:Kanit', t)
    t = re.sub(r'(?<![\w-])Sarabun(?=[,\'"; ])', 'Kanit', t)   # ชื่อฟอนต์ที่เหลือในรายการ fallback
    if t != s:
        bak = f + '.sarabun.bak'
        if not os.path.exists(bak):
            shutil.copyfile(f, bak)
        io.open(f, 'w', encoding='utf-8').write(t)
        changed.append(os.path.basename(f))

# น้ำหนักที่สคริปต์เรียกแต่ Kanit ไม่มี
need = set(re.findall(r'Kanit-([A-Za-z]+)\.ttf', ' '.join(io.open(proj / c, encoding='utf-8').read() for c in changed)))
missing = sorted(w for w in need if not (proj / 'fonts' / f'Kanit-{w}.ttf').exists())
for png in glob.glob(str(proj / 'diagrams' / '*.png')):
    os.remove(png)
print('แก้', changed, '| น้ำหนักที่ไม่มี', missing or '-')
