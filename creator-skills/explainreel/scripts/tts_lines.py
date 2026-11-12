# เจนเสียงอ่านบททีละประโยคด้วย edge-tts แล้วต่อเป็นไฟล์เดียวพร้อมไทม์ไลน์ (รันด้วย python ตัวหลัก)
# ใช้: python tts_lines.py <course_dir>
# อ่าน <course_dir>/clip.json (lines[].say หรือ lines[].tts) ออก <course_dir>/narr_src.wav + <course_dir>/timeline.json
import asyncio
import io
import json
import os
import subprocess
import sys

import edge_tts
import numpy as np
import soundfile as sf

VOICE, RATE = "th-TH-NiwatNeural", "-6%"
SR = 44100
GAP = 0.32        # ช่องว่างระหว่างประโยค ต้องยาวพอให้ voice_kosin.sh หาจุดตัดท่อนได้
LONG_GAP = 0.55   # ก่อนฉาก num / cta / stamp
HEAD, TAIL = 0.3, 1.2

d = sys.argv[1]
clip = json.load(io.open(f"{d}/clip.json", encoding="utf-8"))
os.makedirs(f"{d}/tts", exist_ok=True)


async def gen():
    for l in clip["lines"]:
        mp3 = f"{d}/tts/{l['id']:02d}.mp3"
        if not os.path.exists(mp3):
            await edge_tts.Communicate(l.get("tts") or l["say"].replace("|", " ").replace("*", ""), VOICE, rate=RATE).save(mp3)


asyncio.run(gen())

parts, timeline, t = [np.zeros(int(HEAD * SR))], [], HEAD
for i, l in enumerate(clip["lines"]):
    wav = f"{d}/tts/{l['id']:02d}.wav"
    subprocess.run(
        ["ffmpeg", "-y", "-loglevel", "error", "-i", f"{d}/tts/{l['id']:02d}.mp3",
         "-af", "silenceremove=start_periods=1:start_threshold=-45dB:start_silence=0.02,areverse,"
                "silenceremove=start_periods=1:start_threshold=-45dB:start_silence=0.05,areverse",
         "-ar", str(SR), "-ac", "1", wav], check=True)
    a, _ = sf.read(wav)
    if i:
        g = LONG_GAP if l["scene"]["type"] in ("num", "cta", "warn") else GAP
        parts.append(np.zeros(int(g * SR))); t += g
    timeline.append({"id": l["id"], "sub": l.get("sub", ""), "scene": l["scene"], "start": round(t, 3), "end": round(t + len(a) / SR, 3)})
    parts.append(a); t += len(a) / SR
parts.append(np.zeros(int(TAIL * SR)))
sf.write(f"{d}/narr_src.wav", np.concatenate(parts), SR)
json.dump({"lines": timeline, "total": round(t + TAIL, 3), "meta": clip.get("meta", {})},
          io.open(f"{d}/timeline.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print(f"{d}: {len(timeline)} lines total={t + TAIL:.1f}s")
