# -*- coding: utf-8 -*-
# เรนเดอร์ engine.html ทีละเฟรมด้วย Playwright สำหรับ /salereelclip
# ใช้:
#   python sr_render.py <proj> shots <outdir> <t1> <t2> ... [--guides]   ภาพนิ่งตามเวลา (--guides วาดเขต UI ของ Reels ทับ)
#   python sr_render.py <proj> range <f0> <f1> <out.mp4>                 ช่วงเฟรม (f1 = -1 คือถึงเฟรมสุดท้าย)
#   python sr_render.py <proj> full <out.mp4> [jobs=3]                   แบ่งช่วงรันพร้อมกันแล้วต่อไฟล์ให้ (ภาพอย่างเดียว ไม่มีเสียง)
# อ่าน <proj>/clip.json (bg, theme, head) และ <proj>/timeline.json (จาก align.py หรือ sr_preview.py)
# ใช้ <proj>/engine.html ถ้ามี (ฉบับที่ปรับเอง) ไม่มีจึงใช้ฉบับของสกิล
import io
import json
import os
import subprocess
import sys

FPS = 30
skill = os.path.dirname(os.path.dirname(os.path.abspath(__file__))).replace("\\", "/")
d = os.path.abspath(sys.argv[1]).replace("\\", "/")
mode = sys.argv[2]
html = f"{d}/engine.html" if os.path.exists(f"{d}/engine.html") else f"{skill}/scripts/engine.html"
clip = json.load(io.open(f"{d}/clip.json", encoding="utf-8"))
tl = json.load(io.open(f"{d}/timeline.json", encoding="utf-8"))
total = tl["total"]


def fonts_css():
    fd = f"{skill}/assets/fonts"
    faces = [("Regular", 400, "normal"), ("Medium", 500, "normal"), ("SemiBold", 600, "normal"),
             ("Bold", 700, "normal"), ("ExtraBold", 800, "normal"), ("Italic", 400, "italic")]
    return "".join(f"@font-face{{font-family:'Kanit';src:url('file:///{fd}/Kanit-{n}.ttf');font-weight:{w};font-style:{s}}}"
                   for n, w, s in faces)


def open_page(p, guides=False):
    b = p.chromium.launch()
    page = b.new_page(viewport={"width": 1080, "height": 1920})
    page.goto(f"file:///{html}")
    page.add_style_tag(content=fonts_css())
    page.evaluate("document.fonts.load('800 100px Kanit')")
    page.evaluate("Promise.all(['400','500','600','700','800'].map(w => document.fonts.load(w + ' 60px Kanit', 'กขค')))")
    page.evaluate("document.fonts.ready")
    cfg = {"bg": clip.get("bg", {"type": "none"}), "theme": clip.get("theme", {}), "head": tl.get("head", clip.get("head", 0.4)),
           "base": f"file:///{d}/", "guides": guides}
    page.evaluate("([l, c]) => window.init(l, c)", [tl["lines"], cfg])
    page.wait_for_timeout(300)
    return b, page


def encode(page, f0, f1, out):
    ff = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "image2pipe", "-framerate", str(FPS), "-c:v", "mjpeg", "-i", "-",
                           "-c:v", "libx264", "-preset", "medium", "-crf", "17", "-pix_fmt", "yuv420p", "-r", str(FPS), out],
                          stdin=subprocess.PIPE)
    for f in range(f0, f1):
        page.evaluate("t => window.renderAt(t)", f / FPS)
        ff.stdin.write(page.screenshot(type="jpeg", quality=93))
    ff.stdin.close()
    ff.wait()


if mode == "full":
    out = os.path.abspath(sys.argv[3])
    jobs = int(sys.argv[4]) if len(sys.argv) > 4 else 3
    n = int(round(total * FPS))
    cuts = [round(n * i / jobs) for i in range(jobs + 1)]
    parts = [f"{out}.part{i}.mp4" for i in range(jobs)]
    procs = [subprocess.Popen([sys.executable, os.path.abspath(__file__), d, "range", str(cuts[i]), str(cuts[i + 1]), parts[i]])
             for i in range(jobs)]
    if any(p.wait() for p in procs):
        sys.exit("บางช่วงเรนเดอร์ไม่ผ่าน ดูข้อความด้านบน")
    lst = f"{out}.list.txt"
    io.open(lst, "w", encoding="utf-8").write("".join(f"file '{x}'\n" for x in parts))
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", lst, "-c", "copy", out], check=True)
    for x in parts + [lst]:
        os.remove(x)
    print("done", out, "frames", n)
    sys.exit(0)

from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    if mode == "shots":
        args = [a for a in sys.argv[4:] if a != "--guides"]
        b, page = open_page(p, guides="--guides" in sys.argv)
        out = sys.argv[3]
        os.makedirs(out, exist_ok=True)
        for i, t in enumerate(args):
            page.evaluate("t => window.renderAt(t)", float(t))
            page.screenshot(path=f"{out}/s{i:02d}.jpg", type="jpeg", quality=88)
        print("shots", len(args), "->", out)
    elif mode == "range":
        f0, f1, out = int(sys.argv[3]), int(sys.argv[4]), sys.argv[5]
        if f1 < 0:
            f1 = int(round(total * FPS))
        b, page = open_page(p)
        encode(page, f0, f1, out)
        print("range", f0, f1, "->", out)
    else:
        sys.exit("mode ต้องเป็น shots | range | full")
    b.close()
