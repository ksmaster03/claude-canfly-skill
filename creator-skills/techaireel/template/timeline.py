# -*- coding: utf-8 -*-
"""จับคู่ประโยคพากย์กับช่วงภาพที่อัดมา แล้วคำนวณไทม์ไลน์ปลายทาง

หลักการ: ช่วงที่ภาพนิ่งยืดได้ไม่จำกัด ช่วงที่ภาพขยับ (คลิก พิมพ์) ให้ใกล้ความเร็วเดิม
ค่าเวลาของวิดีโอหักสเลทออกแล้ว (videoTime = eventT - SLATE_OFFSET)
"""
import io, json, os

ROOT = r"__ROOT__"
SLATE_OFFSET = 0.41          # วัดจากเฟรมแดงที่ 4.04 เทียบ event slate ที่ 4.45
GAP = 0.42                   # ช่องหายใจระหว่างประโยค
FPS = 30

# กลุ่มประโยค -> ช่วงเวลาในวิดีโอต้นฉบับ (หน่วยวินาที หลังหักสเลทแล้ว)
GROUPS = [
    ([1, 2, 3],  16.43, 20.08),   # hook บนการ์ด Daily briefing ที่เขียนว่า Weekdays at 8:00 AM ตรงกับที่พูด
    ([4],         6.50,  9.03),   # ชี้เมนูซ้าย
    ([5],         9.03, 12.27),   # กด Scheduled
    ([6],        12.27, 14.91),   # หน้าว่าง
    ([7],        14.91, 16.43),   # เทมเพลตทั้งหมด
    ([8, 9],     16.43, 20.08),   # Daily briefing
    ([10, 11],   20.08, 23.51),   # Inbox triage
    ([12],       23.51, 26.15),   # Meeting prep
    ([13],       26.15, 27.50),   # Weekly review
    ([14],       27.50, 28.77),
    ([15],       28.77, 30.75),   # กด New task
    ([16],       30.75, 31.50),
    ([17],       31.50, 33.78),   # Create with Claude
    ([18],       33.78, 36.61),   # Set up manually
    ([19],       36.61, 40.81),   # พิมพ์ชื่องาน
    ([20],       40.81, 41.78),
    ([21],       41.78, 46.10),   # พิมพ์คำสั่ง
    ([22],       46.10, 50.25),   # โปรเจกต์กับโมเดล
    ([23],       50.25, 52.08),   # Frequency
    ([24, 25],   52.08, 54.02),   # เมนูความถี่
    ([26],       50.25, 52.08),   # Permissions ใช้ภาพก่อนเมนูความถี่เปิด ไม่งั้นเมนูบังช่องที่พูดถึง
    ([27],       56.98, 58.50),   # ปุ่ม Save
    ([28],       14.91, 16.43),   # ย้อนใช้ภาพรายการที่มีเวลากำกับ
]
# ช่วงที่ยืมภาพซ้ำจากที่อื่น ห้ามรับ mark จากตอนอัด ไม่งั้นกรอบไฮไลต์ไปโผล่ผิดช่วง
REUSED = {(1, 2, 3), (26,), (28,)}
CARD_LINES = [29, 30, 31, 32, 33, 34, 35]   # ช่วงยกตัวอย่างการใช้งาน ใช้การ์ดกราฟิกแทนภาพจอ
CTA_LINES = [36]                             # ปิดท้ายชวนกดติดตาม
CTA_CLICK_OFFSET = 2.12   # คำว่า "ติดตาม" เริ่มที่ 2.12 วิ ในประโยค 36 วัดด้วย whisper ใช้กดปุ่มในฉากปิด

data = json.load(io.open(os.path.join(ROOT, "script/script.json"), encoding="utf-8"))
by_id = {ln["id"]: ln for ln in data["lines"]}

segments, cues = [], []
t_out = 0.0

def place(ids, dur_total):
    """วางประโยคลงไทม์ไลน์ปลายทาง คืนเวลาเริ่มจบของทั้งกลุ่ม"""
    global t_out
    start = t_out
    for i, lid in enumerate(ids):
        ln = by_id[lid]
        cues.append({
            "id": lid, "text": ln["text"], "beat": ln["beat"],
            "audio": ln["audio"],
            "start": round(t_out, 3), "end": round(t_out + ln["dur"], 3),
        })
        t_out += ln["dur"]
        if i < len(ids) - 1:
            t_out += GAP
    return start, t_out

for ids, v_from, v_to in GROUPS:
    need = sum(by_id[i]["dur"] for i in ids) + GAP * (len(ids) - 1)
    start, end = place(ids, need)
    have = v_to - v_from
    span = need + GAP          # ภาพต้องคลุมช่องหายใจท้ายกลุ่มด้วย ไม่งั้นภาพจะสั้นกว่าเสียง
    segments.append({
        "vFrom": round(v_from, 3), "vTo": round(v_to, 3),
        "outStart": round(start, 3), "outDur": round(span, 3),
        "speed": round(have / span, 4), "lines": ids,
        "events": tuple(ids) not in REUSED,
    })
    t_out += GAP     # ช่องว่างท้ายกลุ่ม

cards_start = t_out
place(CARD_LINES, 0)
cards_end = t_out
t_out += GAP + 0.5            # เว้นจังหวะก่อนเปลี่ยนเข้าฉากปิด
cta_start = t_out
place(CTA_LINES, 0)

out = {
    "fps": FPS,
    "slateOffset": SLATE_OFFSET,
    "gap": GAP,
    "totalDur": round(t_out, 3),
    "outro": 2.6,
    "screenDur": round(cards_start, 3),
    "cardsStart": round(cards_start, 3),
    "cardsEnd": round(cards_end, 3),
    "ctaStart": round(cta_start, 3),
    "ctaClick": round(cta_start + CTA_CLICK_OFFSET, 3),
    "segments": segments,
    "cues": cues,
    "meta": {k: data[k] for k in ("title", "topbar", "headline", "subhead", "bottom")},
}
io.open(os.path.join(ROOT, "script/timeline.json"), "w", encoding="utf-8").write(
    json.dumps(out, ensure_ascii=False, indent=2))

print("ช่วงภาพหน้าจอ  %.2f วินาที  (%d segment)" % (cards_start, len(segments)))
print("ช่วงการ์ดตัวอย่าง %.2f วินาที" % (cards_end - cards_start))
print("รวมทั้งคลิป    %.2f วินาที  (%d:%02d)" % (t_out, int(t_out // 60), int(t_out % 60)))
print("\nsegment ที่ต้องยืดเกิน 2.5 เท่า (ภาพต้องนิ่งจริงถึงจะรอด):")
for s in segments:
    if s["speed"] < 0.4:
        print("  บรรทัด %-8s ยืด %.1f เท่า  ภาพ %.2f-%.2f" % (
            str(s["lines"]), 1 / s["speed"], s["vFrom"], s["vTo"]))
