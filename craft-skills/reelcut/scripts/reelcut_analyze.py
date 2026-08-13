#!/usr/bin/env python
"""
reelcut_analyze.py — forensic teardown of a short vertical ad / reel.

Measures everything you need to reverse-engineer an edit:
  cuts, shot list, push-in, freeze frames, motion peaks, colour grade,
  loudness (EBU R128), stereo width, VO pauses & speaking rate,
  SFX inventory (needs --stems), music-bed presence test.

Usage:
    python reelcut_analyze.py VIDEO [--work DIR] [--stems] [--no-frames]

--stems runs demucs (htdemucs, two-stem) to split VO from everything else.
        Costs ~1s of CPU per second of audio. It is the ONLY decisive test for
        "is there a music bed or just SFX" — use it whenever sound matters.

Requires on PATH: ffmpeg, ffprobe.  Python: numpy, scipy.  Optional: demucs.
"""
import argparse
import json
import os
import subprocess
import sys

import numpy as np
import scipy.io.wavfile as wav
import scipy.signal as sig

GW, GH = 90, 160        # grayscale analysis resolution
CW, CH = 120, 214       # rgb analysis resolution


def run(args, **kw):
    """Always an argv list — never shell=True. Paths here come from the user and
    routinely contain spaces; a shell string would also let ';' or '"' inject."""
    return subprocess.run(args, capture_output=True, text=True,
                          encoding="utf-8", errors="replace", **kw)


def hdr(t):
    print(f"\n{'=' * 66}\n{t}\n{'=' * 66}")


def db(v):
    return 20 * np.log10(np.maximum(v, 1e-9))


def find_cuts(d, fps):
    """A real cut is a spike towering over its neighbours.
    Sustained high diff is fast motion, not an edit."""
    out = []
    for i, val in enumerate(d):
        if val < 18:
            continue
        lo, hi = max(0, i - 3), min(len(d), i + 4)
        nb = np.concatenate([d[lo:i], d[i + 1:hi]])
        if len(nb) and val > 2.0 * nb.mean():
            out.append((i + 1) / fps)
    return out


# ---------------------------------------------------------------- container
def probe(video):
    hdr("1. CONTAINER")
    r = run(["ffprobe", "-v", "error", "-show_format", "-show_streams",
             "-print_format", "json", video])
    d = json.loads(r.stdout)
    v = next(s for s in d["streams"] if s["codec_type"] == "video")
    a = next((s for s in d["streams"] if s["codec_type"] == "audio"), None)
    num, den = v["r_frame_rate"].split("/")
    fps = float(num) / float(den)
    print(f"  duration   {float(d['format']['duration']):.2f} s")
    print(f"  video      {v['codec_name']} {v.get('profile','')} "
          f"{v['width']}x{v['height']} {fps:g} fps  {int(v.get('bit_rate',0))/1000:.0f} kbps")
    print(f"  aspect     {v.get('display_aspect_ratio','?')}   pix {v['pix_fmt']}  {v.get('color_space','?')}")
    if a:
        br = int(a.get("bit_rate", 0)) / 1000
        print(f"  audio      {a['codec_name']} {a.get('profile','')} {a['sample_rate']} Hz "
              f"{a['channels']}ch  {br:.0f} kbps")
        if "HE-AAC" in str(a.get("profile", "")) or 0 < br < 96:
            print("  !! low-bitrate/HE-AAC => this is a PLATFORM TRANSCODE, not a master.")
            print("     Content above ~10 kHz is synthesised SBR. Treat HF numbers as directional.")
    return float(d["format"]["duration"]), fps


# ------------------------------------------------------------------ picture
def dump_frames(video, work):
    g = os.path.join(work, "gray.raw")
    c = os.path.join(work, "rgb.raw")
    run(["ffmpeg", "-hide_banner", "-v", "error", "-i", video,
         "-vf", f"scale={GW}:{GH}", "-pix_fmt", "gray", "-f", "rawvideo", g, "-y"])
    run(["ffmpeg", "-hide_banner", "-v", "error", "-i", video,
         "-vf", f"scale={CW}:{CH},format=rgb24", "-f", "rawvideo", c, "-y"])
    return g, c


