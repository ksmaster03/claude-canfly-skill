# -*- coding: utf-8 -*-
"""เปลี่ยนปกหน้าในเล่ม (PDF + EPUB) เป็นปก v3 โดยยังไม่ใส่หน้าลิขสิทธิ์/ปกหลัง ใช้กับเล่มที่ยังรอเลข ISBN

  python apply_cover.py <book.json>

ผลลัพธ์อยู่ที่ <โฟลเดอร์ book.json>/out/ ชื่อไฟล์เดียวกับต้นฉบับ (ไม่แตะ dist/)
พอได้เลข ISBN ให้รัน apply_isbn.py <book.json> <เลข> ซึ่งอ่านจาก dist/ ใหม่และใส่ครบทั้งปกหน้า หน้าลิขสิทธิ์ ปกหลัง
"""
import io, json, os, re, sys, glob, zipfile, pathlib, html
import fitz
from PIL import Image

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import front_cover

cfg_path = pathlib.Path(sys.argv[1]).resolve()
c = json.load(io.open(cfg_path, encoding='utf-8'))
OUT = cfg_path.parent / 'out'
OUT.mkdir(exist_ok=True)

src_pdf = c['book_pdf']
doc = fitz.open(src_pdf)
pr = doc[0].rect
names0 = doc.resolve_names()
before = {k: doc[v['page']].get_text()[:60] for k, v in names0.items()}
cov_a4 = OUT / 'cover-a4.jpg'
front_cover.render(c, cov_a4, H=round(1600 * pr.height / pr.width))
front_cover.render(c, OUT / 'cover.jpg')
doc.delete_page(0); doc.new_page(0, width=pr.width, height=pr.height)
doc[0].insert_image(doc[0].rect, filename=str(cov_a4))
# ขนาดหน้าทุกหน้าให้เท่าหน้าเนื้อหา (หน้าลิขสิทธิ์/ปกหลังสร้างเป็น A4 595x842 ส่วน Chromium ได้ 596x843)
ref = doc[min(2, doc.page_count - 1)].rect
for pg_ in doc:
    if abs(pg_.rect.width - ref.width) > 0.3 or abs(pg_.rect.height - ref.height) > 0.3:
        pg_.set_mediabox(fitz.Rect(0, 0, ref.width, ref.height))
md = doc.metadata
md['title'] = c['title']
md['author'] = c['author_name']   # ให้ตรงกับชื่อผู้แต่งที่ยื่น ISBN (build ใส่ <ชื่อผู้แต่ง/แบรนด์>)
doc.set_metadata(md)
out_pdf = OUT / os.path.basename(src_pdf)
n0 = doc.page_count
doc.save(out_pdf, garbage=3, deflate=True)
chk = fitz.open(out_pdf); rn = chk.resolve_names()
bad = [k for k, t in before.items() if k not in rn or chk[rn[k]['page']].get_text()[:60] != t]
print(f'PDF  {chk.page_count} หน้า  ลิงก์ {len(before)} อัน เพี้ยน {len(bad)}  -> {out_pdf}')
if bad or chk.page_count != n0:
    sys.exit('ลิงก์เพี้ยน: ' + ', '.join(bad[:5]))

stem = os.path.splitext(src_pdf)[0]
src_epub = c.get('book_epub') or (stem + '.epub' if os.path.exists(stem + '.epub') else None)
if not src_epub:
    print('EPUB ไม่พบ ข้าม'); sys.exit(0)
zin = zipfile.ZipFile(src_epub)
nl = zin.namelist()
opf_name = next(n for n in nl if n.endswith('.opf'))
base = opf_name.rsplit('/', 1)[0] + '/' if '/' in opf_name else ''
opf = zin.read(opf_name).decode('utf-8')
m = re.search(r'<meta name="cover" content="([^"]+)"', opf)
it = m and re.search(r'<item[^>]*id="%s"[^>]*href="([^"]+)"' % re.escape(m.group(1)), opf)
if not it:
    sys.exit('หา cover image ใน EPUB ไม่เจอ')
cover_img = base + it.group(1)
opf = re.sub(r'(<dc:creator[^>]*>)[^<]*(</dc:creator>)', lambda m_: m_.group(1) + html.escape(c['author_name']) + m_.group(2), opf, count=1)
buf = io.BytesIO(); im = Image.open(OUT / 'cover.jpg').convert('RGB')
im.save(buf, 'PNG' if cover_img.lower().endswith('.png') else 'JPEG', quality=90)
out_epub = OUT / os.path.basename(src_epub)
with zipfile.ZipFile(out_epub, 'w') as zout:
    zout.writestr(zipfile.ZipInfo('mimetype'), zin.read('mimetype'), compress_type=zipfile.ZIP_STORED)
    for n in nl:
        if n == 'mimetype':
            continue
        data = buf.getvalue() if n == cover_img else opf.encode('utf-8') if n == opf_name else zin.read(n)
        zout.writestr(n, data, compress_type=zipfile.ZIP_DEFLATED)
z = zipfile.ZipFile(out_epub)
assert z.namelist()[0] == 'mimetype' and z.testzip() is None
print(f'EPUB ปกใหม่ที่ {cover_img}  -> {out_epub}')
