# -*- coding: utf-8 -*-
# 19/10/2026 ประกอบเสียง intro จากแผน audio_plan.json: ตัดเพลงเป็นท่อนวางตามเวลา + เสียงตูมสังเคราะห์ + SFX แล้วปรับความดังด้วย loudnorm
# ใช้: python build_audio.py audio_plan.json out.wav
import io, json, os, subprocess, sys
import numpy as np
from scipy.io import wavfile
from scipy.signal import butter, sosfilt, fftconvolve

plan = json.load(io.open(sys.argv[1], encoding="utf-8"))
out = sys.argv[2]
SR = plan.get("sr", 48000)
mix = np.zeros((int(plan["total"] * SR), 2), np.float64)


def load(path):
    """อ่านไฟล์เสียงอะไรก็ได้ผ่าน ffmpeg เป็นสเตอริโอ 48k float"""
    path = os.path.expandvars(path)   # รองรับ $MEDIA/sfx/... ในแผนเสียง
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", path, "-f", "f32le", "-ac", "2", "-ar", str(SR), "-"],
                         capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.float32).reshape(-1, 2).astype(np.float64)


def place(buf, at, gain_db=0.0):
    i0 = int(round(at * SR))
    n = min(len(buf), len(mix) - i0)
    if n > 0:
        mix[i0:i0 + n] += buf[:n] * 10 ** (gain_db / 20)


def fades(buf, fi, fo):
    b = buf.copy()
    a, z = int(fi * SR), int(fo * SR)
    if a > 0:
        b[:a] *= np.linspace(0, 1, a)[:, None]
    if z > 0:
        b[-z:] *= np.linspace(1, 0, z)[:, None]
    return b


def boom(dur=4.0, seed=1):
    """เสียงตูมแบบเทรลเลอร์: sub กวาดลง 70->30 Hz + ก้อนลมต่ำ + หางรีเวิร์บ"""
    r = np.random.default_rng(seed)
    t = np.arange(int(dur * SR)) / SR
    f = 30 + 40 * np.exp(-t * 6)
    sub = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 1.1)
    nz = r.standard_normal(len(t))
    low = sosfilt(butter(4, 300, "low", fs=SR, output="sos"), nz) * np.exp(-t * 10) * 0.9
    mid = sosfilt(butter(2, [90, 2500], "band", fs=SR, output="sos"), nz) * np.exp(-t * 28) * 0.6
    dry = sub + low + mid
    ir_t = np.arange(int(2.6 * SR)) / SR
    wet = []
    for ch in range(2):
        ir = sosfilt(butter(2, 3000, "low", fs=SR, output="sos"), r.standard_normal(len(ir_t))) * np.exp(-ir_t * 2.2)
        wet.append(fftconvolve(dry, ir)[:len(t)])
    wet = np.stack(wet, 1)
    wet /= np.abs(wet).max() + 1e-9
    st = np.stack([dry, dry], 1)
    st /= np.abs(st).max() + 1e-9
    y = st * 0.85 + wet * 0.35
    return y / (np.abs(y).max() + 1e-9) * 0.95


cache = {}
for m in plan.get("music", []):
    src = cache.setdefault(m["src"], load(m["src"]))
    seg = src[int(m["from"] * SR):int(m["to"] * SR)]
    place(fades(seg, m.get("fade_in", 0.01), m.get("fade_out", 0.02)), m["at"], m.get("gain_db", 0))
for b in plan.get("booms", []):
    place(boom(b.get("dur", 4.0), b.get("seed", 1)), b["at"], b.get("gain_db", -3))
for s in plan.get("sfx", []):
    src = cache.setdefault(s["src"], load(s["src"]))
    place(src, s["at"], s.get("gain_db", -12))

pk = np.abs(mix).max()
if pk > 0.98:
    mix *= 0.98 / pk
tmp = out + ".raw.wav"
wavfile.write(tmp, SR, mix.astype(np.float32))
m = plan.get("master", {"lufs": -14, "tp": -1.5, "lra": 11})
af = f"loudnorm=I={m['lufs']}:TP={m['tp']}:LRA={m['lra']}"
p1 = subprocess.run(["ffmpeg", "-hide_banner", "-i", tmp, "-af", af + ":print_format=json", "-f", "null", "-"], capture_output=True, text=True)
blk = p1.stderr[p1.stderr.rfind("{"):]   # ffmpeg พิมพ์ข้อความต่อท้าย JSON เลยต้องตัดถึง } ตัวแรก
js = json.loads(blk[:blk.find("}") + 1])
af2 = (af + f":measured_I={js['input_i']}:measured_TP={js['input_tp']}:measured_LRA={js['input_lra']}"
       f":measured_thresh={js['input_thresh']}:offset={js['target_offset']}:linear=true")
subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", tmp, "-af", af2, "-ar", str(SR), "-c:a", "pcm_s16le", out], check=True)
print("raw peak", round(float(pk), 3), "input I", js["input_i"], "LRA", js["input_lra"], "->", out)
