# -*- coding: utf-8 -*-
# Kosin 17/10/2026 เรนเดอร์ภาพประกอบปกที่วาดเองด้วย HTML/SVG เป็น PNG ขนาดครึ่งบนของปก (1080x1130)
# ใช้เมื่อไม่มีภาพเสรีที่เด่นพอ หรือ chatgpt-bridge ถูกอีกเซสชันใช้อยู่ ตัวอย่าง references/cover_art_example.html
# ใช้: python art_to_png.py <proj>/cover_art.html <proj>/img/cover_bg.png
import os, sys
from playwright.sync_api import sync_playwright
sys.stdout.reconfigure(encoding="utf-8")

src, out = os.path.abspath(sys.argv[1]), os.path.abspath(sys.argv[2])
os.makedirs(os.path.dirname(out), exist_ok=True)
with sync_playwright() as pw:
    b = pw.chromium.launch()
    pg = b.new_page(viewport={"width": 1080, "height": 1130})
    pg.goto("file:///" + src.replace(os.sep, "/"))
    pg.evaluate("document.fonts.ready")
    pg.wait_for_timeout(300)
    pg.screenshot(path=out)
    b.close()
print("ok", out)
