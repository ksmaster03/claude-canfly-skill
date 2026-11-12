# -*- coding: utf-8 -*-
# 20/10/2026 รวมคลิปแนะนำเดิม + คลิปเจาะลึกหลายระบบ เป็นคลิปเดียว
# รุ่น 5 ใช้ถึงการ์ดที่ 16 (เฟรม 0 ถึง 2412) ตัดก่อนฉากชื่อปิดที่ 100.54 เพราะคลิปเจาะลึกมีฉากปิดข้อความเดียวกันอยู่แล้ว
# เสียง: เพลงของรุ่น 5 เล่นต่ออีก 1.5 วิ ให้เสียงกระแทกที่ 100.6 ลงตรงจอดำต้นคลิปเจาะลึก แล้วจางหายก่อนเสียงพากย์เริ่ม
# การ์ดท้าย: parts/end_combo.mp4 (เครดิตเพลงทุกเพลงตามเงื่อนไขเจ้าของเพลง)
# ใช้: python src/combine.py
import json, os, subprocess, sys
sys.path.insert(0, '__PROJECT__/src')
from timeline import END_FRAME
import numpy as np
from scipy.io import wavfile

P = '__PROJECT__/'
V5 = os.environ.get('INTRO_CLIP', P + 'intro_old.mp4')   # คลิปแนะนำเดิมที่จะต่อหน้า (ตั้ง env INTRO_CLIP หรือวางไว้ที่ intro_old.mp4)
OUT = P + 'combined/combined.mp4'
SR, FPS = 48000, 24
N1 = 2413                       # เฟรมของรุ่น 5 ที่ใช้ (0 ถึง 2412)
T1 = N1 / FPS                   # 100.5417 วิ
TAIL, FADE = 1.5, 1.15          # เพลงรุ่น 5 เล่นต่อ 1.5 วิ จาง 1.15 วิสุดท้าย
os.makedirs(P + 'combined', exist_ok=True)


def load(path):
    raw = subprocess.run(['ffmpeg', '-v', 'error', '-i', path, '-f', 'f32le', '-ac', '2', '-ar', str(SR), '-'],
                         capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.float32).reshape(-1, 2).astype(np.float64)


a1 = load(V5)[:int((T1 + TAIL) * SR)]
f = int(FADE * SR); a1[-f:] *= np.linspace(1, 0, f)[:, None] ** 2
a2 = load(P + 'audio/master.wav')
n = int(T1 * SR) + len(a2)
mix = np.zeros((n, 2))
mix[:len(a1)] += a1
mix[int(T1 * SR):int(T1 * SR) + len(a2)] += a2
pk = np.abs(mix).max()
if pk > 0.98: mix *= 0.98 / pk
raw = P + 'combined/_mix_raw.wav'
wavfile.write(raw, SR, mix.astype(np.float32))
af = 'loudnorm=I=-14:TP=-1.5:LRA=16'
p1 = subprocess.run(['ffmpeg', '-hide_banner', '-i', raw, '-af', af + ':print_format=json', '-f', 'null', '-'], capture_output=True, text=True)
blk = p1.stderr[p1.stderr.rfind('{'):]
js = json.loads(blk[:blk.find('}') + 1])
af2 = (af + f":measured_I={js['input_i']}:measured_TP={js['input_tp']}:measured_LRA={js['input_lra']}"
       f":measured_thresh={js['input_thresh']}:offset={js['target_offset']}:linear=true")
wav = P + 'combined/master_combined.wav'
subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', raw, '-af', af2, '-ar', str(SR), '-c:a', 'pcm_s16le', wav], check=True)
os.remove(raw)
print('audio', round(n / SR, 2), 's · input I', js['input_i'])

fc = ('[0:v]trim=end_frame=%d,setpts=PTS-STARTPTS[a];' % N1 +
      '[1:v]trim=end_frame=%d,setpts=PTS-STARTPTS[b];' % END_FRAME + '[2:v]setpts=PTS-STARTPTS[c];[a][b][c]concat=n=3:v=1:a=0[v]')
subprocess.run(['ffmpeg', '-hide_banner', '-loglevel', 'error', '-y', '-i', V5, '-i', P + 'parts/silent.mp4', '-i', P + 'parts/end_combo.mp4',
                '-i', wav, '-filter_complex', fc, '-map', '[v]', '-map', '3:a', '-c:v', 'libx264', '-crf', '16', '-preset', 'medium',
                '-pix_fmt', 'yuv420p', '-r', str(FPS), '-c:a', 'aac', '-b:a', '256k', '-shortest', '-movflags', '+faststart', OUT], check=True)
print('video ->', OUT)
