# -*- coding: utf-8 -*-
# รวมเสียงของ /salereelclip -> <proj>/master.wav (-14 LUFS, true peak -1.5 dBTP, โมโนในสเตอริโอ)
# ค่าตั้งต้นตามคลิปต้นแบบที่วัดมา: ไม่มีเพลง · เสียงพูดบีบแน่น (LRA 1.0) · SFX แค่ 3 ก้อน เป็นเสียงทุ้มต่ำ ไม่ใช่เสียงป๊อป
# ใช้: python sr_mix.py <proj> <voice_audio> [--bgm f1.mp3 [f2.mp3 ...]] [--under 15] [--no-sfx] [--mux silent.mp4 out.mp4]
#   voice_audio  ไฟล์เสียงพากย์ หรือ <proj>/aroll/voice.wav ของฟุตเทจคนพูด (head ใน timeline ต้องเป็น 0)
#   --bgm        ใส่เพลงรองพื้น (ต้นแบบไม่มี) เพลงหลายไฟล์ต่อกันด้วยครอสเฟด · --under เบากว่าเสียงพูดกี่ dB (ดีฟอลต์ 15)
# SFX อัตโนมัติ: thump ตอนเปลี่ยนจากฉากเปิดไปฉากที่สอง · boom ตอนคีย์เวิร์ดสีแดงขึ้น · boom ตอนเข้าฉาก offer ครั้งแรก
#   ฉากไหนอยากกำหนดเอง ใส่ "sfx": "thump" | "boom" | "tick" | "none" ใน scene
import io
import json
import subprocess
import sys

import numpy as np
import soundfile as sf

sys.stdout.reconfigure(encoding="utf-8")
d, voice = sys.argv[1], sys.argv[2]
args = sys.argv[3:]


def take(flag, n=None):
    if flag not in args:
        return None
    i = args.index(flag)
    if n == 0:
        return True
    out = []
    for a in args[i + 1:]:
        if a.startswith("--"):
            break
        out.append(a)
    return out


BGM = take("--bgm") or []
UNDER = float((take("--under") or ["15"])[0])
NOSFX = take("--no-sfx", 0)
MUX = take("--mux")
SR = 48000
tl = json.load(io.open(f"{d}/timeline.json", encoding="utf-8"))
total, HEAD = tl["total"], tl.get("head", 0.4)
N = int(total * SR)
run = lambda a: subprocess.run(["ffmpeg", "-y", "-loglevel", "error"] + a, check=True)
rms = lambda x: float(np.sqrt(np.mean(x ** 2)) + 1e-12)

# เสียงพูด: ตัดย่านต่ำ บีบให้แน่น แบบคลิปต้นแบบ (LRA 1.0 LU)
run(["-i", voice, "-af", "highpass=f=80,acompressor=threshold=-24dB:ratio=3.5:attack=4:release=90:makeup=4,alimiter=limit=0.95:level=false",
     "-ar", str(SR), "-ac", "1", f"{d}/_voice.wav"])
vo, _ = sf.read(f"{d}/_voice.wav")
vo = np.concatenate([np.zeros(int(HEAD * SR)), vo])
vo = np.pad(vo, (0, max(0, N - len(vo))))[:N]
vo_rms, vo_pk = rms(vo[np.abs(vo) > 0.01]), float(np.max(np.abs(vo)) + 1e-9)


def sfx(kind):
    if kind == "boom":    # ต้นแบบ 1.25-1.55 วิ พลังงานอยู่ย่าน sub ล้วน
        n = int(1.4 * SR); x = np.arange(n) / SR
        f = 32 + 26 * np.exp(-x * 3.5)
        y = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-x * 2.6)
        return np.tanh(y * 1.6) / np.tanh(1.6) * 10 ** (-15 / 20)
    if kind == "thump":   # ต้นแบบ 0.3 วิ ย่าน sub
        n = int(0.3 * SR); x = np.arange(n) / SR
        y = np.sin(2 * np.pi * (48 + 40 * np.exp(-x * 25)) * x) * np.exp(-x * 14)
        y += np.random.default_rng(1).normal(0, 1, n) * np.exp(-x * 60) * 0.08
        return y * 10 ** (-17 / 20)
    if kind == "tick":    # ไม่มีในต้นแบบ ใช้เมื่อสั่งเอง
        n = int(0.12 * SR); x = np.arange(n) / SR
        return np.sin(2 * np.pi * (900 + 600 * np.exp(-x * 40)) * x) * np.exp(-x * 45) * 10 ** (-24 / 20)
    return None


