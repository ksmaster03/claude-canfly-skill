# -*- coding: utf-8 -*-
# 20/10/2026 ไทม์ไลน์คลิปเจาะลึกระบบ: วางเสียงพากย์ 8 ย่อหน้า แล้วหาเวลาคำหลักจาก prep/words.json
# ภาพ การ์ด และแผนเสียงอ่านเวลาจากไฟล์นี้ทั้งหมด (make_html.py และ build_mix.py)
import io, json

P = '__PROJECT__/'
DUR = json.load(io.open(P + 'vo/prep/durations.json'))
WORDS = json.load(io.open(P + 'vo/prep/words.json', encoding='utf-8'))

# เวลาเริ่มของแต่ละย่อหน้า: เปิด 1.6 วิ · ชื่อเรื่องต่อท้ายเสียงช่วงเปิด 0.45 วิ ยาว 4 วิ · ช่วงคั่นระหว่างระบบราว 1 วิ
# (21/10/2026 เสียงพากย์เร่งเป็น 1.196 เท่า ชื่อเรื่องจึงขยับตามเสียง ไม่ล็อกที่ 11.8 แล้ว)
GAP = 1.15   # 21/10/2026 จาก 0.95 ให้ช่วงดังเต็มของเพลงตรงชื่อเรื่องหลังตัดเพลง 4 ห้อง
VO = {'v01': 1.6}
TITLE = round(VO['v01'] + DUR['v01'] + 0.08, 2)      # ตรงช่วงดังเต็มต้นเพลง (14.76 ของเพลง) ดู audio/build_mix.py
VO['v02'] = round(VO['v01'] + DUR['v01'] + 4.45, 2)
order = ['v02', 'v03', 'v04', 'v05', 'v06', 'v07', 'v08']
for a, b in zip(order, order[1:]):
    VO[b] = round(VO[a] + DUR[a] + GAP, 2)


def norm(x):
    return x.replace(' ', '').replace('ํา', 'ำ')   # ตัวถอดเสียงบางทีเขียน ำ แยกเป็น ํ + า


def at(v, needle, off=0.0):
    """เวลาในคลิปของคำที่ได้ยิน (ตัวถอดเสียงสะกดบางคำเพี้ยน จึงค้นด้วยคำที่มันได้ยินจริง)"""
    txt, idx = '', []
    for s in WORDS[v]:
        for t, w in s['w']:
            for ch in norm(w):
                txt += ch; idx.append(t)
    i = txt.find(norm(needle))
    if i < 0:
        raise KeyError(f'{v}: {needle}')
    return round(VO[v] + idx[i] + off, 2)


def end(v, pad=0.0):
    return round(VO[v] + DUR[v] + pad, 2)


TOP = at('v08', 'ท็อปเทียร์')        # คำว่า ท็อปเทียร์ ตรงเสียงตูมท่อนจบของเพลง (วินาทีที่ 176 ของเพลง)
MUSIC_AT = round(TOP - 176.0, 2)
END_CARD = round(end('v08') + 0.4, 2)
TOTAL = round(END_CARD + 6.0, 2)
END_FRAME = int(END_CARD * 24) - 8      # เฟรมแรกที่เรนเดอร์การ์ดท้ายแยก (ตามเครดิตเพลงแต่ละฉบับ)

if __name__ == '__main__':
    print('VO', VO)
    print('ชื่อเรื่อง', TITLE, 'ท็อปเทียร์', TOP, 'end card', END_CARD, 'END_FRAME', END_FRAME, 'TOTAL', TOTAL, 'frames', round(TOTAL * 24))
