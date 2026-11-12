#!/usr/bin/env python
"""
pc_build.py — assemble a framed promo clip from an edit list whose cut points are
written in BEATS, so every cut lands on the music grid by construction.

  python pc_build.py edit.json -o out.mp4 [--work DIR] [--keep]

edit.json (paths are relative to the json file, or absolute):
{
  "fps": 25,
  "size": [1080, 1080],
  "window": [1080, 567, 0, 264],        footage window inside the frame: w, h, x, y
  "frame": "frame.png",                 transparent-window overlay from pc_card.py (optional)
  "bg": "#04020f",                      colour under the window
  "card_bg": "#ffffff",                 colour behind logos / images that do not fill the window
  "music": "music.wav",
  "music_offset": 0.0,                  seconds into the music file where the clip starts
  "grid": {"bpm": 105.0, "first_downbeat": -0.026},    from pc_beat.py grid (music-file time)
  "grade": "navy",                      "navy" | "none" | a raw ffmpeg filter string
  "loudness": {"I": -14, "TP": -1.5},
  "end": 84,                            beat where the clip ends
  "shots": [
    {"at": 0,  "src": "cards/open.png"},
    {"at": 4,  "src": "footage/a.mp4", "in": 12.0, "fx": "flash"},
    {"at": 14, "run": ["logos/1.png", "logos/2.png"], "until": 16},
    {"at": 16, "src": "cards/title.png", "fx": "rgb"}
  ]
}

"at" counts beats from the music's first downbeat (0.5 = half a beat). The first shot
always starts at frame 0. A "run" spreads still images evenly up to "until" (the
logo flash-cut). fx works on the first frames of the incoming shot:
flash | punch | rgb | blur.

Stills are fitted inside the window on "card_bg"; per shot, "fit": "cover" fills the
window instead and "bg" overrides the colour. The window may have an odd size.
The build refuses to run when a source is too short for its shot, and ends by
checking that the planned cuts sit on their planned frames.
"""
import argparse
import concurrent.futures as cf
import json
import os
import re
import shutil
import subprocess
import sys

IMG = (".png", ".jpg", ".jpeg", ".webp", ".bmp")
# output levels measured on the reference clip: whites capped near (193,190,220),
# blacks lifted to navy (5,6,22). See references/digitech-teardown.md section 5.
NAVY = "colorlevels=romin=0.020:gomin=0.024:bomin=0.086:romax=0.757:gomax=0.745:bomax=0.863"

# Every segment leaves here as BT.709 limited-range 4:2:0 with identical tags.
# Mixed tags are not cosmetic: one segment tagged bt470bg among untagged ones made
# ffmpeg rebuild the filter graph mid-stream in the final pass, which silently threw
# away 112 frames and repeated the end card to fill the hole (exit code 0).
TO709 = ("scale=out_color_matrix=bt709:out_range=tv,format=yuv420p,"
         "setparams=range=tv:colorspace=bt709:color_primaries=bt709:color_trc=bt709")
TAGS = ["-color_range", "tv", "-colorspace", "bt709", "-color_primaries", "bt709", "-color_trc", "bt709"]
_MATRIX = {}


def in_matrix(path):
    """Colour matrix to read a source with. Tagged sources are trusted; untagged ones
    follow the usual convention (HD = BT.709, SD = BT.601)."""
    if path not in _MATRIX:
        r = run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries",
                 "stream=color_space,height", "-of", "json", path])
        try:
            st = json.loads(r.stdout)["streams"][0]
        except (ValueError, KeyError, IndexError):
            st = {}
        tagged = st.get("color_space") in ("bt709", "bt470bg", "smpte170m", "smpte240m", "fcc", "bt2020nc")
        _MATRIX[path] = "auto" if tagged else ("bt709" if int(st.get("height", 0) or 0) >= 720 else "bt601")
    return _MATRIX[path]


def run(args):
    """Always an argv list, never shell=True: paths contain spaces and Thai."""
    return subprocess.run(args, capture_output=True, text=True, encoding="utf-8", errors="replace")


def die(msg):
    sys.exit("pc_build: " + msg)


def col(c):
    return "0x" + c.lstrip("#") if c.startswith("#") else c


