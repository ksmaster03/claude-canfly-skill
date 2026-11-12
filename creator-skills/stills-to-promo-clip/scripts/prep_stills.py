"""Round 1+2 prep: upscale each still 2x and estimate its depth map.

  python prep_stills.py <models_dir> [id-filter]

Reads out/<id>.png, writes hires/<id>.png (2560x1440) and depth/<id>.npy (float32 0..1, 1 = near,
at 462x260) plus depth/<id>.png for a visual check. Models (ONNX, run on CPU):
  apisr_2x.onnx                 2x GAN upscaler (APISR RRDB)
  depth_anything_v2_small.onnx  monocular depth
"""
import sys, os, glob, time
import numpy as np
import onnxruntime as ort
from PIL import Image, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
MODELS = sys.argv[1]
FILT = sys.argv[2] if len(sys.argv) > 2 else ""
os.makedirs(os.path.join(HERE, "hires"), exist_ok=True)
os.makedirs(os.path.join(HERE, "depth"), exist_ok=True)

so = ort.SessionOptions()
so.intra_op_num_threads = 8
up = ort.InferenceSession(os.path.join(MODELS, "apisr_2x.onnx"), so, providers=["CPUExecutionProvider"])
dp = ort.InferenceSession(os.path.join(MODELS, "depth_anything_v2_small.onnx"), so, providers=["CPUExecutionProvider"])
UP_IN, DP_IN = up.get_inputs()[0].name, dp.get_inputs()[0].name
print("upscaler input", up.get_inputs()[0].shape, "| depth input", dp.get_inputs()[0].shape)

TILE, PAD = 256, 16


def upscale(img):
    """Tiled 2x upscale; tiles overlap by PAD so seams fall outside the kept centre."""
    a = np.asarray(img, dtype=np.float32) / 255.0
    h, w, _ = a.shape
    ap = np.pad(a, ((PAD, PAD + TILE), (PAD, PAD + TILE), (0, 0)), mode="reflect")
    out = np.zeros((h * 2, w * 2, 3), dtype=np.float32)
    for y in range(0, h, TILE):
        for x in range(0, w, TILE):
            t = ap[y:y + TILE + 2 * PAD, x:x + TILE + 2 * PAD].transpose(2, 0, 1)[None]
            r = up.run(None, {UP_IN: t})[0][0].transpose(1, 2, 0)
            r = r[PAD * 2:PAD * 2 + TILE * 2, PAD * 2:PAD * 2 + TILE * 2]
            hh, ww = min(TILE * 2, h * 2 - y * 2), min(TILE * 2, w * 2 - x * 2)
            out[y * 2:y * 2 + hh, x * 2:x * 2 + ww] = r[:hh, :ww]
    return Image.fromarray((np.clip(out, 0, 1) * 255).astype(np.uint8))


def depth(img):
    w, h = 924, 518                                   # multiples of 14, close to 16:9
    a = np.asarray(img.resize((w, h), Image.BICUBIC), dtype=np.float32) / 255.0
    a = (a - [0.485, 0.456, 0.406]) / [0.229, 0.224, 0.225]
    d = dp.run(None, {DP_IN: a.transpose(2, 0, 1)[None].astype(np.float32)})[0].squeeze()
    lo, hi = np.percentile(d, 1), np.percentile(d, 99)
    d = np.clip((d - lo) / (hi - lo + 1e-6), 0, 1)     # model gives inverse depth: larger = nearer
    im = Image.fromarray((d * 65535).astype(np.uint16)).resize((462, 260), Image.BICUBIC)
    # soften depth edges so displaced geometry stretches gently instead of tearing
    im = Image.fromarray((np.asarray(im) / 257).astype(np.uint8)).filter(ImageFilter.GaussianBlur(3))
    return np.asarray(im, dtype=np.float32) / 255.0


for path in sorted(glob.glob(os.path.join(HERE, "out", "s*.png"))):
    sid = os.path.basename(path)[:-4]
    if FILT and FILT not in sid:
        continue
    img = Image.open(path).convert("RGB")
    t0 = time.time()
    d = depth(img)
    np.save(os.path.join(HERE, "depth", sid + ".npy"), d)
    Image.fromarray((d * 255).astype(np.uint8)).save(os.path.join(HERE, "depth", sid + ".png"))
    t1 = time.time()
    hi = upscale(img).resize((2560, 1440), Image.LANCZOS)
    hi.save(os.path.join(HERE, "hires", sid + ".png"))
    print(f"{sid}: depth {t1-t0:.1f}s, upscale {time.time()-t1:.1f}s")
