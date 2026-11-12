"""Turn the track into per-frame data the video reads. Reproducible: one command.

    python tools/analyse.py

Two different files are read on purpose:

  * TEMPO comes from the PRE-master file. Mastering to -9 LUFS pulled LRA from
    3.60 to 1.90, and the flatter the transients the less a beat tracker has to
    lock onto -- the same search scores 0.514 on the pre-master and 0.456 on the
    master, and disagrees on BPM by 0.13.
  * LEVELS come from the MASTERED file, because that is the mix the viewer
    hears. A cone pumping on the pre-master's dynamics would visibly lead the
    audio it is supposed to be driven by.
"""
import json, os, subprocess, sys
import numpy as np

PRE = sys.argv[1] if len(sys.argv) > 1 else 'audio/source.wav'
MASTER = sys.argv[2] if len(sys.argv) > 2 else 'audio/master.wav'
SR, HOP, NFFT, FPS = 22050, 512, 2048, 30
NBINS = 48

def stft(path):
    raw = subprocess.run(['ffmpeg', '-v', 'error', '-i', path, '-ac', '1',
                          '-ar', str(SR), '-f', 'f32le', '-'],
                         capture_output=True).stdout
    x = np.frombuffer(raw, dtype=np.float32)
    n = 1 + (len(x) - NFFT) // HOP
    fr = np.lib.stride_tricks.as_strided(
        x, (n, NFFT), (x.strides[0] * HOP, x.strides[0]))
    S = np.abs(np.fft.rfft(fr * np.hanning(NFFT).astype(np.float32), axis=1))
    return x, S, np.fft.rfftfreq(NFFT, 1 / SR), np.arange(n) * HOP / SR

def find_bpm(S):
    """Full-track comb search. The long baseline is what buys the precision:
    over 297s a 0.1 BPM error is still under a tenth of a beat at the end."""
    flux = np.maximum(0, np.diff(S, axis=0)).sum(1)
    flux = (flux - flux.mean()) / (flux.std() + 1e-9)
    fps_env = SR / HOP
    best = (0.0, -9.0, 0.0)
    for bpm in np.arange(120.0, 140.0, 0.01):
        beat = 60.0 / bpm * fps_env
        base = np.arange(int((len(flux) - 1) / beat)) * beat
        bs, bp = -9.0, 0.0
        for p in np.linspace(0, beat, 24, endpoint=False):
            ii = np.round(base + p).astype(int)
            ii = ii[ii < len(flux)]
            s = float(flux[ii].mean())
            if s > bs:
                bs, bp = s, p
        if bs > best[1]:
            best = (float(bpm), bs, bp / fps_env)
    return best

def norm(e):
    """5th..99th percentile, so 0 is quiet FOR THIS TRACK and 1 is about as
    loud as it gets. Absolute dB would leave every bar pinned on a -9 master."""
    lo, hi = np.percentile(e, 5), np.percentile(e, 99)
    return np.clip((e - lo) / (hi - lo + 1e-9), 0, 1)

_, Spre, _, _ = stft(PRE)
BPM, score, phase = find_bpm(Spre)
BEAT, BAR = 60.0 / BPM, 4 * 60.0 / BPM
print(f"tempo   : {BPM:.2f} BPM (score {score:.3f})  beat phase {phase:.4f}s  bar {BAR:.4f}s")

xm, S, f, t = stft(MASTER)
DUR = len(xm) / SR
nframes = int(DUR * FPS)
ft = np.arange(nframes) / FPS

BANDS = {'sub': (20, 90), 'bass': (90, 200), 'lowmid': (200, 600),
         'mid': (600, 2500), 'high': (2500, 10000)}
bands = {k: norm(np.interp(ft, t, S[:, (f >= lo) & (f < hi)].sum(1)))
         for k, (lo, hi) in BANDS.items()}

