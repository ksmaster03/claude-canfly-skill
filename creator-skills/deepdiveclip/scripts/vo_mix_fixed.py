# -*- coding: utf-8 -*-
# 29/10/2026 มิกซ์เสียงพากย์ 25 ย่อหน้าลงบนเพลง (audio/master.wav) ตามช่วงเวลาใน vo/plan.json
# ต่อย่อหน้า: ตัดเงียบหัวท้าย · ปรับความดังให้เท่ากัน · ถ้ายาวเกินช่องให้เร่งด้วย atempo (เพดาน 1.12 ตามที่ผู้ใช้เคยรับได้)
# เพลงลดลงใต้เสียงพูดแบบคลิปเจาะลึก (ลงก่อนพูด 0.35 วิ ขึ้นหลังพูด 0.55 วิ) แล้ว loudnorm สองรอบเป็น -14 LUFS
# ใช้: python src/vo_mix.py   ได้ audio/master_vo.wav + vo/prep/fit.json
import io, json, os, subprocess, sys
import numpy as np
from scipy.io import wavfile
sys.stdout.reconfigure(encoding='utf-8')

SR = 48000
TOTAL = 120.0
N = int(TOTAL * SR)
# ย่อหน้าที่สร้างซ้ำแล้วดีกว่า เช่น {"p07": "p07_r2"} อ่านจาก vo/takes.json ถ้ามี
TAKES = json.load(io.open('vo/takes.json', encoding='utf-8')) if os.path.exists('vo/takes.json') else {}
MAX_TEMPO = 1.12
MUSIC_OPEN, MUSIC_DUCK = -3.0, -16.5   # dB ของเพลงตอนไม่มีเสียงพูด / ตอนมีเสียงพูด (เทียบกับ audio/master.wav)
VO_RMS_DB = -20.0                   # ความดังเฉลี่ยช่วงพูดของทุกย่อหน้าก่อนมิกซ์


def load(path, ch=1):
    raw = subprocess.run(['ffmpeg', '-v', 'error', '-i', path, '-f', 'f32le', '-ac', str(ch), '-ar', str(SR), '-'],
                         capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.float32).reshape(-1, ch).astype(np.float64)


def frames_db(x, w):
    n = len(x) // w
    return 20 * np.log10(np.sqrt((x[:n * w].reshape(n, w) ** 2).mean(1)) + 1e-9)


def tempo(x, r):
    tmp = 'vo/prep/_t.f32'; x.astype(np.float32).tofile(tmp)
    raw = subprocess.run(['ffmpeg', '-v', 'error', '-f', 'f32le', '-ar', str(SR), '-ac', '1', '-i', tmp,
                          '-af', f'atempo={r:.4f}', '-f', 'f32le', '-'], capture_output=True, check=True).stdout
    os.remove(tmp)
    return np.frombuffer(raw, np.float32).astype(np.float64)


os.makedirs('vo/prep', exist_ok=True)
plan = json.load(io.open('vo/plan.json', encoding='utf-8'))
vo = np.zeros(N)
fit, spans, warn = {}, [], []
w = int(0.01 * SR)
for p in plan:
    pid = p['id']; take = TAKES.get(pid, pid)
    x = load(f'vo/para/{take}.mp3')[:, 0]
    db = frames_db(x, w); on = np.where(db > -45)[0]
    a = max(0, on[0] * w - int(0.04 * SR)); b = min(len(x), (on[-1] + 1) * w + int(0.12 * SR))
    x = x[a:b]
    sp = frames_db(x, w); act = sp > -40
    rms = 20 * np.log10(np.sqrt(np.mean((10 ** (sp[act] / 20)) ** 2)) + 1e-9)
    x *= 10 ** ((VO_RMS_DB - rms) / 20)
    d0 = len(x) / SR; slot = p['end'] - p['start']; r = 1.0
    if d0 > slot:
        r = d0 / slot
        if r > MAX_TEMPO:
            warn.append(f'{pid} ยาว {d0:.2f} วิ ช่อง {slot:.2f} ต้องเร่ง {r:.3f} เกินเพดาน ใช้ {MAX_TEMPO} แล้วล้นช่อง')
            r = MAX_TEMPO
        x = tempo(x, r)
    d = len(x) / SR
    i0 = int(round(p['start'] * SR)); n = min(len(x), N - i0); vo[i0:i0 + n] += x[:n]
    spans.append((p['start'], p['start'] + d))
    fit[pid] = {'take': take, 'start': p['start'], 'dur': round(d, 3), 'raw': round(d0, 3), 'slot': round(slot, 3), 'tempo': round(r, 3)}
    print(f'{pid} {take:7s} ช่อง {slot:4.2f}  เสียง {d0:4.2f} -> {d:4.2f}  เร่ง {r:.3f}  เหลือ {slot - d:+.2f}')
json.dump(fit, io.open('vo/prep/fit.json', 'w', encoding='utf-8'), indent=1, ensure_ascii=False)

# เพลง
m = load('audio/master.wav', 2)[:N]
m = np.vstack([m, np.zeros((N - len(m), 2))]) if len(m) < N else m
t = np.arange(N) / SR
env_db = np.full(N, MUSIC_OPEN)
for a, b in spans:
    down = np.clip((t - (a - 0.35)) / 0.35, 0, 1)
    up = np.clip(((b + 0.55) - t) / 0.55, 0, 1)
    env_db = np.minimum(env_db, MUSIC_OPEN + (MUSIC_DUCK - MUSIC_OPEN) * np.minimum(down, up))
mus = m * (10 ** (env_db / 20))[:, None]
mix = mus + vo[:, None]

# วัดว่าเพลงเบากว่าเสียงพูดกี่ dB ในช่วงที่พูด
speech = np.zeros(N, bool)
for a, b in spans: speech[int(a * SR):int(b * SR)] = True
vr = 20 * np.log10(np.sqrt(np.mean(vo[speech] ** 2)) + 1e-9)
mr = 20 * np.log10(np.sqrt(np.mean(mus[speech] ** 2)) + 1e-9)
print(f'ช่วงพูด: เสียงพูด {vr:.1f} dB · เพลง {mr:.1f} dB · เพลงเบากว่า {vr - mr:.1f} dB')

pk = np.abs(mix).max()
if pk > 0.98: mix *= 0.98 / pk
tmp = 'audio/_master_vo.raw.wav'; out = 'audio/master_vo.wav'
wavfile.write(tmp, SR, mix.astype(np.float32))
af = 'loudnorm=I=-14:TP=-1.5:LRA=16'
p1 = subprocess.run(['ffmpeg', '-hide_banner', '-i', tmp, '-af', af + ':print_format=json', '-f', 'null', '-'], capture_output=True, text=True)
blk = p1.stderr[p1.stderr.rfind('{'):]
js = json.loads(blk[:blk.find('}') + 1])
af2 = (af + f":measured_I={js['input_i']}:measured_TP={js['input_tp']}:measured_LRA={js['input_lra']}"
       f":measured_thresh={js['input_thresh']}:offset={js['target_offset']}:linear=true")
subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', tmp, '-af', af2, '-ar', str(SR), '-c:a', 'pcm_s16le', out], check=True)
os.remove(tmp)
for s in warn: print('WARN', s)
print('raw peak', round(float(pk), 3), 'input I', js['input_i'], '->', out)
