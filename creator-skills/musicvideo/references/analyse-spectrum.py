"""Band balance, stereo and dynamics of a track. Run BEFORE choosing any EQ move.

    python analyse-spectrum.py before.wav [after.wav]

With two files it prints the SHAPE of each relative to the 60-120 Hz punch band,
which is the comparison that matters: absolute band levels move when the master
gets louder, so they cannot tell you whether the tone actually changed.

The reason this exists: on a bass-heavy track the instinct is to boost bass, and
that is usually wrong. Measure first. On the track this was built for, 20-60 Hz
was already the loudest band in the whole mix -- boosting it would have made the
limiter duck the entire song on every kick.
"""
import subprocess
import sys

import numpy as np

BANDS = [(20, 60, 'sub 20-60'), (60, 120, 'punch 60-120'), (120, 250, 'lowmid 120-250'),
         (250, 500, 'mud 250-500'), (500, 1000, 'mid 500-1k'), (1000, 2000, 'upmid 1-2k'),
         (2000, 4000, 'pres 2-4k'), (4000, 8000, 'bright 4-8k'), (8000, 16000, 'air 8-16k')]


def load(path, sr=48000):
    raw = subprocess.run(['ffmpeg', '-v', 'error', '-i', path, '-f', 'f32le',
                          '-acodec', 'pcm_f32le', '-ac', '2', '-ar', str(sr), '-'],
                         capture_output=True).stdout
    return np.frombuffer(raw, dtype=np.float32).reshape(-1, 2), sr


def bands(a, sr, n=8192):
    mono = a.mean(axis=1)
    win = np.hanning(n)
    acc, c = np.zeros(n // 2 + 1), 0
    for i in range(0, len(mono) - n, n * 4):
        acc += np.abs(np.fft.rfft(mono[i:i + n] * win))
        c += 1
    acc /= max(c, 1)
    f = np.fft.rfftfreq(n, 1 / sr)
    return [(name, 20 * np.log10(np.sqrt((acc[(f >= lo) & (f < hi)] ** 2).mean()) + 1e-12))
            for lo, hi, name in BANDS]


def report(path):
    a, sr = load(path)
    b = bands(a, sr)
    mono = a.mean(axis=1)
    side = (a[:, 0] - a[:, 1]) / 2
    rms = np.sqrt((mono ** 2).mean())
    stats = {
        'peak dBFS': 20 * np.log10(np.abs(a).max() + 1e-12),
        'crest dB': 20 * np.log10(np.abs(mono).max() / (rms + 1e-12)),
        'L/R corr': np.corrcoef(a[:, 0], a[:, 1])[0, 1],
        'side/mid': np.sqrt((side ** 2).mean()) / (rms + 1e-12),
        'clipped': float((np.abs(a) >= 0.999).sum()),
    }
    return b, stats


files = sys.argv[1:]
if not files:
    raise SystemExit(__doc__)

reports = [(f, *report(f)) for f in files]
ref = 'punch 60-120'
print(f"{'band':16s}" + ''.join(f"{f.split('/')[-1][:12]:>14s}" for f, _, _ in reports))
print('-' * (16 + 14 * len(reports)))
for i, (_, name) in enumerate([(0, n) for n, _ in reports[0][1]]):
    row = f'{name:16s}'
    for _, b, _ in reports:
        d = dict(b)
        row += f'{d[name] - d[ref]:14.1f}'
    print(row)
print('(dB relative to the 60-120 Hz punch band -- shape, not level)')
print()
for f, _, st in reports:
    print(f"{f.split('/')[-1][:24]:26s}" + '  '.join(f'{k}={v:.3f}' for k, v in st.items()))
