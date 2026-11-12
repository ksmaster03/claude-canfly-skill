# -*- coding: utf-8 -*-
r"""ตัดพื้นหลังรูปคนจริงด้วย rembg สำหรับวางบนโปสเตอร์

ใช้:
  python cutout.py <in> <out.png> [--fill-body] [--remove-green] [--upscale 2] [--fade-from 0.64]

--fill-body     ชุดขาว/เสื้ออ่อนบนพื้นอ่อน (เช่นชุดเครื่องแบบสีขาว) โมเดลกินเนื้อเสื้อเป็นรู
                → รวม mask isnet-general-use + u2net_human_seg แล้วถมทุกแถวครึ่งล่างให้ทึบ
--remove-green  รูปโปรไฟล์ LinkedIn ที่มีกรอบ #OPENTOWORK: ลบพิกเซลเขียว แล้วเก็บเฉพาะก้อนที่ใหญ่สุด
                (ตัวอักษรขาวบนแถบหลุดไปเอง) + เติมรูภายใน
--upscale N     รูปเล็ก (<800px) ขยายก่อนตัด ขอบจะนุ่มกว่า
--fade-from F   ไล่ alpha เป็น 0 จากความสูงสัดส่วน F ลงไปถึง F+0.14 (ขอบกรอบรูปเดิมมักแข็ง)
ติดตั้ง: pip install "rembg[cpu]" scipy  (โหลดโมเดลครั้งแรก ~180MB ต่อโมเดล)
"""
import sys
import numpy as np
from PIL import Image, ImageFilter, ImageChops
from rembg import remove, new_session
from scipy import ndimage

a = sys.argv[1:]
def opt(name, default=None):
    if name in a:
        i = a.index(name); v = a[i + 1]; del a[i:i + 2]; return v
    return default
fill = "--fill-body" in a; green = "--remove-green" in a
a = [x for x in a if x not in ("--fill-body", "--remove-green")]
up = int(opt("--upscale", "1")); fade = opt("--fade-from")
src, out = a[0], a[1]

im = Image.open(src).convert("RGB")
if up > 1:
    im = im.resize((im.width * up, im.height * up), Image.LANCZOS)
m = remove(im, session=new_session("isnet-general-use"), only_mask=True, post_process_mask=True)
if fill:
    m = ImageChops.lighter(m, remove(im, session=new_session("u2net_human_seg"), only_mask=True, post_process_mask=True))
al = np.asarray(m).astype(np.float32)
if fill:
    h = al.shape[0]
    for y in range(int(h * 0.45), h):
        xs = np.where(al[y] > 128)[0]
        if len(xs): al[y, xs.min():xs.max() + 1] = 255
if green:
    px = np.asarray(im).astype(np.int32)
    g = (px[..., 1] > px[..., 0] + 18) & (px[..., 1] > px[..., 2] + 10)
    gm = Image.fromarray((g * 255).astype(np.uint8)).filter(ImageFilter.MaxFilter(9)).filter(ImageFilter.GaussianBlur(3))
    al = al * (1 - np.asarray(gm).astype(np.float32) / 255)
    lab, n = ndimage.label(al > 40)
    if n:
        sizes = ndimage.sum(np.ones_like(al), lab, range(1, n + 1))
        keep = ndimage.binary_fill_holes(lab == int(np.argmax(sizes)) + 1)
        al = np.where(keep, al, 0)
if fade:
    f = float(fade); h = al.shape[0]
    ramp = np.clip((h * (f + 0.14) - np.arange(h)) / (h * 0.14), 0, 1)[:, None]
    al = al * ramp
res = im.convert("RGBA"); res.putalpha(Image.fromarray(al.clip(0, 255).astype(np.uint8)))
res = res.crop(res.getbbox()); res.save(out)
chk = Image.new("RGBA", res.size, (30, 170, 60, 255)); chk.alpha_composite(res)
chk.convert("RGB").save(out.replace(".png", "-check.png"))
print("saved", out, res.size, "| ดูรอยตัดที่", out.replace(".png", "-check.png"))
