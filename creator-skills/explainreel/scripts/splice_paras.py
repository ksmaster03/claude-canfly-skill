# -*- coding: utf-8 -*-
# Kosin 17/10/2026 ต่อเสียงพากย์หลังแก้รายย่อหน้า: ย่อหน้าที่ดีตัดจากเสียงเดิม ย่อหน้าที่แก้ใช้ <para_dir>/pNN.mp3
# ใช้: python splice_paras.py <proj> <เสียงเดิม> <timeline เดิม> <para_dir> <id,id,...> [out.wav]
#   timeline เดิมต้องเป็นของเสียงเดิม (เก็บไว้ก่อนรัน align.py ใหม่) ตัดตรงช่วงเบาที่ยาวสุดก่อนต้นย่อหน้าถัดไป
#   ต่อด้วยช่องเงียบ 0.5 วิ (เท่า @หยุดพัก=500ms) ยกเว้นย่อหน้า 2 ที่ 0.3 วิ
import io, json, os, subprocess, sys
import numpy as np
import soundfile as sf

proj, old, old_tl, pdir, ids = sys.argv[1:6]
out_wav = sys.argv[6] if len(sys.argv) > 6 else os.path.join(proj, "vo", "voice_fixed.wav")
NEW = {int(x) for x in ids.split(",")}
SR = 24000
GAP = {2: 0.30}


def load(p):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", p, "-ac", "1", "-ar", str(SR), "-f", "f32le", "-"], capture_output=True, check=True).stdout
    return np.frombuffer(raw, dtype=np.float32).copy()


def env(x, hop=240):  # RMS ทุก 10 ms เป็น dB เทียบยอด
    n = len(x) // hop
    r = np.sqrt(np.mean(x[: n * hop].reshape(n, hop) ** 2, axis=1) + 1e-12)
    return 20 * np.log10(r / (np.max(r) + 1e-12))


def trim(x, th=-42, pad=0.03):
    e = env(x); on = np.where(e > th)[0]
    a = max(0, on[0] * 240 - int(pad * SR)); b = min(len(x), (on[-1] + 1) * 240 + int(pad * SR))
    return x[a:b]


full = load(old)
e = env(full)
tl = json.load(io.open(old_tl, encoding="utf-8"))
HEAD = tl.get("head", 0.4)
lines = tl["lines"]
starts = [0.0] + [l["subs"][0]["t"] - HEAD + 0.08 for l in lines[1:]]


def cut_at(t):
    lo, hi = int((t - 0.9) * 100), int((t + 0.25) * 100)
    q = e[lo:hi] < -38
    best, run, bs = (0, lo), 0, lo
    for i, v in enumerate(q):
        if v:
            if run == 0: bs = lo + i
            run += 1
            if run > best[0]: best = (run, bs)
        else:
            run = 0
    n, s = best
    if n < 8:
        sys.exit(f"ไม่เจอช่องเงียบก่อน {t:.2f}s ของเสียงเดิม")
    return (s + n / 2) / 100.0


bounds = [0.0] + [cut_at(t) for t in starts[1:]] + [len(full) / SR]
out = []
for k, l in enumerate(lines):
    lid = l["id"]
    if lid in NEW:
        seg = trim(load(os.path.join(pdir, f"p{lid:02d}.mp3"))); src = "ใหม่"
    else:
        seg = trim(full[int(bounds[k] * SR): int(bounds[k + 1] * SR)]); src = "เดิม %.2f-%.2f" % (bounds[k], bounds[k + 1])
    f = int(0.008 * SR)
    seg = seg.copy(); seg[:f] *= np.linspace(0, 1, f); seg[-f:] *= np.linspace(1, 0, f)
    if k > 0:
        out.append(np.zeros(int(GAP.get(lid, 0.50) * SR), dtype=np.float32))
    out.append(seg)
    print(lid, src, "%.2fs" % (len(seg) / SR))
v = np.concatenate(out)
sf.write(out_wav, v, SR)
print("total %.2fs ->" % (len(v) / SR), out_wav, "· ลบ <proj>/asr.json ก่อนรัน align.py ใหม่")
