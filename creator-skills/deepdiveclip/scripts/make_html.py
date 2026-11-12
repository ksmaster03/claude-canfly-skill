# -*- coding: utf-8 -*-
# 20/10/2026 สร้าง intro.html ของคลิปเจาะลึกระบบ จากหน้าเรนเดอร์ src/intro_engine.html
# เพิ่มชั้น "การ์ดระบบ" ที่ค้างข้ามหลายช็อต และหัวข้อย่อยโผล่ตรงคำพูด · เวลาทั้งหมดมาจาก timeline.py
# ใช้: python src/make_html.py แล้วเรนเดอร์ด้วย render.py (ห้ามแก้ intro.html มือ)
import io, json, sys
sys.path.insert(0, '__PROJECT__/src')
from timeline import VO, at, end, TOP, END_CARD, TOTAL, TITLE

P = '__PROJECT__/'
# ตั้งค่าแบรนด์ของคุณ ค่าเหล่านี้ถูกฉีดเข้า const BRAND ใน intro.html (ชื่อ สโลแกน การ์ดท้าย)
BRAND = {'name': 'BRAND NAME', 'tagline': 'สโลแกนหนึ่งบรรทัด', 'cta': 'คุยกับเราเรื่องระบบของคุณ',
         'companies': 'COMPANY A &nbsp;·&nbsp; COMPANY B', 'urls': 'example.com',
         'contact': 'you@example.com &nbsp;·&nbsp; 02-XXX-XXXX', 'bill': 'มาตรฐานหรือใบรับรอง (ถ้ามี)',
         'credit': 'Music: <ชื่อเพลง> · <ศิลปิน> · <ลิงก์ตามเงื่อนไขเจ้าของเพลง>'}
s = io.open(P + 'src/intro_engine.html', encoding='utf-8').read()


def rep(old, new, n=1):
    global s
    assert s.count(old) == n, (old[:70], s.count(old))
    s = s.replace(old, new)


GOLD, OLIVE, BLUE, GREEN, ORANGE = '#e2b04a', '#a9c46c', '#6ea8ff', '#5fd38d', '#e8946a'


def full(t, img, g='steel', s_=(1.1, 1.03), x0=(0, 0), y0=(0, 0), x=None):
    d = {'t': t, 'k': 'full', 'img': img, 'g': g, 's': list(s_), 'x0': list(x0), 'y0': list(y0)}
    if x: d['x'] = x
    return d


def hook(l1, l2=None, d=0.15, e=0.2):
    return {'kind': 'card', 'l1': l1, **({'l2': l2} if l2 else {}), 'd': d, 'e': e}


