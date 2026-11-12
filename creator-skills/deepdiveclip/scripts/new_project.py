# -*- coding: utf-8 -*-
# 21/10/2026 ตั้งโปรเจกต์คลิปเจาะลึกใหม่จากสคริปต์ในสกิล deepdiveclip
# ใช้: python new_project.py $WORK/<ชื่อโปรเจกต์>
# คัดลอกสคริปต์ไปตำแหน่งที่ใช้จริง แทน __PROJECT__ ด้วยโฟลเดอร์ปลายทาง สร้างโฟลเดอร์ย่อย และคัดลอกฟอนต์
import io, os, shutil, sys

HERE = os.path.dirname(os.path.abspath(__file__))
DST = os.path.abspath(sys.argv[1]).replace('\\', '/')
LAYOUT = {
    'timeline.py': 'src', 'make_html.py': 'src', 'vo_prep.py': 'src', 'assemble.py': 'src', 'combine.py': 'src',
    'prep_img.py': 'src', 'gen_prompts.py': 'src', 'gen_loop.sh': 'src', 'kill_bridge.ps1': 'src', 'intro_engine.html': 'src',
    'build_mix.py': 'audio', 'render.py': '.',
    'pose/pose.html': 'qc/pose', 'pose/run_pose.py': 'qc/pose',
    'youtube/upload.py': 'youtube', 'youtube/make_meta.py': 'youtube', 'youtube/check.py': 'youtube',
}
for d in ['src', 'audio', 'vo/paras', 'vo/prep', 'vo/tmp', 'gen', 'img', 'qc/pose', 'parts', 'share', 'combined', 'youtube', 'ref_bgm', 'old']:
    os.makedirs(os.path.join(DST, d), exist_ok=True)
for src, sub in LAYOUT.items():
    out = os.path.join(DST, sub, os.path.basename(src))
    if os.path.exists(out):
        print('ข้าม (มีอยู่แล้ว)', out); continue
    s = io.open(os.path.join(HERE, src), encoding='utf-8').read().replace('__PROJECT__', DST)
    io.open(out, 'w', encoding='utf-8', newline='\n').write(s)
    print('ok', out)
if not os.path.exists(os.path.join(DST, 'fonts')):
    shutil.copytree(os.path.join(HERE, 'fonts'), os.path.join(DST, 'fonts'))
    print('ok fonts/')
print('ต่อไป: วางโลโก้ img/s01_4.png และพื้นหลังฉากชื่อเรื่อง img/warehouse.png แล้วทำตาม SKILL.md ข้อ 2')
