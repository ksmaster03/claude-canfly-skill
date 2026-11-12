# -*- coding: utf-8 -*-
# 18/10/2026 หาจังหวะเสียงตูม/วูบในเสียงต้นแบบ เพื่อวางคิวภาพให้ตรง (พิมพ์เวลา + ความแรง)
import sys, json
import numpy as np
from scipy.io import wavfile
from scipy.signal import stft, find_peaks

sr, x = wavfile.read(sys.argv[1])
x = x.astype(np.float32)
if x.ndim > 1:
    x = x.mean(axis=1)
x /= (np.abs(x).max() + 1e-9)
hop = 480  # 10 ms
f, t, Z = stft(x, fs=sr, nperseg=2048, noverlap=2048 - hop)
S = np.log1p(np.abs(Z) * 50)
flux = np.maximum(0, np.diff(S, axis=1)).sum(axis=0)
flux = np.concatenate([[0], flux])
flux /= flux.max()
low = S[f < 150].mean(axis=0)
rms = np.sqrt(np.convolve(x ** 2, np.ones(hop) / hop, mode="same"))[::hop][: len(t)]
rms_db = 20 * np.log10(rms + 1e-6)
pk, pr = find_peaks(flux, height=0.18, distance=25)
hits = []
for p in pk:
    a = max(0, p - 5); b = min(len(rms_db) - 1, p + 60)
    hits.append({"t": round(float(t[p]), 2), "flux": round(float(flux[p]), 2),
                 "low": round(float(low[p]), 2), "db_after": round(float(rms_db[a:b].max()), 1)})
for h in hits:
    print(h)
# ความดังทุก 0.5 วินาที
print("--- loudness every 0.5s (dBFS) ---")
step = 50
print(" ".join(f"{i*0.5:.1f}:{rms_db[i*step:(i+1)*step].max():.0f}" for i in range(len(rms_db) // step)))
json.dump(hits, open(sys.argv[2], "w"), indent=1)