Z_IN, Z_OUT = (1.12, 1.03), (1.03, 1.12)
SHOTS = [
    {'t': 0.0, 'k': 'black'},
    # เปิด: ความพร้อมรบเริ่มที่ไหน
    full(VO['v01'], 'm01-base-dawn.jpg', 'steel', (1.14, 1.04), (0, 0), (1, -1), hook('ความพร้อมรบ', 'ไม่ได้เริ่มที่สนามฝึก', 0.3, 0.15)),
    full(at('v01', 'แต่เริ่มที่คลัง', -0.1), 'm04-bunker.jpg', 'steel', Z_IN, x=hook('คลัง', d=0.25, e=0.05)),
    full(at('v01', 'ที่โรงซ่อม', -0.1), 'm10-motorpool.jpg', 'steel', Z_OUT, x=hook('โรงซ่อม', d=0.2, e=0.05)),
    full(at('v01', 'ที่ความรู้', -0.1), 'm15-archive.jpg', 'warm', Z_IN, x=hook('ความรู้', d=0.2, e=0.05)),
    full(at('v01', 'และที่ร่างกาย', -0.1), 'm22-pushup.jpg', 'steel', Z_OUT, x=hook('กำลังพล', d=0.6, e=0.1)),
    {'t': TITLE, 'k': 'title', 'v': 'portal', 'x': {'kind': 'title', 'l1': BRAND['name'], 'l2': 'เจาะลึก 5 ระบบ', 'd': 0.02, 'e': 0.2}},
    # 01 คลังสิ่งอุปกรณ์
    full(VO['v02'], 'm02-receive.jpg', 'steel', Z_IN, (0, 0), (0, 1)),
    full(at('v02', 'ติดป้าย', -0.2), 'm03-rfid.jpg', 'steel', Z_OUT),
    full(at('v02', 'ระบบรู้ทันที', -0.1), 'g-d01-depot.jpg', 'steel', Z_IN, (1, -1)),
    full(at('v02', 'ตั้งแต่สเบียง', -0.1), 'm07-rations.jpg', 'steel', Z_OUT),
    full(at('v02', 'น้ำมัน', -0.1), 'm06-fuel.jpg', 'warm', Z_IN),
    full(at('v02', 'กระสุน', -0.4), 'm04-bunker.jpg', 'steel', Z_OUT, (-1, 1)),
    full(at('v02', 'ทุกการเบิก', -0.1), 'm05-issue.jpg', 'steel', Z_IN),
    # 01 ระบบผลิต
    full(VO['v03'], 'm08-factory.jpg', 'steel', Z_IN, (0, 0), (0, 1)),
    full(at('v03', 'ผ่านการตรวจ', -0.1), 'm09-qc.jpg', 'steel', Z_OUT),
    full(at('v03', 'ถ้าลอด', -0.1), 'g-d02-plant.jpg', 'steel', Z_IN),
    full(at('v03', 'นี่คืองาน', -0.1), 't-booth-automation.jpg', 'steel', (1.04, 1.12)),
    full(at('v03', '18ปี', -0.6), 't-site-warehouse.jpg', 'steel', Z_IN),
    # 02 ซ่อมบำรุง
    full(VO['v04'], 'm10-motorpool.jpg', 'dim', Z_IN, x=hook('ใช้การไม่ได้', 'ในวันที่ต้องใช้ ก็ไม่มีความหมาย', 0.3, 0.2)),
    full(at('v04', 'ระบบซ่อมบำรุง', -0.15), 'm12-heli.jpg', 'steel', Z_OUT),
    full(at('v04', 'สแกนครั้งเดียว', -0.1), 'm11-qr.jpg', 'steel', Z_IN),
    full(at('v04', 'เซ็นเซอร์', -0.1), 'm13-sensor.jpg', 'steel', Z_OUT),
    full(at('v04', 'แล้วเอไอ', -0.1), 'g-d03-hangar.jpg', 'steel', Z_IN),
    full(at('v04', 'ผู้บังครับ', -0.1), 'm14-ops.jpg', 'steel', Z_OUT),
    # 03 สมองที่สอง
    full(VO['v05'], 'm15-archive.jpg', 'dim', Z_IN, x=hook('ความรู้ที่มีค่าที่สุด', 'มักอยู่ในหัวคน', 0.3, 0.2)),
    full(at('v05', 'ญญาคือ', -0.3), 'g-d13-brain.jpg', 'steel', Z_OUT),
    full(at('v05', 'เก็บคู่มือ', -0.1), 'm17-ask.jpg', 'warm', Z_IN),
    full(at('v05', 'ติดตั้งใน', -0.1), 'm16-airgap.jpg', 'steel', Z_OUT),
    full(at('v05', 'และถ้าไม่มี', -0.1), 'g-d12-onprem-ai.jpg', 'steel', Z_IN),
    # 04 เกมจำลองการฝึก
    full(VO['v06'], 'm04-bunker.jpg', 'dim', Z_IN, x=hook('กระสุน น้ำมัน และเวลา', 'การฝึกจริงทุกครั้งมีต้นทุน', 0.3, 0.2)),
    full(at('v06', 'ลองการฝึก', -0.6), 'm18-simroom.jpg', 'steel', Z_OUT),
    full(at('v06', 'ทั้งขะบวน', -0.1), 'm21-3dworld.jpg', 'steel', Z_IN),
    full(at('v06', 'ฝึกพร้อมกัน', -0.1), 'm19-vr.jpg', 'steel', Z_OUT),
    full(at('v06', 'ทุกการตัดสินใจ', -0.1), 'm20-aar.jpg', 'steel', Z_IN),
    {'t': at('v06', 'ทีมเราสร้าง', -0.15), 'k': 'screen', 'img': 'game-warehouse.jpg', 'ar': 1920 / 1270, 'side': 1},
    # 05 ทดสอบสมรรถภาพ
    full(VO['v07'], 'm22-pushup.jpg', 'steel', Z_IN),
    full(at('v07', 'ลุกนั่ง', -0.1), 'm23-situp.jpg', 'steel', Z_OUT),
    full(at('v07', 'และวิ่ง', -0.1), 'm24-run.jpg', 'warm', Z_IN),
    dict(full(at('v07', 'กล้องเอไอ', -0.1), 'm22-pushup.jpg', 'steel', (1.12, 1.05), (-4, 0)), pose=1, label='มุมศอก 120° · ยังลงไม่สุด ไม่นับ', lab=[1330, 560], labw=520),
    full(at('v07', 'คะแนนออก', -0.1), 'm25-score.jpg', 'steel', Z_OUT),
    dict(full(at('v07', 'ด้วยเทคโน', -0.1), 'm23-situp.jpg', 'warm', (1.12, 1.04), (-6, 0)), pose=1, label='ลุกนั่ง · เข่างอ 76° · มือประสานท้ายทอย', lab=[1120, 520], labw=640),
    # ปิด
    full(VO['v08'], 'm04-bunker.jpg', 'steel', Z_IN, x=hook('คลัง', d=0.1, e=0.02)),
    full(at('v08', 'ซ่อมบำรุง', -0.05), 'm10-motorpool.jpg', 'steel', Z_OUT, x=hook('ซ่อมบำรุง', d=0.1, e=0.02)),
    full(at('v08', 'ความรู้', -0.05), 'm15-archive.jpg', 'warm', Z_IN, x=hook('ความรู้', d=0.1, e=0.02)),
    full(at('v08', 'การฝึก', -0.05), 'm18-simroom.jpg', 'steel', Z_OUT, x=hook('การฝึก', d=0.1, e=0.02)),
    full(at('v08', 'กำลังผล', -0.05), 'm24-run.jpg', 'warm', Z_IN, x=hook('กำลังพล', d=0.1, e=0.05)),
    full(at('v08', 'ทุกอย่าง', -0.1), 'm26-closing.jpg', 'warm', (1.1, 1.02), x=hook('ทุกอย่างอยู่ในระบบ', 'ที่หน่วยดูแลเอง', 0.2, 0.2)),
    {'t': TOP - 0.05, 'k': 'title', 'v': 'portal', 'x': {'kind': 'title', 'l1': BRAND['name'], 'l2': BRAND['tagline'], 'd': 0.02, 'e': 0.3}},
    {'t': END_CARD, 'k': 'black', 'x': {'kind': 'end', 'd': 0.0, 'e': 0.6}},
]