def picture(gray_path, fps):
    v = np.fromfile(gray_path, dtype=np.uint8).reshape(-1, GH, GW).astype(np.float32)
    d = np.abs(np.diff(v, axis=0)).mean(axis=(1, 2))
    cuts = find_cuts(d, fps)

    hdr("2. CUTS  (isolated frame-diff spikes = hard cuts)")
    for t in cuts:
        print(f"  cut @ {t:7.3f} s   diff={d[int(round(t*fps))-1]:6.1f}")
    print(f"  -> {len(cuts)} cuts / {len(cuts)+1} shots")

    hdr("3. SHOT LIST + FRAMING DRIFT  (bright-area growth ~ zoom/dolly)")
    print("  NOTE: proxy only. An object entering or leaving frame moves this number as"
          "\n  much as a real zoom does — eyeball the contact sheet before you trust a row.")
    bounds = [0.0] + cuts + [len(v) / fps]
    shots = []
    for a, b in zip(bounds, bounds[1:]):
        if b - a < 0.15:
            continue
        idx = [int(t * fps) for t in np.linspace(a + 0.05, b - 0.05, 6) if int(t * fps) < len(v)]
        if len(idx) < 2:
            continue
        area = [int((v[i] > 110).sum()) for i in idx]
        growth = area[-1] / max(area[0], 1)
        move = "push-in" if growth > 1.25 else ("pull-out" if growth < 0.8 else "static-ish")
        print(f"  {a:6.3f}-{b:6.3f}s  ({b-a:5.2f}s)  brightArea {area[0]:5d}->{area[-1]:5d}"
              f"  x{growth:4.2f}  {move}")
        shots.append((a, b))
    if shots:
        print(f"  -> avg shot length {np.mean([b - a for a, b in shots]):.2f} s")

    hdr("4. FREEZE / DUPLICATE FRAMES  (speed ramps, held frames)")
    runs, cur = [], None
    for i, val in enumerate(d):
        if val < 0.35:
            cur = i if cur is None else cur
        elif cur is not None:
            runs.append((cur, i)); cur = None
    if cur is not None:
        runs.append((cur, len(d)))
    found = [(a, b) for a, b in runs if b - a >= 2]
    for a, b in found:
        print(f"  {a/fps:6.3f}-{(b+1)/fps:6.3f}s  ({b-a+1} frames held)")
    if not found:
        print("  none — no freeze frames, no speed ramps")

    hdr("5. FAST-MOTION BURSTS  (whips / rapid graphic animation, not cuts)")
    inb, s, any_ = False, 0, False
    for i, val in enumerate(d):
        high = val > 12
        if high and not inb:
            inb, s = True, i
        elif not high and inb:
            inb = False
            if i - s >= 4:
                a, b = s / fps, i / fps
                if not any(a - 0.15 <= c <= b + 0.15 for c in cuts):
                    print(f"  {a:6.3f}-{b:6.3f}s  ({(i-s)/fps:.2f}s sustained motion)")
                    any_ = True
    if not any_:
        print("  none")
    return cuts


def colour(rgb_path, fps):
    hdr("6. COLOUR GRADE")
    v = np.fromfile(rgb_path, dtype=np.uint8).reshape(-1, CH, CW, 3).astype(np.float32)
    R, G, B = v[..., 0], v[..., 1], v[..., 2]
    Y = 0.2126 * R + 0.7152 * G + 0.0722 * B
    print(f"  luma      p1={np.percentile(Y,1):5.1f}  median={np.percentile(Y,50):5.1f}  "
          f"p99={np.percentile(Y,99):5.1f}  mean={Y.mean():5.1f}")
    crushed = (Y < 25).mean() * 100
    print(f"  crushed   {crushed:.1f}% of pixels below Y=25"
          f"{'   <- heavy crushed-black look' if crushed > 30 else ''}")
    sh_, hi = Y < 25, Y > 200
    if sh_.any():
        print(f"  shadows   R={R[sh_].mean():5.1f} G={G[sh_].mean():5.1f} B={B[sh_].mean():5.1f}")
    if hi.any():
        print(f"  highlight R={R[hi].mean():5.1f} G={G[hi].mean():5.1f} B={B[hi].mean():5.1f}")
    mx, mn = v.max(3), v.min(3)
    sat = np.where(mx > 0, (mx - mn) / np.maximum(mx, 1), 0)
    print(f"  satur.    mean={sat.mean():.3f}  p90={np.percentile(sat,90):.3f}")

    hdr("7. ON-SCREEN GRAPHICS  (white-outlined-text proxy, per 0.5 s)")
    white = ((mx > 225) & (mn > 200)).sum(axis=(1, 2))
    step = max(1, int(round(fps / 2)))
    for i in range(0, len(v), step):
        print(f"  t={i/fps:5.2f}  whitePx={white[i]:5d} {'#' * min(40, int(white[i] / 40))}")


# -------------------------------------------------------------------- audio
def extract_audio(video, work):
    w48 = os.path.join(work, "a48.wav")
    run(["ffmpeg", "-hide_banner", "-v", "error", "-i", video, "-vn",
         "-acodec", "pcm_s16le", "-ar", "48000", w48, "-y"])
    return w48


