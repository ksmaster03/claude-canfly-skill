# -*- coding: utf-8 -*-
# จับเวลาซับทีละวลีกับเสียงพากย์จริง แล้วสร้าง timeline.json ให้ตัวเรนเดอร์
# ใช้: python align.py <project_dir> <voice_audio>
# อ่าน <project_dir>/clip.json:
#   { "head": 0.4, "tail": 1.4,
#     "show": [["คล็อดโค้ด", "Claude Code"], ...],      คำอ่าน -> คำที่ขึ้นจอ (เรียงคำยาวก่อนคำสั้น)
#     "lines": [ { "id": 1, "scene": {...}, "say": "วลีหนึ่ง|*วลีสำคัญ*|วลีสาม" }, ... ] }
# "say" ต้องเป็นคำอ่านแบบเดียวกับที่เสียงพูดจริง คั่นวลีด้วย | ครอบวลีสำคัญด้วย *...*
# ผลถอดเสียงเก็บที่ <project_dir>/asr.json ลบทิ้งเมื่อเปลี่ยนไฟล์เสียง
import difflib
import io
import json
import os
import re
import subprocess
import sys

d, audio = sys.argv[1], sys.argv[2]
clip = json.load(io.open(f"{d}/clip.json", encoding="utf-8"))
HEAD, TAIL = clip.get("head", 0.4), clip.get("tail", 1.4)
dur = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", audio],
                           capture_output=True, text=True).stdout.strip())

if not os.path.exists(f"{d}/asr.json"):
    from faster_whisper import WhisperModel
    m = WhisperModel("mobiuslabsgmbh/faster-whisper-large-v3-turbo", device="cpu", compute_type="int8")
    segs, _ = m.transcribe(audio, language="th", word_timestamps=True, vad_filter=False)
    asr = [{"s": round(s.start, 2), "e": round(s.end, 2), "t": s.text.strip(),
            "w": [[round(w.start, 2), round(w.end, 2), w.word] for w in (s.words or [])]} for s in segs]
    io.open(f"{d}/asr.json", "w", encoding="utf-8").write(json.dumps(asr, ensure_ascii=False))
asr = json.load(io.open(f"{d}/asr.json", encoding="utf-8"))


def show(s):
    for a, b in clip.get("show", []):
        s = s.replace(a, f" {b} ")
    return re.sub(r"\s+", " ", s).strip()


keep = lambda s: re.sub(r"[^ก-ฮะาำเ-ไ]", "", s)  # พยัญชนะกับสระที่ยืนบรรทัด
hyp, times = [], []
for seg in asr:
    if seg["s"] >= dur - 0.45:   # เศษท้ายไฟล์ที่ตัวถอดเสียงมักแต่งขึ้นเอง
        continue
    for a, b, w in seg["w"]:
        k = keep(w)
        for i, ch in enumerate(k):
            hyp.append(ch); times.append(a + (b - a) * i / max(1, len(k)))
hyp = "".join(hyp)

ref, starts, meta = "", [], []
for l in clip["lines"]:
    for p in l["say"].split("|"):
        starts.append(len(ref)); meta.append((l["id"], p)); ref += keep(p)
sm = difflib.SequenceMatcher(None, ref, hyp, autojunk=False)
r2h = {a + i: b + i for a, b, n in sm.get_matching_blocks() for i in range(n)}
print("ref", len(ref), "hyp", len(hyp), "matched", len(r2h), "ratio", round(sm.ratio(), 3))
if sm.ratio() < 0.8:
    print("WARN: บทกับเสียงตรงกันต่ำกว่า 80% ตรวจว่า say ตรงกับที่พูดจริง หรือเสียงขาดบางท่อน")


def t_at(i):
    for j in range(i, min(i + 10, len(ref))):
        if j in r2h:
            return max(0.0, times[r2h[j]] - 0.07 * (j - i))
    for j in range(i - 1, max(i - 10, -1), -1):
        if j in r2h:
            return times[r2h[j]] + 0.07 * (i - j)
    return None


ts = [t_at(s) for s in starts]
miss = [m for m, t in zip(meta, ts) if t is None]
for i, t in enumerate(ts):   # จุดที่จับไม่ได้ ใช้กึ่งกลางระหว่างเพื่อนบ้าน
    if t is None:
        a = ts[i - 1] if i else 0.0
        b = next((x for x in ts[i + 1:] if x is not None), a + 2.0)
        ts[i] = a + (b - a) * 0.5
pushed = 0
for i in range(1, len(ts)):  # เวลาต้องเดินหน้าเสมอ
    if ts[i] < ts[i - 1] + 0.25:
        ts[i] = ts[i - 1] + 0.25; pushed += 1
print("phrases", len(ts), "unmatched", len(miss), miss[:5], "pushed", pushed)

lines = []
for k, l in enumerate(clip["lines"]):
    subs = [{"t": round(t + HEAD - 0.08, 2), "text": show(p.replace("*", "")), "em": p.startswith("*")}
            for (sid, p), t in zip(meta, ts) if sid == l["id"]]
    lines.append({"id": l["id"], "start": 0.3 if k == 0 else round(subs[0]["t"] - 0.05, 2), "scene": l["scene"], "subs": subs,
                  "sub": "|".join(x["text"] for x in subs)})
vend = round(dur - 0.35 + HEAD, 2)
for a, b in zip(lines, lines[1:] + [None]):
    a["end"] = b["start"] if b else vend
total = round(vend + TAIL, 2)
io.open(f"{d}/timeline.json", "w", encoding="utf-8", newline="\n").write(json.dumps({"total": total, "head": HEAD, "lines": lines}, ensure_ascii=False))
for l in lines:
    flag = "  <-- ฉากค้างนานเกิน 15 วิ ควรแตกฉาก" if l["end"] - l["start"] > 15 else ""
    print(l["id"], l["start"], "dur %.1f" % (l["end"] - l["start"]), len(l["subs"]), "|", l["subs"][0]["text"], flag)
print("total", total)