def card(a, b, ac, n, ch, nm, sub, items):
    return {'a': a, 'b': b, 'ac': ac, 'n': n, 'ch': ch, 'nm': nm, 'sub': sub,
            'f': [x for x, _ in items], 'ft': [t for _, t in items]}


CARDS = [
    card(VO['v02'] + 0.1, end('v02', 0.35), GOLD, '01 / 05', 'คลังสิ่งอุปกรณ์', 'คลัง สป. อัจฉริยะ', 'ระบบคลังสินค้า WMS', [
        ('ตรวจสภาพและติด RFID ทุกหีบ', at('v02', 'ติดป้าย')),
        ('รู้ล็อต หมายเลข และตำแหน่งทันที', at('v02', 'ระบบรู้ทันที')),
        ('เสบียง น้ำมัน จนถึงกระสุน', at('v02', 'ตั้งแต่สเบียง')),
        ('นับอายุ เตือนก่อนหมดอายุ', at('v02', 'ระบบนับอายุ')),
        ('เบิกตามสิทธิ์ ตรวจย้อนได้ทุกครั้ง', at('v02', 'และเบิก')),
    ]),
    card(VO['v03'] + 0.1, end('v03', 0.35), GOLD, '01 / 05', 'การผลิตยุทโธปกรณ์', 'ระบบควบคุมการผลิต', 'MES สำหรับอุตสาหกรรมป้องกันประเทศ', [
        ('ติดตามทุกชิ้นงาน วัตถุดิบถึงส่งมอบ', at('v03', 'ระบบควบคุม')),
        ('ตรวจคุณภาพทุกขั้นตอน', at('v03', 'ผ่านการตรวจ')),
        ('ล็อตมีปัญหา ย้อนถึงต้นทางได้ทันที', at('v03', 'ถ้าลอด')),
        ('ประสบการณ์จริงในโรงงานและคลัง', at('v03', 'นี่คืองาน')),
    ]),
    card(at('v04', 'ระบบซ่อมบำรุง', -0.1), end('v04', 0.35), ORANGE, '02 / 05', 'ซ่อมบำรุงยุทโธปกรณ์', 'ระบบแจ้งซ่อม', 'ซ่อมก่อนเสีย พร้อมใช้ทุกวัน', [
        ('ทะเบียนรถ อากาศยาน เครื่องปั่นไฟ', at('v04', 'ขึ้นทะเบีย')),
        ('สแกน QR เห็นประวัติซ่อมทั้งหมด', at('v04', 'สแกนครั้งเดียว')),
        ('เซนเซอร์เตือนเมื่อเกินเกณฑ์', at('v04', 'เซ็นเซอร์')),
        ('AI วางแผนซ่อมก่อนเสีย', at('v04', 'แล้วเอไอ')),
        ('ความพร้อมใช้ บนหน้าจอเดียว', at('v04', 'ผู้บังครับ')),
    ]),
    card(at('v05', 'ญญาคือ', -0.2), end('v05', 0.35), GREEN, '03 / 05', 'สมองที่สองของ AI', 'คลังความรู้', 'ความรู้ขององค์กรให้ AI ใช้', [
        ('คู่มือ ระเบียบ บทเรียนจากการฝึก', at('v05', 'เก็บคู่มือ')),
        ('ค้นได้ด้วยภาษาไทย', at('v05', 'ด้วยภาษาไทย')),
        ('ติดตั้งในเครือข่ายปิด ไม่ต่ออินเทอร์เน็ต', at('v05', 'ติดตั้งใน')),
        ('ไม่มีข้อมูลจริง ไม่ตอบ ไม่แต่งเรื่อง', at('v05', 'มันจะไม่ตอบ')),
    ]),
    card(at('v06', 'ลองการฝึก', -0.6), end('v06', 0.35), BLUE, '04 / 05', 'การฝึกเสมือนจริง', 'เกมจำลองการฝึก 3 มิติ', '', [
        ('ซ้อมสถานการณ์ซ้ำได้ไม่จำกัด', at('v06', 'ให้กำลังพล')),
        ('ขบวนลำเลียง งานคลัง เหตุฉุกเฉิน', at('v06', 'ทั้งขะบวน')),
        ('ฝึกพร้อมกันได้ทั้งทีม', at('v06', 'ฝึกพร้อมกัน')),
        ('บันทึกทุกการตัดสินใจ ทบทวนหลังฝึก', at('v06', 'ทุกการตัดสินใจ')),
        ('ทีมเรามีเกม 3 มิติที่ใช้งานจริงแล้ว', at('v06', 'ทีมเราสร้าง')),
    ]),
    card(VO['v07'] + 0.1, end('v07', 0.35), OLIVE, '05 / 05', 'ทดสอบสมรรถภาพร่างกาย', 'กล้อง AI วัดสมรรถภาพ', 'ทดสอบประจำปี 3 สถานี', [
        ('ดันพื้น · ลุกนั่ง · วิ่ง 2 กม.', at('v07', 'สถานี')),
        ('นับครั้งเอง ท่าไม่ถึงไม่นับ', at('v07', 'กล้องเอไอ')),
        ('คะแนนออกทันที เข้าประวัติกำลังพล', at('v07', 'คะแนนออก')),
        ('ผลโปร่งใส ตรวจย้อนได้', at('v07', 'ผลโปร')),
        ('เทคโนโลยีเดียวกับระบบวัดการซ้อมกีฬา', at('v07', 'ด้วยเทคโน')),
    ]),
]