def fx_filter(name, W, H, fps):
    if not name or name == "none":
        return ""
    if name == "flash":         # white bloom fading over 3 frames
        return f",fade=t=in:st=0:d={3/fps:.4f}:color=white"
    if name == "punch":         # shot arrives 30 % zoomed in and settles in 6 frames
        z = "(1+0.30*max(0,1-n/6))"
        return f",scale=w='trunc({W}*{z}/2)*2':h='trunc({H}*{z}/2)*2':eval=frame,crop={W}:{H}"
    if name == "rgb":           # colour channels split sideways for 5 frames
        return ",format=rgb24,rgbashift=rh=-16:bh=16:enable='lt(n,5)'"
    if name == "blur":          # 4 soft frames, then sharp
        return ",gblur=sigma=14:enable='lt(n,4)'"
    die(f"unknown fx '{name}' (use flash, punch, rgb, blur)")


def count_frames(path):
    r = run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-count_packets",
             "-show_entries", "stream=nb_read_packets", "-of", "csv=p=0", path])
    try:
        return int(r.stdout.strip().split(",")[0])
    except ValueError:
        return 0


def main():
    for s in (sys.stdout, sys.stderr):
        try:
            s.reconfigure(encoding="utf-8")
        except Exception:
            pass
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("edit")
    ap.add_argument("-o", "--out", required=True)
    ap.add_argument("--work", help="folder for the per-shot segments (default: <out>_pcwork)")
    ap.add_argument("--keep", action="store_true", help="keep the work folder")
    a = ap.parse_args()

    base = os.path.dirname(os.path.abspath(a.edit))
    with open(a.edit, encoding="utf-8") as f:
        E = json.load(f)

    def P(p):
        return p if os.path.isabs(p) else os.path.normpath(os.path.join(base, p))

    fps = float(E.get("fps", 25))
    SW, SH = E.get("size", [1080, 1080])
    W, H, X, Y = E.get("window", [SW, SH, 0, 0])
    beat = 60.0 / float(E["grid"]["bpm"])
    d0 = float(E["grid"].get("first_downbeat", 0.0)) - float(E.get("music_offset", 0.0))

    def frame_of(b):
        return max(0, int(round((d0 + b * beat) * fps)))

    # ---- expand the shot list into (start_frame, src, in, fx, label)
    items = []
    for i, s in enumerate(E["shots"]):
        if "run" in s:
            if "until" not in s:
                die(f"shot {i}: a run needs 'until'")
            a0, a1, n = frame_of(s["at"]), frame_of(s["until"]), len(s["run"])
            if a1 - a0 < n:
                die(f"shot {i}: {n} images do not fit in {a1-a0} frames")
            for j, src in enumerate(s["run"]):
                items.append((a0 + int(round(j * (a1 - a0) / n)), src, 0.0, s.get("fx"), s, f"{i}.{j}"))
        else:
            items.append((frame_of(s["at"]), s["src"], float(s.get("in", 0.0)), s.get("fx"), s, str(i)))
    if not items:
        die("no shots")
    items[0] = (0,) + items[0][1:]
    total = frame_of(E["end"])
    starts = [it[0] for it in items] + [total]
    for k in range(len(items)):
        if starts[k + 1] - starts[k] < 1:
            die(f"shot {items[k][5]} would be {starts[k+1]-starts[k]} frames long: "
                f"its 'at' is not before the next shot (or 'end' is too early)")

    work = a.work or os.path.splitext(os.path.abspath(a.out))[0] + "_pcwork"
    os.makedirs(work, exist_ok=True)
    # yuv420p cannot hold an odd width or height (the reference window is 567 px tall):
    # segments are rendered one pixel larger and cut to the exact window in the final pass
    Ws, Hs = W + (W & 1), H + (H & 1)
    card_bg = col(E.get("card_bg", "#ffffff"))
    enc = ["-an", "-c:v", "libx264", "-preset", "ultrafast", "-crf", "12", "-g", "1", "-pix_fmt", "yuv420p"] + TAGS
    reset = "setpts=N/FRAME_RATE/TB"        # each segment starts at 0, one frame apart

    def render(k):
        start, src, tin, fx, s, label = items[k]
        n = starts[k + 1] - start
        seg = os.path.join(work, f"seg_{k:04d}.mp4")
        src_p = P(src)
        if not os.path.exists(src_p):
            return f"shot {label}: source not found: {src_p}"
        fxf = fx_filter(fx, Ws, Hs, fps)
        if src_p.lower().endswith(IMG):
            fit = s.get("fit", "contain")
            sc = (f"scale={Ws}:{Hs}:force_original_aspect_ratio=increase,crop={Ws}:{Hs}" if fit == "cover"
                  else f"scale={Ws}:{Hs}:force_original_aspect_ratio=decrease")
            # stills stay in RGB until the single, explicit BT.709 conversion (brand colours)
            fc = (f"[1:v]{sc}[i];[0:v]format=rgb24[b];[b][i]overlay=(W-w)/2:(H-h)/2:format=rgb,"
                  f"setsar=1{fxf},{reset},{TO709}[v]")
            cmd = ["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i",
                   f"color=c={col(s.get('bg', card_bg))}:s={Ws}x{Hs}:r={fps:g}",
                   "-loop", "1", "-framerate", f"{fps:g}", "-i", src_p,
                   "-filter_complex", fc, "-map", "[v]", "-frames:v", str(n)] + enc + [seg]
        else:
            vf = (f"fps={fps:g},scale={Ws}:{Hs}:force_original_aspect_ratio=increase:"
                  f"in_color_matrix={in_matrix(src_p)}:out_color_matrix=bt709:out_range=tv,"
                  f"crop={Ws}:{Hs},setsar=1{fxf},{reset},{TO709}")
            # camera files carry timecode/data streams that corrupt segment durations: video only
            cmd = ["ffmpeg", "-v", "error", "-y", "-ss", f"{tin:.3f}", "-i", src_p,
                   "-map", "0:v:0", "-dn", "-sn", "-vf", vf, "-frames:v", str(n)] + enc + [seg]
        r = run(cmd)
        got = count_frames(seg) if os.path.exists(seg) else 0
        if got != n:
            why = (r.stderr or "").strip().splitlines()[-1:] or ["source ran out of frames"]
            return (f"shot {label} ({os.path.basename(src_p)} in={tin:g}s): needed {n} frames, got {got}. "
                    f"{why[0]}  Pick an earlier 'in' or a longer source; a frozen last frame reads as a stutter.")
        return None

    print(f"{len(items)} shots, {total} frames = {total/fps:.2f} s @ {fps:g} fps, "
          f"beat = {beat*fps:.2f} frames ({E['grid']['bpm']} BPM)")
    with cf.ThreadPoolExecutor(max_workers=4) as ex:
        errs = [e for e in ex.map(render, range(len(items))) if e]
    if errs:
        die("\n  " + "\n  ".join(errs))

    lst = os.path.join(work, "list.txt")
    with open(lst, "w", encoding="utf-8") as f:
        for k in range(len(items)):
            f.write("file '" + os.path.join(work, f"seg_{k:04d}.mp4").replace("\\", "/").replace("'", "'\\''") + "'\n")

    dur = total / fps
    grade = E.get("grade", "navy")
    gf = NAVY if grade == "navy" else ("null" if grade in ("none", "", None) else grade)
    inputs = ["-f", "concat", "-safe", "0", "-i", lst]
    # The composite runs in RGB: the window may be odd-sized (no chroma subsampling to
    # fight) and every colour conversion is explicit. Frames are renumbered on the way
    # in so the encoder has no timestamp gap to pad or trim.
    # Packed rgb24, not planar gbrp: on ffmpeg 8.1.1 the yuv420p -> gbrp conversion left
    # the last 8 columns of a 1080-wide picture black (width not a multiple of 16).
    fc = [f"[0:v]setpts=N/({fps:g}*TB),scale=in_color_matrix=bt709:in_range=tv,format=rgb24,{gf},"
          f"crop={W}:{H}:0:0:exact=1[g]",
          f"color=c={col(E.get('bg', '#04020f'))}:s={SW}x{SH}:r={fps:g},format=rgb24[bg]",
          f"[bg][g]overlay={X}:{Y}:shortest=1:format=rgb[v1]"]
    last, idx = "v1", 1
    music = E.get("music")
    mi = None
    if music:
        inputs += ["-ss", f"{float(E.get('music_offset', 0.0)):.3f}", "-i", P(music)]
        mi, idx = idx, idx + 1
    if E.get("frame"):
        inputs += ["-loop", "1", "-framerate", f"{fps:g}", "-i", P(E["frame"])]
        fc.append(f"[{last}][{idx}:v]overlay=0:0:format=rgb[v2]")
        last = "v2"
    fc.append(f"[{last}]{TO709}[v]")
    maps = ["-map", "[v]"]
    if mi is not None:
        L = E.get("loudness", {})
        tI, tTP = float(L.get("I", -14)), float(L.get("TP", -1.5))
        pre = f"atrim=0:{dur:.3f},asetpts=PTS-STARTPTS,apad=whole_dur={dur:.3f},afade=t=out:st={max(0,dur-0.25):.3f}:d=0.25"
        m = run(["ffmpeg", "-hide_banner", "-nostats", "-ss", f"{float(E.get('music_offset', 0.0)):.3f}",
                 "-i", P(music), "-af", f"{pre},loudnorm=I={tI}:TP={tTP}:LRA=11:print_format=json",
                 "-vn", "-f", "null", "-"])
        js = re.findall(r"\{[^{}]*\"input_i\"[^{}]*\}", m.stderr, re.S)
        if not js:
            die("loudnorm measuring pass failed:\n" + m.stderr[-400:])
        v = json.loads(js[-1])
        ln = (f"loudnorm=I={tI}:TP={tTP}:LRA=11:measured_I={v['input_i']}:measured_TP={v['input_tp']}:"
              f"measured_LRA={v['input_lra']}:measured_thresh={v['input_thresh']}:offset={v['target_offset']}:linear=true")
        fc.append(f"[{mi}:a]{pre},{ln},aresample=48000[a]")
        maps += ["-map", "[a]", "-c:a", "aac", "-b:a", "192k"]
    cmd = (["ffmpeg", "-v", "error", "-y"] + inputs + ["-filter_complex", ";".join(fc)] + maps +
           ["-frames:v", str(total), "-t", f"{dur:.3f}", "-r", f"{fps:g}", "-c:v", "libx264",
            "-preset", "medium", "-crf", "18", "-pix_fmt", "yuv420p"] + TAGS + ["-movflags", "+faststart", a.out])
    r = run(cmd)
    if r.returncode != 0 or not os.path.exists(a.out):
        die("final pass failed:\n" + (r.stderr or "")[-800:])

    got = count_frames(a.out)
    print(f"wrote {a.out}: {got} frames ({got/fps:.2f} s)" + ("" if got == total else f"   !! expected {total}"))
    if mi is not None:
        e = run(["ffmpeg", "-hide_banner", "-nostats", "-i", a.out, "-af", "ebur128=peak=true", "-f", "null", "-"]).stderr
        tail = e[e.rfind("Summary:"):] if "Summary:" in e else ""
        g = lambda k: (re.search(k + r":\s+(-?[\d.]+)", tail) or [None, "?"])[1]
        print(f"loudness measured on the file: I {g('I')} LUFS, LRA {g('LRA')} LU, true peak {g('Peak')} dBTP")
    sys.dont_write_bytecode = True          # keep __pycache__ out of the skill folder
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import pc_beat
    det = {int(round(t * fps)) for t, _ in pc_beat.find_cuts(a.out, (W - (W & 1), H - (H & 1), X, Y), fps)[0]}
    plan = starts[1:-1]
    hit = sum(f in det for f in plan)
    late = max(range(-3, 4), key=lambda k: sum(f + k in det for f in plan))
    print(f"planned cuts found on their exact frame: {hit}/{len(plan)}"
          + ("" if hit >= 0.9 * len(plan) else
             f"   !! most cuts sit {late:+d} frames off: the timeline drifted, do not ship this"
             if late and sum(f + late in det for f in plan) > hit else
             "   (cuts between look-alike shots are not detectable; view a contact sheet)"))
    if not a.keep:
        shutil.rmtree(work, ignore_errors=True)
    print("next: python pc_beat.py check " + a.out)


if __name__ == "__main__":
    main()
