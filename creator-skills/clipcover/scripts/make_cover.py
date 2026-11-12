# -*- coding: utf-8 -*-
# เรนเดอร์ปกคลิปแนวตั้ง 1080x1920 จาก <project_dir>/cover.json ด้วย Chromium (ตัวอักษรไทยไม่ลอย)
# ใช้: python make_cover.py <project_dir> [ชื่อไฟล์ config=cover.json]
# ได้: cover.jpg · cover_4x5.jpg (ครอปกลางแบบที่หน้าโปรไฟล์ตัด ไว้ตรวจว่าข้อความไม่หลุด) · cover_preview.jpg (ย่อไว้เปิดดู)
# cover.json:
#   { "layout": "split" หรือ "single", "img": ["img/a.jpg", "img/b.jpg"], "pos": ["42% 18%", "62% 50%"],
#     "tag": "FILM FILE #0002", "brand": "โกสินทร์ต้องบินได้",
#     "stamp": "ทั้งโลกแบน AI", "a": "บรรทัดนำ", "b": "คำใหญ่", "c": "บรรทัดรอง", "chip": "ชื่อเรื่อง · ประเด็น" }
#   ไม่ใส่ "credit" จะเติมจาก credits.json ของโปรเจกต์ให้เอง
import io
import json
import os
import shutil
import subprocess
import sys

from playwright.sync_api import sync_playwright

d = os.path.abspath(sys.argv[1]).replace("\\", "/")
name = sys.argv[2] if len(sys.argv) > 2 else "cover.json"
here = os.path.dirname(os.path.abspath(__file__))
cfg = json.load(io.open(f"{d}/{name}", encoding="utf-8"))
imgs = cfg["img"] if isinstance(cfg["img"], list) else [cfg["img"]]
for im in imgs:
    if not os.path.exists(f"{d}/{im}"):
        sys.exit(f"ไม่มีไฟล์ภาพ {im}")
if "credit" not in cfg and os.path.exists(f"{d}/credits.json"):
    cr = json.load(io.open(f"{d}/credits.json", encoding="utf-8"))
    miss = [im for im in imgs if im not in cr]
    if miss:
        print("WARN ภาพไม่มีใน credits.json ต้องใส่ credit เองและยืนยันสิทธิ์ใช้ภาพ:", miss)
    cfg["credit"] = " · ".join(dict.fromkeys(cr[im]["credit"].replace("ภาพ: ", "") for im in imgs if im in cr))
    if cfg["credit"]:
        cfg["credit"] = "ภาพ: " + cfg["credit"]
for k in ("stamp", "a", "b", "c", "chip"):
    if "—" in cfg.get(k, "") or "–" in cfg.get(k, ""):
        sys.exit(f"ช่อง {k} มีขีดยาว ให้ใช้เว้นวรรคหรือจุดกลางแทน")
if len(cfg.get("b", "")) > 12:
    print("WARN คำใหญ่ (b) ยาวเกิน 12 ตัวอักษร จะถูกย่อจนไม่เด่น ควรเหลือ 1 ถึง 2 คำ")

shutil.copyfile(f"{here}/cover.html", f"{d}/_cover.html")
out = f"{d}/{os.path.splitext(name)[0]}.jpg"
with sync_playwright() as p:
    b = p.chromium.launch()
    page = b.new_page(viewport={"width": 1080, "height": 1920})
    page.goto(f"file:///{d}/_cover.html")
    page.evaluate("document.fonts.ready")
    page.wait_for_timeout(400)
    box = page.evaluate("c => window.init(c)", cfg)
    page.wait_for_timeout(500)
    page.screenshot(path=out, type="jpeg", quality=93)
    b.close()
os.remove(f"{d}/_cover.html")
base = os.path.splitext(out)[0]
run = lambda a: subprocess.run(["ffmpeg", "-y", "-loglevel", "error"] + a, check=True)
run(["-i", out, "-vf", "crop=1080:1350:0:285", "-q:v", "3", f"{base}_4x5.jpg"])
run(["-i", out, "-vf", "scale=540:-1", "-q:v", "4", f"{base}_preview.jpg"])
print("ปก ->", out)
print(f"ข้อความอยู่ช่วง y {box['top']} ถึง {box['bottom']} ·", "อยู่ในเขตปลอดภัย 4:5" if box["safe"] else "‼ หลุดเขตปลอดภัย 4:5 (285 ถึง 1635) ให้ลดบรรทัดหรือปรับ \"top\"")
