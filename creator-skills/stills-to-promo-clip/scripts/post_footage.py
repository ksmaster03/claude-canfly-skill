"""Film finish for the footage v2 frames, then encode each shot to MP4.

  python post_footage.py [id-filter]

frames_v2/<id>/f_####.jpg  ->  clips_v2/<id>.mp4  (+ clips_v2/mission_possible_reel_v2.mp4)
Adds what the renderer does not: lens vignette, a gentle grade (lifted blacks, cool shadows,
warm highlights) and moving film grain that is stronger in the mid-tones.
"""
import sys, os, glob
import numpy as np
import cv2, av

HERE = os.path.dirname(os.path.abspath(__file__))
SRC, OUT = os.path.join(HERE, "frames_v2"), os.path.join(HERE, "clips_v2")
FILT = sys.argv[1] if len(sys.argv) > 1 else ""
FPS, W, H = 24, 1920, 1080
os.makedirs(OUT, exist_ok=True)
rng = np.random.default_rng(2026)

yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
rad = np.sqrt(((xx - W / 2) / (W / 2)) ** 2 + ((yy - H / 2) / (H / 2)) ** 2) / np.sqrt(2)
VIGNETTE = (1.0 - 0.34 * np.clip(rad, 0, 1) ** 2.4)[..., None]
# a few pre-made grain plates, cycled and flipped, are indistinguishable from fresh noise and much faster
PLATES = [cv2.GaussianBlur(rng.standard_normal((H, W)).astype(np.float32), (0, 0), 0.8) for _ in range(8)]


def finish(bgr, i):
    x = bgr.astype(np.float32) / 255.0
    x = x * VIGNETTE
    luma = x.mean(2, keepdims=True)
    x[..., 0] += 0.012 * (1 - luma[..., 0])           # blue into the shadows
    x[..., 2] += 0.010 * luma[..., 0]                 # red into the highlights
    x = 0.018 + x * 0.982                             # lifted blacks
    g = PLATES[i % len(PLATES)]
    if (i // len(PLATES)) % 2:
        g = g[::-1, ::-1]
    x += (g * 0.045)[..., None] * (0.35 + 1.3 * luma * (1 - luma) * 4)
    return (np.clip(x, 0, 1) * 255).astype(np.uint8)


def encoder(path):
    c = av.open(path, "w")
    st = c.add_stream("libx264", rate=FPS)
    st.width, st.height, st.pix_fmt = W, H, "yuv420p"
    st.options = {"crf": "15", "preset": "medium"}
    return c, st


def write(c, st, bgr):
    fr = av.VideoFrame.from_ndarray(bgr, format="bgr24")
    for pkt in st.encode(fr):
        c.mux(pkt)


shots = sorted(d for d in os.listdir(SRC) if os.path.isdir(os.path.join(SRC, d)) and FILT in d)
reel = encoder(os.path.join(OUT, "mission_possible_reel_v2.mp4")) if not FILT else None
k = 0
for sid in shots:
    files = sorted(glob.glob(os.path.join(SRC, sid, "f_*.jpg")))
    c, st = encoder(os.path.join(OUT, sid + ".mp4"))
    for f in files:
        img = finish(cv2.imread(f), k)
        k += 1
        write(c, st, img)
        if reel:
            write(reel[0], reel[1], img)
    for pkt in st.encode():
        c.mux(pkt)
    c.close()
    print(f"{sid}: {len(files)} frames")
if reel:
    for pkt in reel[1].encode():
        reel[0].mux(pkt)
    reel[0].close()
    print("reel:", k, "frames")