# แฟลชและแสงรั่วตรงจุดเปลี่ยนระบบ
SECT = [VO['v02'], VO['v03'], VO['v04'], VO['v05'], VO['v06'], VO['v07'], VO['v08']]
HITS = [[0.0, .3], [TITLE, 1.0]] + [[round(t, 2), .3] for t in SECT] + [[TOP - 0.05, .9], [END_CARD, .4]]
LEAKS = [[round(t - 0.25, 2), 0.5] for t in SECT] + [[round(TITLE - 0.25, 2), 0.5], [round(TOP - 0.3, 2), 0.6]]

POSES = json.load(io.open(P + 'src/poses.json'))   # จุดข้อต่อจาก MediaPipe Pose บนภาพจริง (qc/pose/run_pose.py)
js = lambda o: json.dumps(o, ensure_ascii=False)
start = s.index('const AC = ')
stop = s.index('// ---------- อนุภาคคลื่น')
s = s[:start] + ('// 20/10/2026 สร้างจาก src/make_html.py และ src/timeline.py (เวลาตามคำพูดจริงของเสียงพากย์)\n'
                 f'const SHOTS = {js(SHOTS)};\n'
                 f'const CARDS = {js(CARDS)};\n'
                 'const FOUR = [];\n'
                 f'const POSES = {js(POSES)};\n'
                 f'const LEAKS = {js(LEAKS)};\n'
                 f'const HITS = {js(HITS)};\n\n') + s[stop:]

