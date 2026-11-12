"""Find the hook: the loudest sustained stretch that starts where the music turns.

Two things this gets wrong if you are not careful, both learned the hard way:

  * Measure on the PRE-MASTER. The -9 LUFS master has LRA 1.90 -- loud and
    quiet sections are squeezed to within a hair of each other, and any
    energy-based search on it returns noise.
  * Search several window LENGTHS. An 87s window spans 30% of a 297s track, so
    every placement averages to the same number; the first version of this
    picked a "hook" that was 0.6% BELOW the track's own average energy.
"""
import json, subprocess, sys
import numpy as np

PRE = sys.argv[1] if len(sys.argv) > 1 else 'audio/source.wav'
SR, HOP, NFFT = 22050, 512, 2048
F = json.load(open('src/features.json'))
BAR, PH, DUR = F['barSeconds'], F['beatPhase'], F['duration']
MAX_S, MIN_S = 88.0, 30.0

raw = subprocess.run(['ffmpeg', '-v', 'error', '-i', PRE, '-ac', '1', '-ar', str(SR),
                      '-f', 'f32le', '-'], capture_output=True).stdout
x = np.frombuffer(raw, dtype=np.float32)
n = 1 + (len(x) - NFFT) // HOP
fr = np.lib.stride_tricks.as_strided(x, (n, NFFT), (x.strides[0] * HOP, x.strides[0]))
S = np.abs(np.fft.rfft(fr * np.hanning(NFFT).astype(np.float32), axis=1))
f = np.fft.rfftfreq(NFFT, 1 / SR)
t = np.arange(n) * HOP / SR

bars = np.arange(PH, DUR - BAR, BAR)
edges = np.geomspace(40, 10000, 17)
V, E = [], []
for b in bars:
    m = (t >= b) & (t < b + BAR)
    seg = S[m] if m.sum() >= 4 else np.zeros((1, S.shape[1]))
    v = np.array([np.log1p(seg[:, (f >= edges[i]) & (f < edges[i+1])].mean()) for i in range(16)])
    V.append(v / (np.linalg.norm(v) + 1e-9))
    E.append(float(np.sqrt((x[int(b*SR):int((b+BAR)*SR)] ** 2).mean())))
V = np.array(V)
E = np.array(E); E = (E - E.min()) / (E.max() - E.min() + 1e-9)
nov = np.r_[0, 1 - np.einsum('ij,ij->i', V[1:], V[:-1])]
nov = nov / (nov.max() + 1e-9)

print(f"pre-master bar energy: min {E.min():.3f}  mean {E.mean():.3f}  max {E.max():.3f}  "
      f"spread {E.max()-E.min():.3f}")

cands = []
for L in range(int(MIN_S // BAR), int(MAX_S // BAR) + 1):
    for s in range(0, len(bars) - L):
        seg = E[s:s + L]
        # A hook must be loud THROUGHOUT, so the floor matters as much as the
        # mean -- otherwise a window happily swallows a quiet breakdown.
        score = 0.55 * seg.mean() + 0.30 * np.percentile(seg, 15) + 0.15 * nov[s]
        cands.append((score, s, L, seg.mean(), np.percentile(seg, 15), nov[s]))
cands.sort(reverse=True)

print(f"\n{'start':>8s} {'len':>7s} {'score':>6s} {'mean':>6s} {'floor':>6s} {'onset':>6s}")
for sc, s, L, mn, fl, ov in cands[:8]:
    print(f"{bars[s]:8.2f} {L*BAR:6.1f}s {sc:6.3f} {mn:6.3f} {fl:6.3f} {ov:6.3f}")

sc, s, L, mn, fl, ov = cands[0]
start, end = bars[s], bars[s] + L * BAR
print(f"\n=> hook {start:.3f}s .. {end:.3f}s  ({end-start:.2f}s)  frames {round(start*30)}..{round(end*30)-1}")
print(f"   mean energy {mn:.3f} vs track {E.mean():.3f}  ({(mn/E.mean()-1)*100:+.1f}%)")
json.dump({'start': round(start, 4), 'end': round(end, 4),
           'startFrame': round(start * 30), 'endFrame': round(end * 30) - 1,
           'meanEnergy': round(float(mn), 4), 'trackMean': round(float(E.mean()), 4)},
          open('src/hook.json', 'w'))
