# -*- coding: utf-8 -*-
# Kosin 17/10/2026 แทนช่วงย่อหน้าในเสียงพากย์ด้วยเสียงที่สร้างใหม่ ตัดตรงช่องเงียบที่ใกล้ขอบที่สุด ปรับความดังให้เท่ากัน
# ใช้: python splice.py <src> <fix> <t_start> <t_end> <out.wav>   (t = เวลาโดยประมาณของต้นย่อหน้าแรกที่แทน และต้นย่อหน้าถัดไปที่เก็บไว้)
import re, subprocess, sys
src, fix, ta, tb, out = sys.argv[1], sys.argv[2], float(sys.argv[3]), float(sys.argv[4]), sys.argv[5]
run = lambda a: subprocess.run(["ffmpeg", "-hide_banner", "-y"] + a, capture_output=True, text=True, encoding="utf-8", errors="replace")
r = run(["-i", src, "-af", "silencedetect=noise=-38dB:d=0.1", "-f", "null", "-"])
sil = list(zip(map(float, re.findall(r"silence_start: ([\d.]+)", r.stderr)), map(float, re.findall(r"silence_end: ([\d.]+)", r.stderr))))
near = lambda t: min(((a + b) / 2 for a, b in sil if abs((a + b) / 2 - t) < 1.5), key=lambda m: abs(m - t), default=t)
a, b = near(ta), near(tb)
lufs = lambda p, ss=None, t=None: float(re.findall(r"I:\s+(-?[\d.]+) LUFS", run((["-ss", str(ss), "-t", str(t)] if ss is not None else []) + ["-i", p, "-af", "ebur128", "-f", "null", "-"]).stderr)[-1])
g = lufs(src, a, b - a) - lufs(fix)
run(["-t", str(a), "-i", src, "-ar", "24000", "-ac", "1", "_p1.wav"])
run(["-i", fix, "-af", "silenceremove=start_periods=1:start_threshold=-45dB,areverse,silenceremove=start_periods=1:start_threshold=-45dB,areverse,"
     f"volume={g:.2f}dB,adelay=200,apad=pad_dur=0.25", "-ar", "24000", "-ac", "1", "_p2.wav"])
run(["-ss", str(b), "-i", src, "-ar", "24000", "-ac", "1", "_p3.wav"])
open("_parts.txt", "w").write("file '_p1.wav'\nfile '_p2.wav'\nfile '_p3.wav'\n")
r = run(["-f", "concat", "-safe", "0", "-i", "_parts.txt", "-c:a", "pcm_s16le", out])
print(f"cut {a:.2f}-{b:.2f} gain {g:+.2f} dB", "ok" if r.returncode == 0 else r.stderr[-300:])
