# -*- coding: utf-8 -*-
# 20/10/2026 ฉบับเพลงตัวอย่าง (เพลง Suno ไม่มีเสียงร้อง 96 BPM ยาว 193.2 วิ) ผู้ใช้สั่งเปลี่ยนเพราะเพลงเดิมไม่สนุก
# เริ่มเพลงที่ 2.82 วิ ให้เบสกลับเข้า (180.53 ของเพลง) ตรงฉากชื่อแบรนด์ท้ายคลิป ช่วงดังเต็มต้นเพลง (14.76) ตรงชื่อเรื่อง และเพลงจบพร้อมคลิป
# เดิม: มิกซ์เสียงคลิปเจาะลึก: เสียงพากย์ 8 ย่อหน้า + เพลง cinematic ลดลงใต้เสียงพูด
# + เสียงตูมสังเคราะห์เบา ๆ ตรงจุดเปลี่ยนระบบ แล้ว loudnorm สองรอบเป็น -14 LUFS
# ใช้: python audio/build_mix.py audio/master.wav
import io, json, subprocess, sys
import numpy as np
from scipy.io import wavfile
from scipy.signal import butter, sosfilt, fftconvolve
sys.path.insert(0, '__PROJECT__/src')
from timeline import VO, DUR, TOP, MUSIC_AT, END_CARD, TOTAL, TITLE

P = '__PROJECT__/'
out = sys.argv[1]
SR = 48000
N = int(TOTAL * SR)
MUSIC = '__PROJECT__/ref_bgm/music.wav'
# 21/10/2026 เสียงพากย์ 1.1232 เท่า (เร็วขึ้น 8% จากรอบแรก) ช่วงคั่น 1.15 วิ คลิป 179.1 วิ: ตัดเพลงออก 4 ห้อง (16 จังหวะที่ตรวจจับได้ 70.496 ถึง 80.527
# ใต้เสียงพากย์ช่วงซ่อมบำรุง) เริ่มเพลงที่ 3.619 ให้ช่วงดังเต็ม (14.76) ตรงชื่อเรื่อง 11.13 และเบส (180.53) ตรงฉากชื่อแบรนด์ท้ายคลิป
SEGS = [(3.619, 70.496, 0.0), (80.527, 193.2, 66.877)]   # (จากเพลง, ถึงเพลง, วางที่เวลาคลิป)
MUSIC_OPEN, MUSIC_DUCK = -5.0, -21.0     # dB ของเพลงตอนไม่มีเสียงพูด / ตอนมีเสียงพูด


def load(path, ch=2):
    raw = subprocess.run(['ffmpeg', '-v', 'error', '-i', path, '-f', 'f32le', '-ac', str(ch), '-ar', str(SR), '-'],
                         capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.float32).reshape(-1, ch).astype(np.float64)


def boom(dur=4.0, seed=1):
    """เสียงตูมแบบเทรลเลอร์ (สูตรเดียวกับ trailerintro/scripts/build_audio.py)"""
    r = np.random.default_rng(seed)
    t = np.arange(int(dur * SR)) / SR
    f = 30 + 40 * np.exp(-t * 6)
    sub = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 1.1)
    nz = r.standard_normal(len(t))
    low = sosfilt(butter(4, 300, 'low', fs=SR, output='sos'), nz) * np.exp(-t * 10) * 0.9
    mid = sosfilt(butter(2, [90, 2500], 'band', fs=SR, output='sos'), nz) * np.exp(-t * 28) * 0.6
    dry = sub + low + mid
    ir_t = np.arange(int(2.6 * SR)) / SR
    wet = np.stack([fftconvolve(dry, sosfilt(butter(2, 3000, 'low', fs=SR, output='sos'), r.standard_normal(len(ir_t))) * np.exp(-ir_t * 2.2))[:len(t)] for _ in range(2)], 1)
    wet /= np.abs(wet).max() + 1e-9
    st = np.stack([dry, dry], 1); st /= np.abs(st).max() + 1e-9
    y = st * 0.85 + wet * 0.35
    return y / (np.abs(y).max() + 1e-9) * 0.95


mix = np.zeros((N, 2))


