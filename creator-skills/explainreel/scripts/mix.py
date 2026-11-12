# -*- coding: utf-8 -*-
# รวมเสียงพากย์ + เพลงประกอบ (ไม่ใส่ก็ได้) + เสียงป๊อปตอนเปลี่ยนฉากสำคัญ -> <project_dir>/master.wav ที่ราว -14 LUFS
# ใช้: python mix.py <project_dir> <voice_audio> [under_db] [music1 music2 ...]
#   under_db   เพลงเบากว่าเสียงพากย์กี่ dB ดีฟอลต์ 12 (ผู้ใช้เคยบอกว่า 17 และ 27 ไม่ได้ยินเพลงเลย อย่าตั้งเกิน 16)
#   เพลงหลายไฟล์จะถูกตัดเงียบหัวท้ายแล้วต่อกันด้วยครอสเฟด 4 วินาที ถ้ายังสั้นกว่าคลิปจะหยุดพร้อมข้อความ
import io
import json
import subprocess
import sys

import numpy as np
import soundfile as sf

d, voice = sys.argv[1], sys.argv[2]
UNDER = float(sys.argv[3]) if len(sys.argv) > 3 else 12.0
MUSIC = sys.argv[4:]
SR, XF = 48000, 4.0
tl = json.load(io.open(f"{d}/timeline.json", encoding="utf-8"))
total, HEAD = tl["total"], tl.get("head", 0.4)
N = int(total * SR)
run = lambda a: subprocess.run(["ffmpeg", "-y", "-loglevel", "error"] + a, check=True)
rms = lambda x: float(np.sqrt(np.mean(x ** 2)) + 1e-12)

run(["-i", voice, "-ar", str(SR), "-ac", "1", f"{d}/_voice.wav"])
vo, _ = sf.read(f"{d}/_voice.wav")
vo = np.concatenate([np.zeros(int(HEAD * SR)), vo])
vo = np.pad(vo, (0, max(0, N - len(vo))))[:N]
vo_rms = rms(vo[np.abs(vo) > 0.01])

mus = np.zeros((N, 2))
if MUSIC:
    trim = "silenceremove=start_periods=1:start_threshold=-45dB,areverse,silenceremove=start_periods=1:start_threshold=-45dB,areverse"
    ins = sum([["-i", m] for m in MUSIC], [])
    fc = ";".join(f"[{i}:a]{trim}[m{i}]" for i in range(len(MUSIC)))
    cur = "[m0]"
    for i in range(1, len(MUSIC)):
        fc += f";{cur}[m{i}]acrossfade=d={XF}:c1=tri:c2=tri[x{i}]"; cur = f"[x{i}]"
    run(ins + ["-filter_complex", fc, "-map", cur, "-ar", str(SR), "-ac", "2", f"{d}/_music.wav"])
    m, _ = sf.read(f"{d}/_music.wav", always_2d=True)
    print("music %.1fs need %.1fs" % (len(m) / SR, total))
    if len(m) < N:
        sys.exit("เพลงสั้นกว่าคลิป ให้ใส่เพลงเพิ่มอีกไฟล์ หรือใส่ไฟล์เดิมซ้ำเพื่อวน")
    mus = m[:N] * (vo_rms / rms(m[:N]) * 10 ** (-UNDER / 20))
    t = np.arange(N) / SR
    mus *= (np.clip(t / 0.6, 0, 1) * np.clip((total - t) / 2.0, 0, 1))[:, None]


def pop_sfx(kind):
    n = int((0.5 if kind == "boom" else 0.22) * SR)
    x = np.arange(n) / SR
    if kind == "boom":
        return np.sin(2 * np.pi * 58 * x * (1 + 0.5 * np.exp(-x * 16))) * np.exp(-x * 7) * 0.30
    return np.sin(2 * np.pi * (520 + 900 * np.exp(-x * 30)) * x) * np.exp(-x * 26) * 0.16


fx = np.zeros(N)
KINDS = {"num": "hit", "stamp": "hit", "warn": "boom", "cmds": "hit", "term": "hit", "cta": "hit", "formula": "hit"}
for l in tl["lines"][1:]:
    k = KINDS.get(l["scene"]["type"])
    if k:
        s = pop_sfx(k)
        i = int(l["start"] * SR)
        fx[i:i + len(s)] += s[: max(0, N - i)]

sf.write(f"{d}/_mix_raw.wav", mus + (vo + fx)[:, None], SR)
# วัดความดังของไฟล์สเตอริโอจริง แล้วปรับให้ได้ -14 LUFS (เสียงโมโนที่กลายเป็นสเตอริโอดังขึ้นราว 3 dB จึงต้องวัดหลังรวม)
out = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-i", f"{d}/_mix_raw.wav", "-af", "ebur128", "-f", "null", "-"],
                     capture_output=True, text=True).stderr
I = float([x for x in out.splitlines() if x.strip().startswith("I:")][-1].split()[1])
run(["-i", f"{d}/_mix_raw.wav", "-af", f"volume={-14.0 - I:.1f}dB,alimiter=limit=-1.5dB:level=false", "-ar", str(SR), "-ac", "2", f"{d}/master.wav"])
print("total=%.1fs raw %.1f LUFS -> -14 · music %s" % (total, I, ("%.0f dB under voice" % UNDER) if MUSIC else "none"))
