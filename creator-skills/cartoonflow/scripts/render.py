# -*- coding: utf-8 -*-
# Kosin 18/10/2026 เรนเดอร์ flow.html เป็น flow.png ด้วย Chromium (ตัวอักษรไทยไม่ลอย) และย่อภาพการ์ตูนเป็น img/web/*.jpg สำหรับไฟล์ Markdown
import sys
from pathlib import Path
from playwright.sync_api import sync_playwright
from PIL import Image

HERE = Path(__file__).resolve().parent
web = HERE / "img" / "web"
web.mkdir(parents=True, exist_ok=True)
for p in sorted((HERE / "img").glob("s*.png")):
    im = Image.open(p).convert("RGB")
    im.thumbnail((800, 800))
    im.save(web / (p.stem + ".jpg"), quality=86)

with sync_playwright() as pw:
    b = pw.chromium.launch()
    pg = b.new_page(viewport={"width": 1080, "height": 1200}, device_scale_factor=1)
    pg.goto((HERE / "flow.html").as_uri(), wait_until="networkidle")
    pg.evaluate("document.fonts.ready")
    pg.wait_for_timeout(800)
    missing = pg.evaluate("[...document.images].filter(i => !i.complete || !i.naturalWidth).map(i => i.getAttribute('src'))")
    pg.screenshot(path=str(HERE / "flow.png"), full_page=True)
    h = pg.evaluate("document.body.scrollHeight")
    b.close()
print("flow.png สูง", h, "px · ภาพที่ขาด:", missing or "ไม่มี")