# Log-spaced bins for the analyser. 5 bands is enough to drive a cone but far
# too coarse to look like a spectrum -- neighbouring bars move as one block.
#
# Scaling is dB against ONE global reference, not per-bin percentiles. Per-bin
# normalisation was the first attempt and it looked wrong for a reason: it gives
# every bin its own full 0..1 range, which flattens the mix's actual tilt, so a
# track whose sub band is the loudest thing in it renders with a bass end no
# taller than its hi-hats. A shared reference keeps the tilt the ear hears.
edges = np.geomspace(30, 11000, NBINS + 1)
# MEAN, not sum. The bins are log-spaced, so the 30-33 Hz bin spans 3 Hz while
# the 10-11 kHz bin spans 1000 Hz; summing hands the top of the range a ~300x
# head start that has nothing to do with how loud it is. Mean = spectral
# density, which is what an analyser actually shows.
def bin_energy(i):
    m = (f >= edges[i]) & (f < edges[i + 1])
    if m.any():
        return S[:, m].mean(1)
    # Below ~110 Hz a log bin is narrower than the 10.77 Hz FFT resolution
    # (22050/2048), so it can straddle no bin at all. Reading the nearest
    # bin keeps the low end continuous; taking mean() of the empty slice
    # silently produced NaN across the whole analyser.
    c = np.sqrt(edges[i] * edges[i + 1])
    return S[:, int(np.argmin(np.abs(f - c)))]

raw = np.stack([np.interp(ft, t, bin_energy(i)) for i in range(NBINS)], axis=1)
db = 20 * np.log10(raw + 1e-9)
# +4.5 dB/decade tilt, the usual analyser trick: without it the top octaves sit
# on the floor all song, because music simply has less energy up there.
centres = np.sqrt(edges[:-1] * edges[1:])
db = db + 2.0 * np.log10(centres / centres[0])[None, :]
ceil = np.percentile(db, 99.5)
FLOOR_DB = 52.0
spec = np.clip((db - (ceil - FLOOR_DB)) / FLOOR_DB, 0, 1)

rms = norm(np.interp(ft, t, np.sqrt((np.lib.stride_tricks.as_strided(
    xm, (1 + (len(xm) - NFFT) // HOP, NFFT),
    (xm.strides[0] * HOP, xm.strides[0])) ** 2).mean(1))))

PH = phase
def snap_half(s):
    return PH + round((s - PH) / (BAR / 2)) * (BAR / 2)

# Scene stills in filename order, read from the folder rather than listed here,
# so the cut list follows whatever the image step actually produced.
IMG_DIR = 'public/img'
IMAGES = sorted(os.path.splitext(f)[0] for f in os.listdir(IMG_DIR)
                if f.lower().endswith(('.png', '.jpg', '.jpeg', '.webp')))
if not IMAGES:
    raise SystemExit('no stills in ' + IMG_DIR + ' -- generate them first')
hi_thr = np.percentile(rms, 62)
scenes, tt, i = [], PH, 0
while tt < DUR - 1.0:
    seg = rms[int(tt * FPS): int(min(DUR, tt + 4 * BAR) * FPS)]
    bars = 2 if (len(seg) and seg.mean() > hi_thr) else 4
    end = snap_half(min(tt + bars * BAR, DUR))
    if end - tt < BAR:
        end = DUR
    scenes.append({'img': IMAGES[i % len(IMAGES)], 'start': round(tt, 4),
                   'end': round(end, 4), 'bars': bars, 'dir': i % 4})
    tt, i = end, i + 1

out = {
    'fps': FPS, 'frames': nframes, 'duration': round(DUR, 3),
    'bpm': round(BPM, 2), 'beatSeconds': round(BEAT, 6),
    'barSeconds': round(BAR, 6), 'beatPhase': round(PH, 4),
    'tempoScore': round(score, 3),
    'bands': {k: [round(float(v), 3) for v in b] for k, b in bands.items()},
    'spectrum': [[round(float(v), 3) for v in row] for row in spec],
    'rms': [round(float(v), 3) for v in rms],
    'scenes': scenes,
}
json.dump(out, open('src/features.json', 'w'))
import os
lowmean = spec[:, :12].mean(); highmean = spec[:, -12:].mean()
print(f"frames  : {nframes} ({DUR:.2f}s)   spectrum bins: {NBINS}")
print(f"analyser: low 12 bins mean {lowmean:.3f}  vs high 12 bins mean {highmean:.3f}  "
      f"(low should lead on a bass track)")
print(f"scenes  : {len(scenes)}  ({sum(1 for s in scenes if s['bars']==2)} x 2-bar, "
      f"{sum(1 for s in scenes if s['bars']==4)} x 4-bar)")
print(f"written : src/features.json  {os.path.getsize('src/features.json')/1e6:.2f} MB")
