# -*- coding: utf-8 -*-
# 21/10/2026 สร้าง meta.json ของคลิปรวม (UTF-8) สำหรับ upload.py · เวลาสารบัญคิดจากจุดต่อ + เวลาในคลิปเจาะลึก
# ตั้งค่าแบรนด์ ช่องทางติดต่อ และเครดิตเพลงในบล็อก CONFIG ด้านล่างก่อนรัน
import io, json, sys
sys.path.insert(0, '__PROJECT__/src')
from timeline import VO

# ---------------- CONFIG: แก้ให้ตรงงานของคุณ ----------------
BRAND = 'ชื่อแบรนด์ของคุณ'
INTRO_TITLE = 'แนะนำแบรนด์'                 # หัวข้อแรกในสารบัญ (ช่วงคลิปแนะนำเดิม)
LINKS = 'example.com'                        # เว็บไซต์
CONTACT = 'you@example.com · 02-XXX-XXXX'    # อีเมล เบอร์โทร
ABOUT = 'คำอธิบายแบรนด์หนึ่งถึงสองประโยค'
SUBSIDIARIES = [                             # ใส่ได้ตามจริง เว้นว่างถ้าไม่มี
    'บริษัท A: สิ่งที่ทำ (จังหวัด)',
    'บริษัท B: สิ่งที่ทำ (จังหวัด)',
]
SYSTEMS = [                                  # 1 บรรทัดต่อ 1 ระบบ ตรงกับย่อหน้า v02 ถึง v07
    '1. ระบบที่ 1 สรุปสิ่งที่ทำ',
    '2. ระบบที่ 2 สรุปสิ่งที่ทำ',
]
CREDITS = 'Music: <ชื่อเพลง> by <ศิลปิน>\nLink to Video: <ลิงก์ตามเงื่อนไขเจ้าของเพลง>'   # ต้องสะกดตรงต้นฉบับ
VIDEO_FILE = '__PROJECT__/combined/combined.mp4'
THUMB_FILE = '__PROJECT__/combined/cover.jpg'
TITLE = f'{BRAND}: ชื่อคลิปฉบับเต็ม'          # ไม่เกิน 100 ตัวอักษร
TAGS = [BRAND, 'AI', 'ระบบคลังสินค้า', 'ระบบโรงงาน']
# -------------------------------------------------------------

J = 2413 / 24   # จุดต่อ คลิปแนะนำเดิม -> คลิปเจาะลึก
mmss = lambda t: '%d:%02d' % (int(t) // 60, int(t) % 60)
chapters = [
    (0, INTRO_TITLE),
    (J, 'เจาะลึกระบบ'),
    (J + VO['v02'], '01 ระบบที่ 1'),
    (J + VO['v04'], '02 ระบบที่ 2'),
    (J + VO['v05'], '03 ระบบที่ 3'),
    (J + VO['v06'], '04 ระบบที่ 4'),
    (J + VO['v07'], '05 ระบบที่ 5'),
    (J + VO['v08'], 'สรุปและช่องทางติดต่อ'),
]
desc = (
    ABOUT + '\n\n'
    'สารบัญ\n' + '\n'.join(f'{mmss(t)} {name}' for t, name in chapters) + '\n\n'
    + ('บริษัทในเครือ\n' + '\n'.join(SUBSIDIARIES) + '\n\n' if SUBSIDIARIES else '')
    + 'เจาะลึกระบบ\n' + '\n'.join(SYSTEMS) + '\n\n'
    'ติดต่อ\n'
    + LINKS + '\n'
    + CONTACT + '\n\n'
    'เสียงบรรยาย เพลง และภาพประกอบบางส่วนในคลิปสร้างด้วย AI\n\n'
    'Credits:\n'
    + CREDITS
)
meta = {
    'file': VIDEO_FILE,
    'thumb': THUMB_FILE,
    'title': TITLE,
    'description': desc,
    'tags': TAGS,
    'categoryId': '28',
    'privacyStatus': 'unlisted',
}
assert len(meta['title']) <= 100, len(meta['title'])
assert '—' not in desc and '–' not in desc
io.open('__PROJECT__/youtube/meta.json', 'w', encoding='utf-8').write(json.dumps(meta, ensure_ascii=False, indent=1))
print('title', len(meta['title']), 'chars · desc', len(desc), 'chars')
print('\n'.join(f'{mmss(t)} {n}' for t, n in chapters))