rep('const W = 1920, H = 1080, TOTAL = 120.0;', f'const W = 1920, H = 1080, TOTAL = {TOTAL};')
i = s.index('const BRAND = {'); j = s.index('};', i) + 2
s = s[:i] + 'const BRAND = ' + js(BRAND) + ';' + s[j:]
rep('<!-- 19/10/2026 เครื่องยนต์หน้าเรนเดอร์คลิปแนะนำ/เจาะลึกแนว cinematic 16:9',
    '<!-- 20/10/2026 คลิปเจาะลึกระบบ สร้างจาก src/make_html.py ห้ามแก้มือ\n'
    '     ต้นแบบ: เครื่องยนต์หน้าเรนเดอร์แนว cinematic 16:9')

# ชั้นการ์ดระบบ
rep('  #scrim { position:absolute; inset:0; opacity:0; }',
    '  #scrim { position:absolute; inset:0; opacity:0; }\n'
    '  #cscrim { position:absolute; inset:0; opacity:0; background:linear-gradient(90deg, rgba(0,0,0,.86) 0%, rgba(0,0,0,.68) 40%, rgba(0,0,0,0) 66%); }\n'
    '  #card { position:absolute; inset:0; opacity:0; }\n'
    '  #card .ft { transition:none; }\n'
    '  .pl { stroke:#7dffb0; stroke-width:5; stroke-linecap:round; stroke-dasharray:1; stroke-dashoffset:1; filter:drop-shadow(0 0 6px rgba(80,255,150,.9)); }\n'
    '  .pj { fill:#ffffff; opacity:0; }\n'
    '  .plab { opacity:0; } .plab rect { fill:rgba(8,12,16,.8); stroke:#e2b04a; stroke-width:2; } .plab text { font-family:Kanit; font-weight:400; font-size:34px; fill:#fff; }')
rep('  <div id="scrim"></div>\n  <div id="txt"></div>', '  <div id="scrim"></div>\n  <div id="cscrim"></div>\n  <div id="card"></div>\n  <div id="txt"></div>')