events = []
if not NOSFX:
    lines, offer_done = tl["lines"], False
    for k, l in enumerate(lines):
        s = l["scene"]
        kind, at = s.get("sfx"), l["start"]
        if kind is None:
            if k == 1:
                kind = "thump"
            if s.get("kwColor") == "red":   # ต้นแบบวาง boom ตอนตัดเข้าฉากเจ็บ (39.55 วิ) ไม่ใช่ตอนคำแดงขึ้น
                kind = "boom"
            if s.get("frame") == "offer" and not offer_done:
                kind, offer_done = "boom", True
        if kind and kind != "none":
            # ก้อนที่ห่างกันไม่ถึง 2.5 วิ ทับกันจนเละ เก็บก้อนแรก (ต้นแบบห่างกัน 4.75 วิ)
            if events and at - events[-1][0] < 2.5 and s.get("sfx") is None:
                continue
            events.append((at, kind))
fx = np.zeros(N)
for at, kind in events:
    y = sfx(kind)
    if y is None:
        continue
    i = int(max(0, at - 0.02) * SR)
    fx[i:i + len(y)] += (y * vo_pk)[: max(0, N - i)]

mus = np.zeros(N)
if BGM:
    trim = "silenceremove=start_periods=1:start_threshold=-45dB,areverse,silenceremove=start_periods=1:start_threshold=-45dB,areverse"
    ins = sum([["-i", m] for m in BGM], [])
    fc = ";".join(f"[{i}:a]{trim}[m{i}]" for i in range(len(BGM)))
    cur = "[m0]"
    for i in range(1, len(BGM)):
        fc += f";{cur}[m{i}]acrossfade=d=4:c1=tri:c2=tri[x{i}]"; cur = f"[x{i}]"
    run(ins + ["-filter_complex", fc + f";{cur}highpass=f=110[o]", "-map", "[o]", "-ar", str(SR), "-ac", "1", f"{d}/_music.wav"])
    m, _ = sf.read(f"{d}/_music.wav")
    if len(m) < N:
        sys.exit("เพลงสั้นกว่าคลิป ใส่ไฟล์เพิ่มหรือใส่ไฟล์เดิมซ้ำ")
    mus = m[:N] * (vo_rms / rms(m[:N]) * 10 ** (-UNDER / 20))
    t = np.arange(N) / SR
    mus *= np.clip(t / 0.6, 0, 1) * np.clip((total - t) / 1.5, 0, 1)

mix = vo + fx + mus
st = np.stack([mix, mix], 1)
sf.write(f"{d}/_mix_raw.wav", st, SR)
out = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-i", f"{d}/_mix_raw.wav", "-af", "ebur128", "-f", "null", "-"],
                     capture_output=True, text=True).stderr
I = float([x for x in out.splitlines() if x.strip().startswith("I:")][-1].split()[1])
run(["-i", f"{d}/_mix_raw.wav", "-af", f"volume={-14.0 - I:.2f}dB,alimiter=limit=-1.5dB:level=false:attack=2:release=40",
     "-ar", str(SR), "-ac", "2", f"{d}/master.wav"])
chk = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-i", f"{d}/master.wav", "-af", "ebur128=peak=true", "-f", "null", "-"],
                     capture_output=True, text=True).stderr.splitlines()
get = lambda key: [x for x in chk if x.strip().startswith(key)][-1].split()[1]
print(f"total {total:.2f}s · SFX {[(round(a, 2), k) for a, k in events]} · BGM {'%.0f dB under' % UNDER if BGM else 'ไม่มี (ตามต้นแบบ)'}")
print(f"master.wav  I {get('I:')} LUFS · LRA {get('LRA:')} LU · true peak {get('Peak:')} dBFS")
if MUX:
    silent, final = MUX[0], MUX[1]
    run(["-i", silent, "-i", f"{d}/master.wav", "-map", "0:v", "-map", "1:a", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k",
         "-shortest", "-movflags", "+faststart", final])
    print("mux ->", final)
