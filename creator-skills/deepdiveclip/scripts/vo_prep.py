# -*- coding: utf-8 -*-
# 20/10/2026 เตรียมเสียงพากย์รายย่อหน้า: ตัดเงียบหัวท้าย ย่อช่วงหยุดที่ยาวเกิน แล้วเร่ง 4% (atempo คงระดับเสียง)
import subprocess, numpy as np, json, io, os
SR = 48000
D = '__PROJECT__/vo/'
SRC = ['p01.mp3', 'p02.mp3', 'p03_fix.wav', 'p04.mp3', 'p05.mp3', 'p06.mp3', 'p07.mp3', 'p08_fix.wav']
MAXGAP, TEMPO = 0.42, 1.1232   # 21/10/2026 ผู้ใช้ขอเร็วขึ้น 8% จากรอบแรก (1.04 x 1.08) หลังลอง 15% แล้วเร็วไป
def load(f):
    raw = subprocess.run(['ffmpeg', '-v', 'error', '-i', f, '-ac', '1', '-ar', str(SR), '-f', 'f32le', '-'], capture_output=True).stdout
    return np.frombuffer(raw, np.float32).copy()
out = {}
os.makedirs(D + 'prep', exist_ok=True)
for i, f in enumerate(SRC, 1):
    x = load(D + 'paras/' + f); w = int(0.01 * SR); n = len(x) // w
    db = np.array([20 * np.log10(np.sqrt(np.mean(x[k*w:(k+1)*w] ** 2)) + 1e-9) for k in range(n)])
    sil = db < -45
    # ช่วงเงียบต่อเนื่อง
    runs, k = [], 0
    while k < n:
        if sil[k]:
            j = k
            while j < n and sil[j]: j += 1
            runs.append((k, j)); k = j
        else: k += 1
    keep = np.ones(len(x), bool)
    for a, b in runs:
        L = (b - a) * 0.01
        if a == 0: keep[:max(0, b * w - int(0.05 * SR))] = False; continue
        if b >= n: keep[a * w + int(0.15 * SR):] = False; continue
        if L > MAXGAP:
            cut = int((L - MAXGAP) * SR); mid = (a * w + b * w) // 2
            keep[mid - cut // 2: mid - cut // 2 + cut] = False
    y = x[keep]
    tmp = D + 'prep/_t.f32'; y.astype(np.float32).tofile(tmp)
    o = D + 'prep/v%02d.wav' % i
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-f', 'f32le', '-ar', str(SR), '-ac', '1', '-i', tmp, '-af', 'atempo=%.3f' % TEMPO, '-c:a', 'pcm_s16le', o], check=True)
    d = float(subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', o], capture_output=True, text=True).stdout)
    out['v%02d' % i] = round(d, 3); print('v%02d' % i, f, 'raw %.2f -> %.2f' % (len(x) / SR, d))
os.remove(tmp)
json.dump(out, io.open(D + 'prep/durations.json', 'w'), indent=1)
print('total', round(sum(out.values()), 2))
