"""Map a song's structure by energy so MV scenes can be cut onto real section changes.

    python sections.py <track.mp3> [bpm] [phase]

Prints a per-bar RMS profile (dBFS) plus the bars where energy jumps or drops hard.
Loud sustained runs read as choruses; a deep dip near the back half reads as the bridge.
"""
import subprocess
import sys

import numpy as np

SR = 22050


def pcm(path):
    raw = subprocess.run(
        ["ffmpeg", "-v", "error", "-i", path, "-ac", "1", "-ar", str(SR), "-f", "f32le", "-"],
        capture_output=True,
    ).stdout
    return np.frombuffer(raw, dtype=np.float32)


def main():
    path = sys.argv[1]
    bpm = float(sys.argv[2]) if len(sys.argv) > 2 else 169.4
    phase = float(sys.argv[3]) if len(sys.argv) > 3 else 0.30
    bar = 4 * 60.0 / bpm

    x = pcm(path)
    dur = len(x) / SR
    nbars = int((dur - phase) / bar)

    rms = []
    for i in range(nbars):
        a = int((phase + i * bar) * SR)
        b = int((phase + (i + 1) * bar) * SR)
        seg = x[a:b]
        r = float(np.sqrt(np.mean(seg ** 2))) if len(seg) else 1e-9
        rms.append(20 * np.log10(max(r, 1e-9)))
    rms = np.array(rms)

    print(f"duration = {dur:.2f}s   bar = {bar:.4f}s   bars = {nbars}")
    print(f"loudest bar = {rms.max():.1f} dB   quietest = {rms.min():.1f} dB")

    # Smooth over 2 bars so a single crash cymbal doesn't read as a section.
    k = np.convolve(rms, np.ones(3) / 3, mode="same")
    print("\nper-bar dBFS (bar: time  level  meter)")
    for i, (v, s) in enumerate(zip(rms, k)):
        t = phase + i * bar
        meter = "#" * max(0, int((v + 40) / 1.2))
        mark = ""
        if i > 0:
            d = s - k[i - 1]
            if d > 1.8:
                mark = "  <== ENERGY UP"
            elif d < -1.8:
                mark = "  <== ENERGY DOWN"
        print(f"{i:3d}: {t:7.2f}s {v:6.1f} {meter}{mark}")


if __name__ == "__main__":
    main()