def loudness(video):
    hdr("8. LOUDNESS (EBU R128)")
    r = run(["ffmpeg", "-hide_banner", "-i", video,
             "-af", "ebur128=peak=true", "-f", "null", "-"])
    tail = r.stderr.split("Summary:")[-1] if "Summary:" in r.stderr else ""
    lra = None
    for line in tail.splitlines():
        line = line.strip()
        if line.startswith(("I:", "LRA:", "Peak:", "Threshold:", "LRA low:", "LRA high:")):
            print("  " + line)
            if line.startswith("LRA:"):
                lra = float(line.split()[1])
    if lra is not None:
        if lra < 3:
            print("  !! LRA under 3 LU — compressed flat. Punchy on a phone, fatiguing on headphones.")
        elif lra > 9:
            print("  !! LRA over 9 LU — quiet parts will vanish in a noisy environment.")


def stereo(w48):
    hdr("9. STEREO WIDTH")
    sr, x = wav.read(w48)
    x = x.astype(np.float64) / 32768
    if x.ndim == 1:
        print("  mono file")
        return
    L, R = x[:, 0], x[:, 1]
    w = int(sr * 0.5)
    cs, sm = [], []
    for i in range(len(L) // w):
        a, b = L[i * w:(i + 1) * w], R[i * w:(i + 1) * w]
        if np.std(a) < 1e-6 or np.std(b) < 1e-6:
            continue
        cs.append(np.corrcoef(a, b)[0, 1])
        m_, s_ = (a + b) / 2, (a - b) / 2
        sm.append(db(np.sqrt((s_ ** 2).mean())) - db(np.sqrt((m_ ** 2).mean())))
    if not cs:
        print("  silent")
        return
    print(f"  L/R correlation  min={min(cs):.2f}  median={np.median(cs):.2f}  max={max(cs):.2f}")
    print(f"  side below mid   median={np.median(sm):.1f} dB")
    if np.median(cs) > 0.85:
        print("  -> effectively MONO. Deliberate for single-phone-speaker playback.")


def stems(w48, work):
    out = os.path.join(work, "stems")
    base = os.path.join(out, "htdemucs", os.path.splitext(os.path.basename(w48))[0])
    if not os.path.exists(os.path.join(base, "vocals.wav")):
        print("\n  running demucs (htdemucs, two-stem, CPU) ...")
        r = run([sys.executable, "-m", "demucs", "-n", "htdemucs",
                 "--two-stems=vocals", "-d", "cpu", "-o", out, w48])
        if not os.path.exists(os.path.join(base, "vocals.wav")):
            print("  !! demucs failed:", (r.stderr or r.stdout)[-300:])
            return None, None

    def ld(p):
        sr, y = wav.read(p)
        y = y.astype(np.float64) / (32768 if y.dtype == np.int16 else 1)
        return sr, (y.mean(1) if y.ndim > 1 else y)
    return ld(os.path.join(base, "vocals.wav")), ld(os.path.join(base, "no_vocals.wav"))


def voice(sr, voc):
    hdr("10. VOICE — pauses & delivery")
    w = int(sr * 0.03)
    d = db(np.array([np.sqrt((voc[i * w:(i + 1) * w] ** 2).mean())
                     for i in range(len(voc) // w)]))
    inside, s, tot, gaps = False, 0, 0.0, []
    for i, val in enumerate(d):
        if val < -38 and not inside:
            inside, s = True, i
        elif val >= -38 and inside:
            inside = False
            dur = (i - s) * 0.03
            if dur >= 0.09:
                gaps.append((s * 0.03, i * 0.03, dur)); tot += dur
    for a, b, dur in gaps:
        print(f"  gap {a:6.2f}-{b:6.2f}s  ({dur*1000:.0f} ms)")
    total = len(voc) / sr
    print(f"  -> {len(gaps)} pauses, silence {tot:.2f}s of {total:.2f}s = {tot/total*100:.1f}%")
    if tot / total < 0.12:
        print("     tight cut — every breath removed")
    env = sig.savgol_filter(sig.decimate(np.abs(sig.hilbert(voc)), 48, ftype="fir"), 51, 2)
    pk, _ = sig.find_peaks(env, height=env.max() * 0.12, distance=90)
    print(f"  -> {len(pk)} syllable-like peaks = {len(pk)/total:.2f}/s ({len(pk)/total*60:.0f}/min)")
    return [(a, b) for a, b, _ in gaps]


def bedtest(sr, bed, voc):
    hdr("11. MUSIC BED vs SFX  (the decisive test)")
    hb = sig.sosfilt(sig.butter(4, [300, 8000], btype="band", fs=sr, output="sos"), bed)
    w = int(sr * 0.05)
    n = len(bed) // w
    r = np.array([np.sqrt((bed[i * w:(i + 1) * w] ** 2).mean()) for i in range(n)])
    rh = np.array([np.sqrt((hb[i * w:(i + 1) * w] ** 2).mean()) for i in range(n)])

    lvl = db(np.median(rh[int(n * 0.2):int(n * 0.65)]))

    def env(x):
        return sig.decimate(np.abs(sig.hilbert(x)), 240, ftype="fir")   # -> 200 Hz
    eb, ev = env(bed), env(voc)
    m = min(len(eb), len(ev))
    corr = np.corrcoef(eb[:m], ev[:m])[0, 1]
    o = np.maximum(0, np.diff(eb)); o = o - o.mean()
    ac = np.correlate(o, o, "full")[len(o) - 1:]
    ac = ac / max(ac[0], 1e-12)
    lo, hi = int(60 / 200 * 200), int(60 / 60 * 200)     # 200..60 BPM in 5 ms samples
    lag = int(np.argmax(ac[lo:hi])) + lo
    print(f"  bed 300Hz-8kHz median (mid section): {lvl:6.1f} dB   (music bed lives ~-35..-25)")
    print(f"  corr(bed env, VO env):               {corr:6.3f}   (>0.5 => it is VO leakage)")
    print(f"  beat autocorrelation:                {ac[lag]:6.3f} @ {60/(lag/200):.0f} BPM")
    if lvl < -33 and ac[lag] < 0.2:
        print("  ==> NO MUSIC BED. Track = voice + discrete SFX + room tone.")
    else:
        print("  ==> a music bed IS present.")

    hdr("12. SFX INVENTORY")
    i, events = 0, []
    while i < n:
        if db(r[i]) > -26:
            j = i
            while j < n and db(r[j]) > -32:
                j += 1
            pk = i + int(np.argmax(r[i:j]))
            if db(r[pk]) > -22:
                events.append((i * 0.05, j * 0.05, db(r[pk]), pk * 0.05))
            i = max(j, i + 1)
        else:
            i += 1
    for a, b, l, p in events:
        seg = bed[int(a * sr):int(b * sr)]
        f_, P = sig.welch(seg, sr, nperseg=min(4096, max(256, len(seg))))

        def bnd(lo_, hi_):
            k = (f_ >= lo_) & (f_ < hi_)
            return 10 * np.log10(np.mean(P[k]) + 1e-14) if k.any() else -99
        print(f"  {a:6.2f}-{b:6.2f}s ({(b-a)*1000:5.0f} ms)  peak {l:6.1f} dB @{p:5.2f}s   "
              f"sub{bnd(20,120):6.1f} low{bnd(120,500):6.1f} "
              f"mid{bnd(500,2000):6.1f} hi{bnd(2000,8000):6.1f}")
    print(f"  -> {len(events)} SFX events above -22 dB")
    return events


def sync(cuts, gaps, sfx):
    hdr("13. SYNC — do cuts land on breaths?  do SFX land on cuts?")
    if gaps and cuts:
        hit = 0
        for c in cuts:
            g = next((g for g in gaps if g[0] - 0.12 <= c <= g[1] + 0.12), None)
            if g:
                hit += 1
                print(f"  cut {c:6.3f}s  IN VO gap {g[0]:.2f}-{g[1]:.2f}s   (cut on the breath)")
            else:
                print(f"  cut {c:6.3f}s  over continuous speech      (B-roll insert)")
        print(f"  -> {hit}/{len(cuts)} cuts land in a pause")
    if sfx and cuts:
        on = sum(1 for _, _, _, p in sfx if any(abs(p - c) < 0.25 for c in cuts))
        print(f"  -> {on}/{len(sfx)} SFX sit on a cut; {len(sfx)-on} sit elsewhere "
              f"(= synced to graphic entry, not to the edit)")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("video")
    ap.add_argument("--work", default=None)
    ap.add_argument("--stems", action="store_true", help="run demucs (needed for sections 10-13)")
    ap.add_argument("--no-frames", action="store_true", help="skip picture analysis")
    a = ap.parse_args()

    video = os.path.abspath(a.video)
    work = a.work or os.path.join(os.path.dirname(video), "_reelcut")
    os.makedirs(work, exist_ok=True)
    print(f"video: {video}\nwork : {work}")

    _, fps = probe(video)
    cuts = []
    if not a.no_frames:
        g, c = dump_frames(video, work)
        cuts = picture(g, fps)
        colour(c, fps)

    w48 = extract_audio(video, work)
    loudness(video)
    stereo(w48)

    if a.stems:
        vo, bd = stems(w48, work)
        if vo:
            gaps = voice(*vo)
            ev = bedtest(bd[0], bd[1], vo[1])
            sync(cuts, gaps, ev)
    else:
        print("\n(pass --stems for voice/SFX/music-bed analysis — it is the interesting half)")

    print(f"\nDone. Intermediates in {work}")


if __name__ == "__main__":
    main()
