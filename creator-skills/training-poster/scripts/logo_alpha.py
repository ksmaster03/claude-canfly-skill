# -*- coding: utf-8 -*-
"""โลโก้ที่เจนบนพื้นดำล้วน → PNG พื้นใส (color-to-alpha จากดำ ขอบ antialias ถูกต้อง)
ใช้: python logo_alpha.py <logo-on-black.png> <out.png>
เหตุผล: GPT เจนพื้นใสไม่ได้ แต่สั่ง "pure solid black #000000" ได้เสมอ วิธีนี้วางบนพื้นเข้มแล้วเหมือนต้นฉบับเป๊ะ"""
import sys
import numpy as np
from PIL import Image
a = np.asarray(Image.open(sys.argv[1]).convert("RGB")).astype(np.float32) / 255
a[a < 0.035] = 0
al = a.max(axis=2)
rgb = np.where(al[..., None] > 0, a / np.maximum(al[..., None], 1e-6), 0)
im = Image.fromarray((np.dstack([rgb, al]) * 255).round().astype(np.uint8), "RGBA")
bb = im.getbbox(); im = im.crop((bb[0] - 20, bb[1] - 20, bb[2] + 20, bb[3] + 20)); im.save(sys.argv[2])
print("saved", sys.argv[2], im.size)
