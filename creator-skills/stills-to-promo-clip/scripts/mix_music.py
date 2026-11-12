"""Fit "Volatile Reaction" to the 32 s promo cut and write music.wav.

Track: "Volatile Reaction" by Kevin MacLeod (incompetech.com), Creative Commons Attribution 4.0.
Changes made here (must be mentioned with the credit): slowed 155 -> 150 bpm so beats land on the
picture cuts, excerpt 0:09.5-0:40.5 chosen so the track's big entry (0:29.86) hits the title at 21 s,
fade-out, plus our own riser/impact sounds. Needs music_src/volatile.npy (decoded stereo float32 at 44.1 kHz).
"""
import os
import numpy as np
from scipy.io import wavfile
from scipy.signal import butter, lfilter, resample_poly

HERE = os.path.dirname(os.path.abspath(__file__))
SR, LEN = 44100, 32.0
N = int(SR * LEN)
BIG_ENTRY = 29.858          # seconds into the original where the full brass section enters (measured)
TITLE_AT = 21.0             # where that entry must land in the promo
rng = np.random.default_rng(3)

x = np.load(os.path.join(HERE, "music_src", "volatile.npy")).astype(np.float64)
x = x[int((BIG_ENTRY - TITLE_AT * 30 / 31) * SR):]
x = resample_poly(x, 31, 30, axis=0)          # 155 -> 150 bpm (31/30 of the original length)
mix = x[:N].copy() * 0.8


def lp(s, hz):
    b, a = butter(2, hz / (SR / 2)); return lfilter(b, a, s)


def hp(s, hz):
    b, a = butter(2, hz / (SR / 2), "high"); return lfilter(b, a, s)


def put(sig, t, gain):
    i = int(t * SR); sig = sig[: N - i] * gain
    mix[i:i + len(sig)] += sig[:, None]


def boom():
    n = int(2.5 * SR); t = np.arange(n) / SR
    return (np.sin(2 * np.pi * (38 * t + 30 * (1 - np.exp(-t * 6)) / 6)) + 0.5 * lp(rng.standard_normal(n), 220)) * np.exp(-t / 0.7)


def riser(dur):
    n = int(dur * SR); t = np.arange(n) / SR
    return hp(rng.standard_normal(n), 1500) * (t / dur) ** 2 * 0.6 + 0.3 * np.sin(2 * np.pi * (200 * t + 300 * t * t / dur)) * (t / dur) ** 2


put(riser(2.0), 19.0, 0.30)      # into the title
put(boom(), 21.0, 0.45)          # title slam
put(riser(1.0), 24.0, 0.22)
put(boom(), 25.0, 0.45)          # call to action

env = np.ones(N)
k = int(0.03 * SR); env[:k] = np.linspace(0, 1, k)
k = int(2.2 * SR); env[-k:] = np.linspace(1, 0, k) ** 2
mix *= env[:, None]
mix = np.tanh(mix * 1.05)
mix *= 0.89 / np.abs(mix).max()
wavfile.write(os.path.join(HERE, "music.wav"), SR, (mix * 32767).astype(np.int16))
print("music.wav written:", LEN, "s, peak", float(np.abs(mix).max()))