POSE_JS = r'''
// ---------- เส้นโครงร่างจาก MediaPipe Pose (จุดข้อต่อจริงของคนในภาพ) ----------
// วาดเฉพาะซีกที่กล้องเห็นชัด (ขาสองข้างที่ทับกันทำให้เส้นไขว้เป็นฟันเลื่อย)
function poseSvg(S) {
  const p = POSES[S.img]; let h = '';
  const vis = ids => ids.reduce((a, i) => a + p[i][2], 0);
  const L = vis([11, 13, 15, 23, 25, 27]) >= vis([12, 14, 16, 24, 26, 28]);
  const [sh, el, wr, hp, kn, an] = L ? [11, 13, 15, 23, 25, 27] : [12, 14, 16, 24, 26, 28];
  const PE = [[0, sh], [sh, el], [el, wr], [sh, hp], [hp, kn], [kn, an]];
  for (const [a, b] of PE) if (p[a][2] > .5 && p[b][2] > .5) h += `<line class="pl" pathLength="1" x1="${p[a][0]}" y1="${p[a][1]}" x2="${p[b][0]}" y2="${p[b][1]}"/>`;
  for (const i of [0, sh, el, wr, hp, kn, an]) if (p[i][2] > .5) h += `<circle class="pj" cx="${p[i][0]}" cy="${p[i][1]}" r="8"/>`;
  h += `<g class="plab" transform="translate(${S.lab[0]},${S.lab[1]})"><rect x="0" y="-46" rx="10" width="${S.labw}" height="62"/><text x="20" y="-3">${S.label}</text></g>`;
  return `<svg class="ph" id="phs" viewBox="0 96 1920 888" preserveAspectRatio="none" style="overflow:visible">${h}</svg>`;
}
'''
ANIM = r'''
    const phs = $('phs');
    if (phs) {
      phs.style.transform = ph.style.transform;
      const q = ease(clamp((tau - 0.35) / 0.8, 0, 1));
      phs.querySelectorAll('.pl').forEach(l => l.style.strokeDashoffset = (1 - q).toFixed(3));
      phs.querySelectorAll('.pj').forEach(c => c.style.opacity = ease(clamp((tau - 0.9) / 0.3, 0, 1)).toFixed(3));
      const lb = phs.querySelector('.plab'); if (lb) lb.style.opacity = ease(clamp((tau - 1.2) / 0.4, 0, 1)).toFixed(3);
    }
  }'''

CARD_JS = r'''
// ---------- การ์ดระบบ ค้างข้ามหลายช็อต หัวข้อย่อยโผล่ตรงคำพูด ----------
let curCard = -2;
function buildCard(C, seed) {
  const X = $('card');
  if (!C) { X.innerHTML = ''; return; }
  X.innerHTML = `<div class="blk" style="--ac:${C.ac}"><div class="eb cf"><span class="n">${C.n}</span><span>${C.ch}</span></div>`
    + `<div class="nm${isThai(C.nm) ? ' th' : ''}">${glyphs(C.nm, seed, 0.3)}</div>`
    + (C.sub ? `<div class="sub cf">${C.sub}</div>` : '')
    + `<div class="rule" id="crule"></div>`
    + C.f.map(x => `<div class="ft cstep">${x}</div>`).join('') + '</div>';
  const nm = X.querySelector('.nm');
  if (nm && !isThai(C.nm)) { const w = nm.scrollWidth; if (w > 860) nm.style.fontSize = (78 * 860 / w).toFixed(1) + 'px'; }
}
function updateCard(t) {
  let ci = -1;
  for (let i = 0; i < CARDS.length; i++) if (t >= CARDS[i].a && t < CARDS[i].b) ci = i;
  if (ci !== curCard) { buildCard(CARDS[ci], ci >= 0 ? Math.round(CARDS[ci].a * 100) + 3 : 0); curCard = ci; }
  const X = $('card'), cs = $('cscrim');
  if (ci < 0) { X.style.opacity = 0; cs.style.opacity = 0; return; }
  const C = CARDS[ci], dt = t - C.a;
  const o = clamp(dt / 0.3, 0, 1) * clamp((C.b - t) / 0.35, 0, 1);
  X.style.opacity = o.toFixed(3); cs.style.opacity = o.toFixed(3);
  revealGlyphs(X, dt - 0.1, 0.32);
  X.querySelectorAll('.cf').forEach((el, i) => { const p = ease(clamp((dt - 0.2 - i * 0.12) / 0.45, 0, 1)); el.style.opacity = p.toFixed(3); el.style.transform = `translateY(${((1 - p) * 10).toFixed(1)}px)`; });
  const ru = $('crule'); if (ru) ru.style.width = (130 * ease(clamp((dt - 0.35) / 0.5, 0, 1))).toFixed(0) + 'px';
  let last = -1; C.ft.forEach((f, i) => { if (t >= f) last = i; });
  X.querySelectorAll('.cstep').forEach((el, i) => {
    const p = ease(clamp((t - C.ft[i]) / 0.4, 0, 1));
    el.style.opacity = (p * (i === last ? 1 : 0.7)).toFixed(3);
    el.style.transform = `translateX(${((1 - p) * -16).toFixed(1)}px)`;
    el.style.color = i === last ? '#ffffff' : '#c9d1da';
  });
}
'''
rep('window.renderAt = function (t) {', CARD_JS + '\nwindow.renderAt = function (t) {')
rep('  gr.putImageData(NOISE[Math.floor(t * 24) % 8], 0, 0);\n};', '  updateCard(t);\n  gr.putImageData(NOISE[Math.floor(t * 24) % 8], 0, 0);\n};')

