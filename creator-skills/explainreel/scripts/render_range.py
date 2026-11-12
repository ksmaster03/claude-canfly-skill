# -*- coding: utf-8 -*-
# เรนเดอร์ scenes.html ทีละเฟรมด้วย Playwright รันหลายตัวพร้อมกันได้แล้วต่อไฟล์ทีหลัง
# ใช้: python render_range.py <project_dir> shots <outdir> <t1> <t2> ...     ภาพนิ่งตามเวลา ใช้ตรวจก่อนเรนเดอร์จริง
#      python render_range.py <project_dir> <f0> <f1> <out.mp4>              f1 = -1 คือถึงเฟรมสุดท้าย
# ใช้ <project_dir>/scenes.html ถ้ามี (ฉบับที่ปรับธีมหรือเพิ่มชนิดฉาก) ไม่มีจึงใช้ฉบับของสกิล
import io
import json
import os
import subprocess
import sys

from playwright.sync_api import sync_playwright

FPS = 30
d = os.path.abspath(sys.argv[1]).replace("\\", "/")
skill = os.path.dirname(os.path.abspath(__file__)).replace("\\", "/")
html = f"{d}/scenes.html" if os.path.exists(f"{d}/scenes.html") else f"{skill}/scenes.html"
tl = json.load(io.open(f"{d}/timeline.json", encoding="utf-8"))
with sync_playwright() as p:
    b = p.chromium.launch()
    page = b.new_page(viewport={"width": 1080, "height": 1920})
    page.goto(f"file:///{html}")
    page.evaluate("document.fonts.ready")
    page.wait_for_timeout(400)
    page.evaluate("([tl,total]) => { window.TOTAL = total; window.init(tl); }", [tl["lines"], tl["total"]])
    if sys.argv[2] == "shots":
        out = sys.argv[3]
        os.makedirs(out, exist_ok=True)
        for i, t in enumerate(sys.argv[4:]):
            page.evaluate("t => window.renderAt(t)", float(t))
            page.screenshot(path=f"{out}/s{i:02d}.jpg", type="jpeg", quality=85)
    else:
        f0, f1, out = int(sys.argv[2]), int(sys.argv[3]), sys.argv[4]
        if f1 < 0:
            f1 = int(tl["total"] * FPS)
        ff = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "image2pipe", "-framerate", str(FPS), "-c:v", "mjpeg", "-i", "-",
                               "-c:v", "libx264", "-preset", "medium", "-crf", "17", "-pix_fmt", "yuv420p", out], stdin=subprocess.PIPE)
        for f in range(f0, f1):
            page.evaluate("t => window.renderAt(t)", f / FPS)
            ff.stdin.write(page.screenshot(type="jpeg", quality=95))
        ff.stdin.close()
        ff.wait()
    b.close()
print("done", sys.argv[2:5])
