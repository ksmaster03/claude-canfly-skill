# -*- coding: utf-8 -*-
"""สร้างไฟล์แนบคำร้องขอ ISBN ของหอสมุดแห่งชาติ 3 ไฟล์ จาก book.json

  python build_isbn_docs.py <book.json> [ISBN]

ได้ในโฟลเดอร์เดียวกับ book.json:
  1-cover-title.pdf        ปก + หน้าปกใน (ช่อง 1)
  2-copyright-toc-dbd.pdf  หน้าลิขสิทธิ์ + สารบัญ + หนังสือรับรองบริษัท (ช่อง 2 บังคับ)
  3-abstract.pdf           เรื่องย่อ (ช่อง 3)
  copyright-page.pdf       หน้าลิขสิทธิ์เดี่ยว ๆ (ใส่ ISBN จริงแล้วเอาไปแทรกในเล่มได้)
ต้องใช้ Chrome จริง (channel='chrome') เพื่อให้ตัดคำไทยถูก และต้องมีไฟล์ Sarabun ในเครื่อง
"""
import io, json, os, sys, pathlib, html, shutil
import fitz
from playwright.sync_api import sync_playwright

cfg_path = pathlib.Path(sys.argv[1]).resolve()
OUT = cfg_path.parent
c = json.load(io.open(cfg_path, encoding='utf-8'))
ISBN = (sys.argv[2] if len(sys.argv) > 2 else c.get('isbn')) or '.......................................'
pub = c['publisher']
e = html.escape

FONT_DIRS = [pathlib.Path(__file__).resolve().parent.parent / 'fonts' / 'kanit',
             pathlib.Path(c['book_pdf']).resolve().parent.parent / 'fonts',
             pathlib.Path.home() / '.claude/skills/ebook/fonts']
FONTS = next((d for d in FONT_DIRS if (d / 'Kanit-Regular.ttf').exists()), None)
if not FONTS:
    sys.exit('ไม่พบ Kanit-Regular.ttf ใน ' + ', '.join(map(str, FONT_DIRS)))
F = FONTS.as_uri()

CSS = f"""
@font-face{{font-family:S;src:url('{F}/Kanit-Regular.ttf')}}
@font-face{{font-family:S;font-weight:700;src:url('{F}/Kanit-Bold.ttf')}}
@page{{size:A4;margin:28mm 24mm}}
body{{font-family:S;font-size:15pt;line-height:1.75;color:#111}}
h1{{font-size:20pt;line-height:1.45;margin:0 0 4mm}} .sub{{font-size:15pt;margin-bottom:10mm}}
table{{border-collapse:collapse}} td{{vertical-align:top;padding:1.2mm 0}} td:first-child{{width:38mm;font-weight:700}}
.isbn{{font-size:17pt;font-weight:700;margin:8mm 0}} .small{{font-size:13pt;color:#333}}
"""
author = e(c['author_name']) + (f" (นามปากกา {e(c['pen_name'])})" if c.get('pen_name') else '')
addr = f"{e(pub['address_no'])}" + (f" หมู่ที่ {e(pub['moo'])}" if pub.get('moo') else '') + \
       (f" ซอย{e(pub['soi'])}" if pub.get('soi') else '') + \
       (f" ถนน{e(pub['road'])}" if pub.get('road') and pub['road'] != '-' else '') + \
       f" ตำบล{e(pub['subdistrict'])} อำเภอ{e(pub['district'])} จังหวัด{e(pub['province'])} {e(pub['zip'])}"
