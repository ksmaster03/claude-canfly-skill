# -*- coding: utf-8 -*-
# 18/10/2026 เรนเดอร์ intro.html ทีละเฟรม (24 fps) อ่านความยาวจาก TOTAL ในหน้า
# ใช้: python render.py shots <outdir> <t1> <t2> ...   ภาพนิ่งตามเวลา
#      python render.py <f0> <f1> <out.mp4>             f1 = -1 คือถึงเฟรมสุดท้าย
import os, subprocess, sys, time
from playwright.sync_api import sync_playwright

FPS = 24
d = os.path.dirname(os.path.abspath(__file__)).replace("\\", "/")
with sync_playwright() as p:
    b = p.chromium.launch(args=["--allow-file-access-from-files"])
    page = b.new_page(viewport={"width": 1920, "height": 1080})
    page.goto(f"file:///{d}/intro.html", wait_until="networkidle")
    print("ready", page.evaluate("window.ready()"), flush=True)
    if sys.argv[1] == "shots":
        out = sys.argv[2]
        os.makedirs(out, exist_ok=True)
        for i, t in enumerate(sys.argv[3:]):
            page.evaluate("t => window.renderAt(t)", float(t))
            page.screenshot(path=f"{out}/s{i:02d}_{float(t):05.2f}.jpg", type="jpeg", quality=88)
    else:
        f0, f1, out = int(sys.argv[1]), int(sys.argv[2]), sys.argv[3]
        if f1 < 0:
            f1 = round(page.evaluate("TOTAL") * FPS)
        ff = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "image2pipe", "-framerate", str(FPS), "-c:v", "mjpeg", "-i", "-",
                               "-c:v", "libx264", "-preset", "medium", "-crf", "16", "-pix_fmt", "yuv420p", out], stdin=subprocess.PIPE)
        t0 = time.time()
        for f in range(f0, f1):
            page.evaluate("t => window.renderAt(t)", f / FPS)
            ff.stdin.write(page.screenshot(type="jpeg", quality=94))
            if (f - f0) % 100 == 0:
                print(f"frame {f} ({time.time() - t0:.0f}s)", flush=True)
        ff.stdin.close()
        ff.wait()
    b.close()
print("done", sys.argv[1:4])
