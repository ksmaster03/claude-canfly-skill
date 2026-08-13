"""Find a track's real downbeats so the video's bar grid can be cut onto one.

    python downbeat.py "$MEDIA/bgm/<track>.mp3" [bpm] [after_seconds]

Prints the bar length and the first downbeats past `after_seconds` (default: the
track's measured intro length). Feed the chosen one straight into ffmpeg -ss.

Why this exists: cutting the music at an arbitrary offset puts the song's bars out
of phase with the video's bar grid, and every pose swap then lands slightly off the
beat. It reads as "cheap" without the viewer being able to say why.
"""
import subprocess
import sys

import numpy as np

SR, HOP, NFFT = 22050, 512, 2048


def onset_flux(path):
    """Spectral flux envelope, one value per HOP samples."""
    raw = subprocess.run(
        ["ffmpeg", "-v", "error", "-i", path, "-ac", "1", "-ar", str(SR), "-f", "f32le", "-"],
        capture_output=True,
    ).stdout
    x = np.frombuffer(raw, dtype=np.float32)
    n = 1 + (len(x) - NFFT) // HOP
    frames = np.lib.stride_tricks.as_strided(x, (n, NFFT), (x.strides[0] * HOP, x.strides[0]))
    S = np.abs(np.fft.rfft(frames * np.hanning(NFFT).astype(np.float32), axis=1))
    flux = np.maximum(0, np.diff(S, axis=0)).sum(1)
    return (flux - flux.mean()) / (flux.std() + 1e-9), SR / HOP


def tempo(flux, fps, lo=70, hi=180):
    """BPM by autocorrelation of the onset envelope.

    Same method as $MEDIA/build_catalog.py, including the part that matters:
    each candidate lag is scored together with its 2x and 4x multiples. Without
    that harmonic reinforcement a plain argmax drifts to a shorter lag and reports
    a wrong, non-octave tempo (166.7 instead of 113.5 on a track measured here).
    """
    ac = np.correlate(flux, flux, "full")[len(flux) - 1:]

    def at(lag):
        i = int(lag)
        if i + 1 >= len(ac):
            return 0.0
        return float(ac[i] + (ac[i + 1] - ac[i]) * (lag - i))

    best, bpm_best = -1e18, None
    for bpm in np.arange(lo, hi + 0.01, 0.05):
        lag = 60.0 / bpm * fps
        v = at(lag) + 0.5 * at(lag * 2) + 0.5 * at(lag * 4)
        if v > best:
            best, bpm_best = v, float(bpm)
    return round(bpm_best, 1)


def downbeats(flux, fps, bpm, after, limit=60.0):
    """Scan bar-grid phases; keep the one whose downbeats carry the most onset energy."""
    bar = 4 * 60.0 / bpm
    best_phase, best_score = 0.0, -1e9
    for ph in np.arange(0, bar, 0.01):
        idx = (np.arange(ph, limit, bar) * fps).astype(int)
        idx = idx[(idx > 0) & (idx < len(flux))]
        if not len(idx):
            continue
        s = float(flux[idx].mean())
        if s > best_score:
            best_phase, best_score = float(ph), s
    grid = [t for t in np.arange(best_phase, limit, bar) if t >= after]
    return bar, best_phase, best_score, grid


if __name__ == "__main__":
    path = sys.argv[1]
    bpm = float(sys.argv[2]) if len(sys.argv) > 2 else None
    after = float(sys.argv[3]) if len(sys.argv) > 3 else 6.0

    flux, fps = onset_flux(path)
    if bpm is None:
        bpm = tempo(flux, fps)
    bar, phase, score, grid = downbeats(flux, fps, bpm, after)

    print(f"bpm      = {bpm:.1f}")
    print(f"bar      = {bar:.4f}s   (put this BPM in src/theme.ts)")
    print(f"phase    = {phase:.3f}s   score = {score:.2f}")
    print("downbeats: " + ", ".join(f"{t:.3f}" for t in grid[:10]))