def place(buf, at, gain_db=0.0):
    i0 = int(round(at * SR)); n = min(len(buf), N - i0)
    if n > 0: mix[i0:i0 + n] += buf[:n] * 10 ** (gain_db / 20)


# เพลง: เริ่มให้เสียงตูมท่อนจบ (วินาทีที่ 176 ของเพลง) ตรงคำว่า ท็อปเทียร์
src = load(MUSIC)
m = np.zeros((N, 2))
XF = int(0.04 * SR)
for a, b, at_ in SEGS:
    seg = src[int(a * SR):int(b * SR)].copy()
    seg[:XF] *= np.linspace(0, 1, XF)[:, None]; seg[-XF:] *= np.linspace(1, 0, XF)[:, None]
    i = int(round(at_ * SR)) - (XF // 2 if at_ > 0 else 0); n = min(len(seg), N - i); m[i:i + n] += seg[:n]
fi = int(0.6 * SR); m[:fi] *= np.linspace(0, 1, fi)[:, None]
env_db = np.full(N, MUSIC_OPEN)
t = np.arange(N) / SR
for v, a in VO.items():
    b = a + DUR[v]
    down = np.clip((t - (a - 0.35)) / 0.35, 0, 1)        # ลดลงก่อนเริ่มพูด 0.35 วิ
    up = np.clip(((b + 0.55) - t) / 0.55, 0, 1)          # ค่อยดังขึ้นหลังพูดจบ 0.55 วิ
    w = np.minimum(down, up)
    env_db = np.minimum(env_db, MUSIC_OPEN + (MUSIC_DUCK - MUSIC_OPEN) * w)
# ช่วงคำว่า ท็อปเทียร์ กรุ๊ป ถึงท้ายคลิป ปล่อยเพลงเต็มขึ้นบ้างแม้ยังพูดอยู่
tail = np.clip((t - (TOP - 0.2)) / 0.4, 0, 1)
env_db = env_db + (MUSIC_DUCK + 7 - env_db) * tail * (env_db < MUSIC_DUCK + 7)
env = 10 ** (env_db / 20)
mix += m * env[:, None]

# เสียงพากย์
for v, a in VO.items():
    place(load(P + f'vo/prep/{v}.wav'), a, 0.0)

# เสียงตูมเบา ๆ ตรงจุดเปลี่ยนระบบ (ไม่ใส่ที่ชื่อเรื่องและท่อนจบ เพราะเพลงมีตูมของมันเองอยู่แล้ว)
for i, v in enumerate(['v04', 'v05', 'v06', 'v07']):
    place(boom(3.0, seed=11 + i), VO[v] - 0.3, -14)
place(boom(4.0, seed=21), END_CARD, -12)
place(boom(4.0, seed=31), TITLE, -9)      # ชื่อเรื่อง
place(boom(4.5, seed=41), TOP - 0.05, -9)  # ท็อปเทียร์ กรุ๊ป (เพลงมีเบสเข้าตรงนี้อยู่แล้ว)

# ค่อย ๆ จางท้ายคลิป
fo = int(1.5 * SR); mix[-fo:] *= np.linspace(1, 0, fo)[:, None]
pk = np.abs(mix).max()
if pk > 0.98: mix *= 0.98 / pk
tmp = out + '.raw.wav'
wavfile.write(tmp, SR, mix.astype(np.float32))
af = 'loudnorm=I=-14:TP=-1.5:LRA=16'
p1 = subprocess.run(['ffmpeg', '-hide_banner', '-i', tmp, '-af', af + ':print_format=json', '-f', 'null', '-'], capture_output=True, text=True)
blk = p1.stderr[p1.stderr.rfind('{'):]
js = json.loads(blk[:blk.find('}') + 1])
af2 = (af + f":measured_I={js['input_i']}:measured_TP={js['input_tp']}:measured_LRA={js['input_lra']}"
       f":measured_thresh={js['input_thresh']}:offset={js['target_offset']}:linear=true")
subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', tmp, '-af', af2, '-ar', str(SR), '-c:a', 'pcm_s16le', out], check=True)
print('music segs', SEGS, 'raw peak', round(float(pk), 3), 'input I', js['input_i'], 'LRA', js['input_lra'], '->', out)
