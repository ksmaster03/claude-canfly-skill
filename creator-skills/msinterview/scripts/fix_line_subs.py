# -*- coding: utf-8 -*-
# fix_line_subs.py <proj> <line_id> [<audio_proj>] : แก้เวลาซับของบรรทัดที่ align จับไม่ได้ (unmatched)
#   หาจุดเริ่มและความยาวจริงของบรรทัดจากไฟล์ vo/norm/*.wav (เร่งความเร็วแล้ว) + ช่วงเงียบแบบเดียวกับ concat_vo.py
#   แล้วแบ่งเวลาให้แต่ละวลีตามความยาวตัวอักษร เขียนทับ timeline.json (ใช้ได้ทั้งโฟลเดอร์ที่มีฉากเปิด เพราะอิง head)
# สร้าง 21 ต.ค. 2569 (Lost บรรทัด 10 unmatched 4)
import glob, io, json, os, sys
import soundfile as sf
d, lid = sys.argv[1], int(sys.argv[2])
ad = sys.argv[3] if len(sys.argv) > 3 else d
files = sorted(glob.glob(f"{ad}/vo/norm/[0-9][0-9]_*.wav"))
t, prev, spans = 0.0, None, {}
for f in files:
    b = os.path.basename(f)[:-4]; who = b.split("_", 1)[1]; n = int(b.split("_")[0])
    if prev is not None: t += 0.4 if who != prev else 0.25
    info = sf.info(f); spans[n] = (t, info.frames / info.samplerate); t += info.frames / info.samplerate; prev = who
tl = json.load(io.open(f"{d}/timeline.json", encoding="utf-8"))
line = next(l for l in tl["lines"] if l["id"] == lid)
st, ln = spans[lid]; base = tl["head"] + st
w = [max(1, len(s["text"])) for s in line["subs"]]; tot = sum(w); acc = 0
for s, k in zip(line["subs"], w):
    s["t"] = round(base + ln * acc / tot - 0.08, 2); acc += k
line["start"] = round(line["subs"][0]["t"] - 0.05, 2)
for a, b in zip(tl["lines"], tl["lines"][1:]): a["end"] = b["start"]
io.open(f"{d}/timeline.json", "w", encoding="utf-8", newline="\n").write(json.dumps(tl, ensure_ascii=False))
print(f"line {lid}: start {base:.2f}s len {ln:.2f}s · {len(w)} วลี", [s["t"] for s in line["subs"]])
