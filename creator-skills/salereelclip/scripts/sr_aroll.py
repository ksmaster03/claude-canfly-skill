# -*- coding: utf-8 -*-
# เตรียมฟุตเทจคนพูด (A-roll) สำหรับ /salereelclip
#   1) ตัดช่วงเงียบให้เหลือช่องหายใจสั้น ๆ (คลิปต้นแบบเงียบแค่ 6% ช่องยาว 90-240 ms)
#   2) ปรับเป็น 1080x1920 30fps แล้วแตกเฟรมเป็น JPG ให้ engine.html ใช้เป็นฉากหลัง
#   3) ถอดเสียงด้วย faster-whisper แล้วเขียน <proj>/asr.json รูปแบบเดียวกับ align.py ของ /explainreel (align จะไม่ถอดซ้ำ)
# ใช้: python sr_aroll.py <video> <proj> [--gap 0.18] [--keep 0.09] [--no-asr]
#      python sr_aroll.py --cut <proj> <t0> <t1>     ตัดพื้นหลังเฟรมช่วงเวลา t0-t1 (วินาทีของคลิปที่ตัดแล้ว) ด้วย rembg ใช้ในฉาก offer
# ผล: <proj>/aroll/tight.mp4  <proj>/aroll/voice.wav  <proj>/aroll/frames/f_00001.jpg ...  <proj>/aroll/aroll.json
import io
import json
import os
import subprocess
import sys

import numpy as np
import soundfile as sf

sys.stdout.reconfigure(encoding="utf-8")
FPS, SR = 30, 48000
run = lambda a: subprocess.run(["ffmpeg", "-y", "-hide_banner", "-loglevel", "error"] + a, check=True)


def opt(name, default):
    if name in sys.argv:
        return float(sys.argv[sys.argv.index(name) + 1])
    return default


if sys.argv[1] == "--cut":
    d, t0, t1 = os.path.abspath(sys.argv[2]), float(sys.argv[3]), float(sys.argv[4])
    from PIL import Image
    from rembg import new_session, remove   # ครั้งแรกจะดาวน์โหลดโมเดล isnet-general-use ราว 170 MB ไป ~/.u2net
    meta = json.load(io.open(f"{d}/aroll/aroll.json", encoding="utf-8"))
    f0, f1 = max(1, int(t0 * FPS) + 1), min(meta["count"], int(t1 * FPS) + 1)
    os.makedirs(f"{d}/aroll/cut", exist_ok=True)
    s = new_session("isnet-general-use")
    for i in range(f0, f1 + 1):
        im = Image.open(f"{d}/aroll/frames/f_{i:05d}.jpg")
        remove(im, session=s).save(f"{d}/aroll/cut/f_{i:05d}.png")
    meta["cut"] = {"dir": "aroll/cut", "from": f0, "to": f1}
    io.open(f"{d}/aroll/aroll.json", "w", encoding="utf-8").write(json.dumps(meta, ensure_ascii=False))
    print(f"cut frames {f0}-{f1} -> aroll/cut  · ใส่ \"cut\": {json.dumps(meta['cut'])} ใน bg ของ clip.json")
    sys.exit(0)

src, d = os.path.abspath(sys.argv[1]), os.path.abspath(sys.argv[2])
GAP, KEEP = opt("--gap", 0.18), opt("--keep", 0.09)
A = f"{d}/aroll"
os.makedirs(f"{A}/frames", exist_ok=True)

# หาช่วงพูดจากพลังงานเสียง (หน้าต่าง 20 ms) เกณฑ์อิงระดับเสียงพูดของไฟล์เอง
run(["-i", src, "-vn", "-ac", "1", "-ar", str(SR), f"{A}/_raw.wav"])
x, _ = sf.read(f"{A}/_raw.wav")
hop = int(0.01 * SR)
env = np.array([np.sqrt(np.mean(x[i:i + 2 * hop] ** 2)) + 1e-9 for i in range(0, len(x) - 2 * hop, hop)])
db = 20 * np.log10(env)
speech_lvl = np.percentile(db, 90)
thr = max(speech_lvl - 30, np.percentile(db, 10) + 6)
on = db > thr
# เติมรูเล็ก ๆ ในคำ (< 60 ms) กันตัดกลางพยางค์
i = 0
while i < len(on):
    if not on[i]:
        j = i
        while j < len(on) and not on[j]:
            j += 1
        if 0 < i and j < len(on) and (j - i) * 0.01 < 0.06:
            on[i:j] = True
        i = j
    else:
        i += 1
