# -*- coding: utf-8 -*-
"""ปกหลังท้ายเล่ม + ป้ายบาร์โค้ด ISBN (EAN-13) แบบหลังปกหนังสือไทย

    from back_cover import build_back_cover_pdf, back_cover_xhtml
    build_back_cover_pdf(cfg, isbn, out_pdf, cover_pdf_page)   # 1 หน้า ขนาดเท่าหน้าเล่ม
    back_cover_xhtml(cfg, isbn)                                # หน้า EPUB (SVG ในไฟล์)

สีพื้นดึงจากปกหน้าแล้วทำให้เข้มพอให้ตัวขาวอ่านชัด · ห้ามใส่ letter-spacing กับข้อความไทย
"""
import html, io, pathlib, re
import fitz
from ean13 import isbn_label_svg, digits_of

e = html.escape
HERE = pathlib.Path(__file__).resolve().parent
FONTS = (HERE.parent / 'fonts' / 'kanit').as_uri()


def price_line(c):
    return f"ราคา {c['price']} บาท" if int(c['price']) else 'ไม่มีราคาจำหน่าย'


def blurb(c, limit=430):
    t = re.sub(r'\s+', ' ', c.get('abstract', '')).strip()
    if len(t) <= limit:
        return t
    cut = t[:limit]
    k = cut.rfind(' ')
    return (cut[:k] if k > limit * 0.6 else cut).rstrip() + ' …'


def cover_color(page):
    """สีเฉลี่ยของปก แล้วกดความสว่างลงให้ข้อความสีขาวผ่าน WCAG AA ได้สบาย"""
    pix = page.get_pixmap(dpi=12, colorspace=fitz.csRGB)
    s = pix.samples; n = len(s) // 3
    r, g, b = (sum(s[i::3]) / n for i in range(3))
    def lum(x):
        x /= 255
        return x / 12.92 if x <= 0.03928 else ((x + 0.055) / 1.055) ** 2.4
    k = 1.0
    while k > 0.05 and 0.2126 * lum(r * k) + 0.7152 * lum(g * k) + 0.0722 * lum(b * k) > 0.045:
        k -= 0.05
    return '#%02x%02x%02x' % (int(r * k), int(g * k), int(b * k))


def _html(c, isbn, bg, w_pt, h_pt):
    pub = c['publisher']
    svg = isbn_label_svg(isbn).replace('<svg ', '<svg style="display:block;width:100%;height:auto" ', 1)
    return f"""<html lang="th"><head><meta charset="utf-8"><style>
@font-face{{font-family:S;src:url('{FONTS}/Kanit-Regular.ttf')}}
@font-face{{font-family:S;font-weight:700;src:url('{FONTS}/Kanit-Bold.ttf')}}
@page{{size:{w_pt}pt {h_pt}pt;margin:0}}
html,body{{margin:0;padding:0}}
.page{{width:{w_pt}pt;height:{h_pt}pt;background:{bg};color:#fff;font-family:S;position:relative;overflow:hidden;box-sizing:border-box;padding:26mm 22mm}}
.kick{{font-size:11pt;opacity:.85}}
h1{{font-size:30pt;line-height:1.3;margin:4mm 0 3mm;font-weight:700}}
.sub{{font-size:15pt;line-height:1.55;opacity:.92;margin-bottom:12mm}}
.blurb{{font-size:13.5pt;line-height:1.8;max-width:150mm;opacity:.95}}
.foot{{position:absolute;left:22mm;bottom:22mm;font-size:11pt;line-height:1.7;opacity:.9;max-width:95mm}}
.bc{{position:absolute;right:20mm;bottom:20mm;width:48mm;text-align:left}}
.price{{font-size:13pt;font-weight:700;margin:0 0 1.5mm 1mm}}
.label{{background:#fff;padding:1.2mm 1.2mm 0.6mm}}
</style></head><body><div class="page">
<div class="kick">E-BOOK · {e(c['year_be'])}</div>
<h1>{e(c['title'])}</h1>
<div class="sub">{e(c.get('subtitle', ''))}</div>
<div class="blurb">{e(blurb(c))}</div>
<div class="foot">จัดทำโดย {e(pub['name_th'])}<br>{e(c['url'])}</div>
<div class="bc"><div class="price">{e(price_line(c))}</div><div class="label">{svg}</div></div>
</div></body></html>"""


def build_back_cover_pdf(c, isbn, out_pdf, cover_page):
    from playwright.sync_api import sync_playwright
    digits_of(isbn)
    w, h = cover_page.rect.width, cover_page.rect.height
    # พื้นเดียวกับปกหน้าแบบใหม่ (front_cover.py) ให้ปกหน้า-หลังเข้าชุด
    doc = _html(c, isbn, 'radial-gradient(120% 70% at 15% 45%, #16213d 0%, #0b1122 55%, #070b16 100%)', round(w, 2), round(h, 2))
    tmp = pathlib.Path(out_pdf).resolve().with_suffix('.html')
    io.open(tmp, 'w', encoding='utf-8').write(doc)
    with sync_playwright() as p:
        b = p.chromium.launch(channel='chrome')
        pg = b.new_page(); pg.goto(tmp.as_uri()); pg.wait_for_timeout(500)
        pg.pdf(path=str(out_pdf), width=f'{w / 72:.4f}in', height=f'{h / 72:.4f}in', print_background=True,
               margin={'top': '0', 'right': '0', 'bottom': '0', 'left': '0'})
        b.close()
    tmp.unlink()
    return out_pdf


def back_cover_xhtml(c, isbn):
    svg = isbn_label_svg(isbn).replace('<svg ', '<svg style="width:14em;max-width:60%;height:auto" ', 1)
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:epub="http://www.idpf.org/2007/ops" lang="th" xml:lang="th">
<head>
  <meta charset="utf-8" />
  <title>ปกหลัง</title>
  <link rel="stylesheet" type="text/css" href="../styles/stylesheet1.css" />
  <style>.backcover p{{text-indent:0}} .backcover .bc{{margin-top:2em;text-align:right}} .backcover .price{{font-weight:bold;margin:0 0 .3em}}</style>
</head>
<body epub:type="backmatter">
<section epub:type="colophon" class="backcover">
  <h2>{e(c['title'])}</h2>
  <p>{e(c.get('subtitle', ''))}</p>
  <p>{e(blurb(c))}</p>
  <p>จัดทำโดย {e(c['publisher']['name_th'])}</p>
  <div class="bc"><p class="price">{e(price_line(c))}</p>{svg}</div>
</section>
</body>
</html>
"""
