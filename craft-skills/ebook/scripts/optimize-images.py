#!/usr/bin/env python
"""optimize-images.py <project-dir> — PNG จาก chatgpt-bridge -> JPEG บีบขนาด

ทำไมต้องมี: PNG ที่ได้จาก chatgpt-bridge หนัก ~1.5-2.3MB/รูป พอฝัง base64 ลง PDF
15 รูปทำให้ PDF บวมเป็น ~43MB. แปลงเป็น JPEG กว้างสุด 1500px quality 82
เหลือ ~4MB โดยตาแทบไม่เห็นต่าง. build-book.mjs จะเลือก .jpg ก่อน .png เอง

ใช้: python optimize-images.py /d/Project/<slug>-ebook
     python optimize-images.py <dir> --quality 88 --maxw 1800
"""
import argparse
import glob
import os
import sys

try:
    from PIL import Image
except ImportError:
    sys.exit("ต้องมี Pillow: pip install pillow")

ap = argparse.ArgumentParser()
ap.add_argument("project", nargs="?", default=".")
ap.add_argument("--quality", type=int, default=82)
ap.add_argument("--maxw", type=int, default=1500, help="ความกว้างสูงสุดของภาพหัวบท")
ap.add_argument("--cover-maxw", type=int, default=1200, help="ความกว้างสูงสุดของปก")
args = ap.parse_args()

img_dir = os.path.join(args.project, "images")
pngs = sorted(glob.glob(os.path.join(img_dir, "*.png")))
if not pngs:
    sys.exit(f"ไม่พบ .png ใน {img_dir}")

before = after = 0
for p in pngs:
    im = Image.open(p).convert("RGB")
    maxw = args.cover_maxw if "cover" in os.path.basename(p) else args.maxw
    if im.width > maxw:
        im = im.resize((maxw, round(im.height * maxw / im.width)), Image.LANCZOS)
    out = p[:-4] + ".jpg"
    im.save(out, "JPEG", quality=args.quality, optimize=True, progressive=True)
    b, a = os.path.getsize(p), os.path.getsize(out)
    before += b
    after += a
    print(f"{os.path.basename(out):<14} {b // 1024:>6}KB -> {a // 1024:>5}KB")

print(f"\nรวม {before // 1024 // 1024}MB -> {after // 1024 // 1024}MB "
      f"({len(pngs)} รูป, เหลือ {after * 100 // before}%)")
print("ต่อไป: node build-book.mjs")