# ช่วงที่เก็บ: ช่วงพูด + ช่องเงียบที่สั้นกว่า GAP เก็บทั้งหมด ช่องที่ยาวกว่าเหลือ KEEP (ครึ่งหน้าครึ่งหลัง)
segs, i, n = [], 0, len(on)
while i < n:
    if on[i]:
        j = i
        while j < n and on[j]:
            j += 1
        segs.append([i * 0.01, j * 0.01])
        i = j
    else:
        i += 1
if not segs:
    sys.exit("ไม่พบเสียงพูดในไฟล์")
keep = []
pad = KEEP / 2
for k, (a, b) in enumerate(segs):
    a2 = a - (pad if k == 0 else 0)
    if keep and a - keep[-1][1] <= GAP:
        keep[-1][1] = b
    else:
        if keep:
            keep[-1][1] += pad
            a2 = a - pad
        keep.append([max(0.0, a2), b])
keep[-1][1] = min(len(x) / SR, keep[-1][1] + 0.25)
src_dur = len(x) / SR
new_dur = sum(b - a for a, b in keep)
print(f"source {src_dur:.2f}s -> {new_dur:.2f}s · {len(keep)} ช่วง · ตัดเงียบออก {src_dur - new_dur:.2f}s · เกณฑ์ {thr:.1f} dB")

# ตัดและต่อทั้งภาพและเสียงในคำสั่งเดียว แล้วจัดเป็น 1080x1920 30fps (cover)
fc, cat = [], ""
for k, (a, b) in enumerate(keep):
    fc.append(f"[0:v]trim={a:.3f}:{b:.3f},setpts=PTS-STARTPTS[v{k}];[0:a]atrim={a:.3f}:{b:.3f},asetpts=PTS-STARTPTS[a{k}]")
    cat += f"[v{k}][a{k}]"
fc.append(f"{cat}concat=n={len(keep)}:v=1:a=1[cv][ca]")
fc.append("[cv]fps=30,scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,setsar=1[vo]")
script = f"{A}/_cut.txt"
io.open(script, "w", encoding="utf-8").write(";\n".join(fc))
run(["-i", src, "-filter_complex_script", script, "-map", "[vo]", "-map", "[ca]", "-c:v", "libx264", "-preset", "medium", "-crf", "16",
     "-pix_fmt", "yuv420p", "-c:a", "pcm_s16le", "-ar", str(SR), f"{A}/tight.mov"])
run(["-i", f"{A}/tight.mov", "-c:v", "copy", "-c:a", "aac", "-b:a", "256k", f"{A}/tight.mp4"])
run(["-i", f"{A}/tight.mov", "-vn", "-ac", "1", "-ar", str(SR), f"{A}/voice.wav"])
run(["-i", f"{A}/tight.mov", "-q:v", "3", f"{A}/frames/f_%05d.jpg"])
os.remove(f"{A}/tight.mov")
os.remove(f"{A}/_raw.wav")
count = len([f for f in os.listdir(f"{A}/frames") if f.endswith(".jpg")])
meta = {"count": count, "fps": FPS, "dur": round(new_dur, 3), "keep": [[round(a, 3), round(b, 3)] for a, b in keep]}
io.open(f"{A}/aroll.json", "w", encoding="utf-8").write(json.dumps(meta, ensure_ascii=False))
print(f"frames {count} · ใส่ใน clip.json:  \"head\": 0, \"tail\": 0.3, \"bg\": {{\"type\": \"aroll\", \"dir\": \"aroll/frames\", \"fps\": 30, \"count\": {count}}}")

if "--no-asr" not in sys.argv:
    from faster_whisper import WhisperModel
    m = WhisperModel("mobiuslabsgmbh/faster-whisper-large-v3-turbo", device="cpu", compute_type="int8")
    segs, _ = m.transcribe(f"{A}/voice.wav", language="th", word_timestamps=True, vad_filter=False)
    asr = [{"s": round(s.start, 2), "e": round(s.end, 2), "t": s.text.strip(),
            "w": [[round(w.start, 2), round(w.end, 2), w.word] for w in (s.words or [])]} for s in segs]
    io.open(f"{d}/asr.json", "w", encoding="utf-8").write(json.dumps(asr, ensure_ascii=False))
    with io.open(f"{A}/transcript.txt", "w", encoding="utf-8") as f:
        for s in asr:
            f.write(f"[{s['s']:6.2f} -> {s['e']:6.2f}] {s['t']}\n")
    print("asr ->", f"{d}/asr.json", "· บทที่ถอดได้อยู่ที่ aroll/transcript.txt ใช้เขียน say ใน clip.json ให้ตรงคำพูดจริง")
