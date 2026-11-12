# -*- coding: utf-8 -*-
# mix_intro.py <proj> <voice> <bgm> [under_db] : รวมเสียงสำหรับคลิปที่มีฉากเปิด (หลัง add_intro.py) ได้สองไฟล์
#   master.wav     YouTube / Facebook: ช่วงเปิดเพลงบรรเลงของเราดังเต็ม (ไม่มีเพลงต้นฉบับ) แล้วลดลงไปอยู่ใต้เสียงพูดก่อนเสียงพูดเริ่ม
#   master_tt.wav  TikTok: ช่วงเปิดเงียบสนิท ให้เพลงต้นฉบับจากคลัง TikTok เล่นตรงนั้น แล้วเพลงบรรเลงของเราค่อยเข้าหลังฉากเปิด
#   เสียงพูดเริ่มที่ head ของ timeline.json เสมอ ไม่มีเพลงใดดังเต็มทับเสียงพูด
import io
import json
import subprocess
import sys

import numpy as np
import soundfile as sf

d, voice, bgm = sys.argv[1], sys.argv[2], sys.argv[3]
UNDER = float(sys.argv[4]) if len(sys.argv) > 4 else 12.0
SR = 48000
tl = json.load(io.open(f"{d}/timeline.json", encoding="utf-8"))
total, HEAD, D = tl["total"], tl["head"], tl.get("intro", 0)
if not D:
    sys.exit("timeline.json ไม่มีฉากเปิด รัน add_intro.py ก่อน")
N = int(total * SR)
run = lambda a: subprocess.run(["ffmpeg", "-y", "-loglevel", "error"] + a, check=True)
rms = lambda x: float(np.sqrt(np.mean(x ** 2)) + 1e-12)

run(["-i", voice, "-ar", str(SR), "-ac", "1", f"{d}/_voice.wav"])
vo, _ = sf.read(f"{d}/_voice.wav")
vo = np.pad(np.concatenate([np.zeros(int(HEAD * SR)), vo]), (0, N))[:N]
vo_rms = rms(vo[np.abs(vo) > 0.01])
trim = "silenceremove=start_periods=1:start_threshold=-45dB"
run(["-i", bgm, "-af", trim, "-ar", str(SR), "-ac", "2", f"{d}/_music.wav"])
m, _ = sf.read(f"{d}/_music.wav", always_2d=True)
if len(m) < N:
    sys.exit("เพลงสั้นกว่าคลิป")
mus = m[:N] * (vo_rms / rms(m[:N]) * 10 ** (-UNDER / 20))
t = np.arange(N) / SR
tail = np.clip((total - t) / 2.0, 0, 1)
BOOST = 10 ** (9 / 20)  # ช่วงเปิดไม่มีเสียงพูด ให้เพลงดังขึ้น 9 dB
v0 = HEAD  # เวลาเสียงพูดเริ่ม
# YT/FB: ดังตั้งแต่ต้น (เฟดเข้า 0.6 วิ) ลดจาก BOOST เหลือ 1 ในช่วง D ถึง v0 (เสียงพูดเริ่มตอนเพลงลดครบแล้ว)
down = np.where(t < D, BOOST, np.where(t < v0, BOOST + (1 - BOOST) * (t - D) / max(v0 - D, 0.05), 1.0))
env_yt = np.clip(t / 0.6, 0, 1) * down * tail
# TikTok: เงียบถึง D แล้วเฟดเข้าจนถึง v0
env_tt = np.clip((t - D) / max(v0 - D, 0.05), 0, 1) * tail


def write(env, out):
    raw = mus * env[:, None] + vo[:, None]
    sf.write(f"{d}/_mix_raw.wav", raw, SR)
    o = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-i", f"{d}/_mix_raw.wav", "-af", "ebur128", "-f", "null", "-"],
                       capture_output=True, text=True).stderr
    I = float([x for x in o.splitlines() if x.strip().startswith("I:")][-1].split()[1])
    run(["-i", f"{d}/_mix_raw.wav", "-af", f"volume={-14.0 - I:.1f}dB,alimiter=limit=-1.5dB:level=false", "-ar", str(SR), "-ac", "2", f"{d}/{out}"])
    return I


a = write(env_yt, "master.wav")
b = write(env_tt, "master_tt.wav")
print(f"total={total:.1f}s intro={D}s voice@{v0:.2f}s · master.wav raw {a:.1f} LUFS · master_tt.wav raw {b:.1f} LUFS -> -14")