COPY = f"""<html lang="th"><head><meta charset="utf-8"><style>{CSS}</style></head><body>
<h1>{e(c['title'])}</h1><div class="sub">{e(c.get('subtitle',''))}</div>
<table>
<tr><td>ผู้เขียน</td><td>{author}</td></tr>
<tr><td>พิมพ์ครั้งที่</td><td>{e(c['edition'])} {e(c.get('edition_month_th',''))} พุทธศักราช {e(c['year_be'])}</td></tr>
<tr><td>รูปแบบ</td><td>หนังสืออิเล็กทรอนิกส์ (PDF และ EPUB) {c['pages']} หน้า</td></tr>
<tr><td>ราคา</td><td>{str(c['price']) + ' บาท' if int(c['price']) else 'ไม่มีราคาจำหน่าย (แจกฟรี)'}</td></tr>
</table>
<div class="isbn">ISBN (e-book) {e(ISBN)}</div>
<table>
<tr><td>จัดทำโดย</td><td>{e(pub['name_th'])}<br>{addr}<br>โทรศัพท์ {e(pub['phone'])} · อีเมล {e(pub['email'])}</td></tr>
<tr><td>เผยแพร่ที่</td><td>{e(c['url'])}</td></tr>
</table>
<p class="small" style="margin-top:10mm">ลิขสิทธิ์ของ{e(pub['name_th'])} สงวนลิขสิทธิ์ตามพระราชบัญญัติลิขสิทธิ์ พ.ศ. 2537
ห้ามคัดลอก ทำซ้ำ หรือเผยแพร่ส่วนหนึ่งส่วนใดของหนังสือเล่มนี้โดยไม่ได้รับอนุญาตเป็นลายลักษณ์อักษร</p>
</body></html>"""
ABS = f"""<html lang="th"><head><meta charset="utf-8"><style>{CSS}</style></head><body>
<h1>เรื่องย่อ</h1>
<div class="sub">{e(c['title'])}{' : ' + e(c['subtitle']) if c.get('subtitle') else ''}<br>โดย {e(c['author_name'])} · {e(pub['name_th'])}</div>
<p>{e(c['abstract'])}</p></body></html>"""


def html_pdf(doc, out):
    tmp = OUT / '_tmp.html'
    io.open(tmp, 'w', encoding='utf-8').write(doc)
    with sync_playwright() as p:
        b = p.chromium.launch(channel='chrome')
        pg = b.new_page(); pg.goto(tmp.as_uri()); pg.wait_for_timeout(500)
        pg.pdf(path=str(out), format='A4', prefer_css_page_size=True); b.close()
    tmp.unlink()


src = fitz.open(c['book_pdf'])
html_pdf(COPY, OUT / 'copyright-page.pdf')
html_pdf(ABS, OUT / '3-abstract.pdf')

d = fitz.open()
for n in c['cover_pages']:
    d.insert_pdf(src, from_page=n - 1, to_page=n - 1)
d.save(OUT / '1-cover-title.pdf', garbage=4, deflate=True)

d = fitz.open(OUT / 'copyright-page.pdf')
for n in c['toc_pages']:
    d.insert_pdf(src, from_page=n - 1, to_page=n - 1)
d.save(OUT / '2-copyright-toc.pdf', garbage=4, deflate=True)
# หนังสือรับรองบริษัท แนบเป็นไฟล์แยกในช่องที่ 2 (เจ้าหน้าที่ขอแบบนี้ ถ้ารวมท้ายไฟล์หน้าลิขสิทธิ์จะหาไม่เจอ)
FILES = ['1-cover-title.pdf', '2-copyright-toc.pdf', '3-abstract.pdf']
if pub.get('juristic') and c.get('dbd_cert_pdf'):
    shutil.copyfile(c['dbd_cert_pdf'], OUT / '4-dbd-certificate.pdf'); FILES.append('4-dbd-certificate.pdf')
old2 = OUT / '2-copyright-toc-dbd.pdf'
if old2.exists():
    old2.unlink()


def shrink(path, limit=4_500_000):
    # ระบบรับไฟล์ละไม่เกินราว 5 MB: ถ้าเกิน แปลงทุกหน้าเป็นภาพ JPEG แล้วลดความละเอียดลงจนผ่าน
    for dpi in (130, 100, 80, 60):
        if os.path.getsize(path) <= limit:
            return
        src_doc = fitz.open(path); out = fitz.open()
        for pg in src_doc:
            pix = pg.get_pixmap(dpi=dpi)
            p = out.new_page(width=pg.rect.width, height=pg.rect.height)
            p.insert_image(p.rect, stream=pix.tobytes('jpeg', jpg_quality=70))
        src_doc.close()
        tmp = str(path) + '.tmp'; out.save(tmp, garbage=4, deflate=True); out.close()
        os.replace(tmp, path)


for f in FILES:
    shrink(OUT / f)
    size = os.path.getsize(OUT / f)
    warn = '  ‼ เกิน 5 MB ระบบไม่รับ' if size > 5_000_000 else ''
    print(f, fitz.open(OUT / f).page_count, 'pages', size // 1024, 'KB' + warn)