# ช็อตจอเอียงต้องมีป้ายบอกว่าเป็นภาพจากเกมจริง
rep("    P.innerHTML = `<div class=\"scr\" id=\"ph\" style=\"width:${w.toFixed(0)}px;height:${h.toFixed(0)}px;left:${(cx - w / 2).toFixed(0)}px;top:${(cy - h / 2).toFixed(0)}px\"><img src=\"img/${S.img}\"></div>`;",
    "    P.innerHTML = `<div class=\"scr\" id=\"ph\" style=\"width:${w.toFixed(0)}px;height:${h.toFixed(0)}px;left:${(cx - w / 2).toFixed(0)}px;top:${(cy - h / 2).toFixed(0)}px\"><img src=\"img/${S.img}\"></div>`\n"
    "      + '<div style=\"position:absolute;left:1000px;top:906px;width:820px;text-align:center;font-family:Kanit;font-weight:300;font-size:30px;color:#c9d1da\">ภาพจากเกม 3 มิติหลายผู้เล่นที่ทีมเราสร้างและเปิดใช้งานจริง</div>';")
rep("    let w = 840, h = w / S.ar; if (h > 600) { h = 600; w = h * S.ar; }\n    const cx = 1410, cy = 560;",
    "    let w = 800, h = w / S.ar; if (h > 540) { h = 540; w = h * S.ar; }\n    const cx = 1410, cy = 560;")

# เส้นโครงร่างทับภาพ
rep("  if (S.k === 'full') P.innerHTML = `<img class=\"ph\" id=\"ph\" src=\"img/${pick(S)}\" style=\"filter:${GRADE[S.g]}\">`;",
    "  if (S.k === 'full') P.innerHTML = `<img class=\"ph\" id=\"ph\" src=\"img/${pick(S)}\" style=\"filter:${GRADE[S.g]}\">` + (S.pose ? poseSvg(S) : '');")
rep('function buildText(T, seed) {', POSE_JS + '\nfunction buildText(T, seed) {')
rep('    ph.style.transform = `translate(${x}%, ${y}%) scale(${sc.toFixed(4)})`;\n  }', '    ph.style.transform = `translate(${x}%, ${y}%) scale(${sc.toFixed(4)})`;' + ANIM)

# บรรทัดเครดิตมีภาษาไทย ฟอนต์ Archivo ไม่มีตัวไทย ให้ Kanit รับช่วง
rep('  .end .cred { font-family:Archivo;', '  .end .cred { font-family:Archivo, Kanit;')
# การ์ดท้าย: เครดิตเพลงของคลิปนี้
rep("(window.CREDIT || BRAND.credit)",
    "(window.CREDIT || BRAND.credit + ' &nbsp;·&nbsp; เสียงบรรยายและภาพประกอบบางส่วนสร้างด้วย AI')")
rep("concat(FOUR.map(c => c.img), ['s04_6.jpg', 's04_11.jpg', 's01_4.png', 'warehouse.png', 'cert-logo.png'])",
    "concat(['s01_4.png', 'warehouse.png'])")

io.open(P + 'intro.html', 'w', encoding='utf-8', newline='\n').write(s)
print('intro.html ok · TOTAL', TOTAL, '· shots', len(SHOTS), '· cards', len(CARDS))
