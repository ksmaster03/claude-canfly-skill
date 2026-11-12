# -*- coding: utf-8 -*-
"""ใส่หน้าลิขสิทธิ์ (และเลข ISBN ถ้ามี) เข้าเล่ม PDF + EPUB โดยไม่แตะไฟล์ต้นฉบับ

  python apply_isbn.py <book.json>                 เตรียมโครง: หน้าลิขสิทธิ์เว้นช่อง ISBN ไว้ (ห้ามขึ้นร้าน)
  python apply_isbn.py <book.json> 978-616-xx-xxxx-x   ใส่เลขจริง ได้ไฟล์พร้อมอัปทับบนร้าน

ผลลัพธ์อยู่ที่ <โฟลเดอร์ book.json>/out/<ชื่อไฟล์เดิม>.pdf และ .epub
- PDF : แทรก copyright-page.pdf ก่อนหน้าสารบัญ (toc_pages[0]) ลิงก์ในสารบัญเป็น named destination จึงไม่เพี้ยน
- EPUB: เพิ่ม text/copyright.xhtml ต่อจาก title_page ใน spine และ dc:identifier urn:isbn เมื่อมีเลข
ตรวจผลเองทุกครั้ง: จำนวนหน้า +1 และลิงก์สารบัญยังไปหน้าเปิดบทเดิม
"""
import io, json, os, re, sys, glob, shutil, subprocess, zipfile, datetime, html, pathlib
import fitz

HERE = pathlib.Path(__file__).resolve().parent
cfg_path = pathlib.Path(sys.argv[1]).resolve()
ISBN = sys.argv[2] if len(sys.argv) > 2 else ''
c = json.load(io.open(cfg_path, encoding='utf-8'))
pub = c['publisher']
OUT = cfg_path.parent / 'out'
OUT.mkdir(exist_ok=True)
e = html.escape

if ISBN and not re.fullmatch(r'97[89]-?\d{1,5}-?\d{1,7}-?\d{1,7}-?\d', ISBN):
    sys.exit('รูปแบบ ISBN ไม่ถูกต้อง: ' + ISBN)

# 0) จำนวนหน้าที่พิมพ์ในหน้าลิขสิทธิ์ = จำนวนหน้าจริงของเล่มที่จะออก (เล่ม + หน้าลิขสิทธิ์ + ปกหลังเมื่อมีเลข)
#    เดิมใช้ค่าตอนยื่นคำร้อง พอจัดรูปเล่มใหม่แล้วตัวเลขไม่ตรง (เจอ 32 จาก 36 เล่ม 1 ต.ค. 2569)
_n_final = fitz.open(c['book_pdf']).page_count + (2 if ISBN else 1)
if c.get('pages') != _n_final:
    c['pages_submitted'] = c.get('pages_submitted', c.get('pages'))
    c['pages'] = _n_final
    json.dump(c, io.open(cfg_path, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)

# 1) หน้าลิขสิทธิ์ PDF (ใช้ตัวสร้างเดียวกับไฟล์แนบคำร้อง เพื่อให้ข้อความตรงกัน)
r = subprocess.run([sys.executable, str(HERE / 'build_isbn_docs.py'), str(cfg_path)] + ([ISBN] if ISBN else []),
                   capture_output=True, text=True, encoding='utf-8')
if r.returncode:
    sys.exit(r.stderr)
cp = fitz.open(cfg_path.parent / 'copyright-page.pdf')

def find_toc(d, fallback):
    """หน้าสารบัญ = หน้าแรกใน 8 หน้าแรกที่มีลิงก์ภายใน (named dest) ตั้งแต่ 5 อัน (toc_pages ใน book.json เลื่อนได้เมื่อ layout เปลี่ยน)"""
    nm = d.resolve_names()
    for i in range(min(8, d.page_count)):
        if sum(1 for l in d[i].get_links() if l.get('nameddest') in nm) >= 5:
            return i
    return fallback


# 2) PDF
src_pdf = c['book_pdf']
doc = fitz.open(src_pdf)
at = find_toc(doc, c['toc_pages'][0] - 1)          # index ของหน้าสารบัญ = แทรกไว้ก่อนหน้านั้น
src_names = doc.resolve_names()
before = {l['nameddest']: doc[src_names[l['nameddest']]['page']].get_text()[:60]
          for l in doc[at].get_links() if l.get('nameddest') in src_names}
n0 = doc.page_count
doc.insert_pdf(cp, start_at=at)
added = 1
if ISBN:  # ปกหน้าแบบใหม่ (รูปผู้เขียน) + ปกหลังท้ายเล่มพร้อมบาร์โค้ด EAN-13 (ใส่เฉพาะตอนมีเลขจริง)
    sys.path.insert(0, str(HERE))
    from back_cover import build_back_cover_pdf, back_cover_xhtml
    import front_cover
    pr = doc[0].rect
    cov_pdf_jpg = OUT / 'cover-a4.jpg'
    front_cover.render(c, cov_pdf_jpg, H=round(1600 * pr.height / pr.width))
    front_cover.render(c, OUT / 'cover.jpg')                     # 2:3 สำหรับ EPUB และหน้าร้าน
    doc.delete_page(0); doc.new_page(0, width=pr.width, height=pr.height)
    doc[0].insert_image(doc[0].rect, filename=str(cov_pdf_jpg))
    bc_pdf = cfg_path.parent / 'back-cover.pdf'
    build_back_cover_pdf(c, ISBN, bc_pdf, fitz.open(src_pdf)[0])
    doc.insert_pdf(fitz.open(bc_pdf))
    added = 2
# ขนาดหน้าทุกหน้าให้เท่าหน้าเนื้อหา (หน้าลิขสิทธิ์/ปกหลังสร้างเป็น A4 595x842 ส่วน Chromium ได้ 596x843)
ref = doc[min(2, doc.page_count - 1)].rect
for pg_ in doc:
    if abs(pg_.rect.width - ref.width) > 0.3 or abs(pg_.rect.height - ref.height) > 0.3:
        pg_.set_mediabox(fitz.Rect(0, 0, ref.width, ref.height))
md = doc.metadata
md['title'] = c['title']
md['author'] = c['author_name']   # ให้ตรงกับชื่อผู้แต่งที่ยื่น ISBN (build ใส่ <ชื่อผู้แต่ง/แบรนด์>)
md['subject'] = f'ISBN {ISBN}' if ISBN else md.get('subject', '')
doc.set_metadata(md)
out_pdf = OUT / os.path.basename(src_pdf)
doc.save(out_pdf, garbage=3, deflate=True)
# ตรวจหลังบันทึก (ค่าในหน่วยความจำก่อนบันทึกยังเป็นเลขหน้าเก่า): ลิงก์สารบัญต้องพาไปหน้าที่ข้อความเหมือนเดิม
chk = fitz.open(out_pdf); rn = chk.resolve_names()
bad = [k for k, t in before.items() if k not in rn or chk[rn[k]['page']].get_text()[:60] != t]
print(f'PDF  {n0} -> {chk.page_count} หน้า  แทรกที่หน้า {at + 1}  ลิงก์สารบัญ {len(before)} อัน เพี้ยน {len(bad)}  -> {out_pdf}')
if bad or chk.page_count != n0 + added:
    sys.exit('ลิงก์สารบัญเพี้ยน: ' + ', '.join(bad))
if ISBN:
    try:
        import zxingcpp
        from PIL import Image
        pix = chk[-1].get_pixmap(dpi=200); img = Image.frombytes('RGB', (pix.width, pix.height), pix.samples)
        got = [x.text for x in zxingcpp.read_barcodes(img)]
        want = re.sub(r'\D', '', ISBN)
        print(f'บาร์โค้ดหน้าสุดท้าย: {got}  {"ตรง" if want in got else "ไม่ตรง"}')
        if want not in got:
            sys.exit('บาร์โค้ดบนปกหลังอ่านไม่ได้หรือไม่ตรงกับ ISBN')
    except ImportError:
        print('‼ ไม่มี zxing-cpp ข้ามการสแกนบาร์โค้ด (pip install zxing-cpp)')

# 3) EPUB
stem = os.path.splitext(src_pdf)[0]
src_epub = c.get('book_epub') or (stem + '.epub' if os.path.exists(stem + '.epub') else None)
if not src_epub:
    cand = [x for x in glob.glob(os.path.dirname(src_pdf) + '/*.epub')]
    src_epub = max(cand, key=os.path.getmtime) if cand else None
if not src_epub:
    print('EPUB ไม่พบ ข้าม'); sys.exit(0)

author = e(c['author_name']) + (f' (นามปากกา {e(c["pen_name"])})' if c.get('pen_name') else '')
addr = f"{e(pub['address_no'])}" + (f" หมู่ที่ {e(pub['moo'])}" if pub.get('moo') else '') + \
       f" ตำบล{e(pub['subdistrict'])} อำเภอ{e(pub['district'])} จังหวัด{e(pub['province'])} {e(pub['zip'])}"
isbn_line = f'ISBN (e-book) {e(ISBN)}' if ISBN else 'ISBN (e-book) .......................................'
XHTML = f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:epub="http://www.idpf.org/2007/ops" lang="th" xml:lang="th">
<head>
  <meta charset="utf-8" />
  <title>ข้อมูลลิขสิทธิ์</title>
  <link rel="stylesheet" type="text/css" href="../styles/stylesheet1.css" />
  <style>.copyright p{{margin:0.35em 0;text-indent:0}} .copyright .isbn{{font-weight:bold;margin:1.2em 0}}</style>
</head>
<body epub:type="frontmatter">
<section epub:type="copyright-page" class="copyright">
  <p><strong>{e(c['title'])}</strong></p>
  <p>{e(c.get('subtitle', ''))}</p>
  <p>ผู้เขียน {author}</p>
  <p>พิมพ์ครั้งที่ {e(str(c['edition']))} {e(c.get('edition_month_th', ''))} พุทธศักราช {e(c['year_be'])} (หนังสืออิเล็กทรอนิกส์)</p>
  <p class="isbn">{isbn_line}</p>
  <p>จัดทำโดย {e(pub['name_th'])}</p>
  <p>{addr}</p>
  <p>โทรศัพท์ {e(pub['phone'])} · อีเมล {e(pub['email'])}</p>
  <p>เผยแพร่ที่ {e(c['url'])}</p>
  <p>ลิขสิทธิ์ของ{e(pub['name_th'])} สงวนลิขสิทธิ์ตามพระราชบัญญัติลิขสิทธิ์ พ.ศ. 2537</p>
</section>
</body>
</html>
"""

zin = zipfile.ZipFile(src_epub)
names = zin.namelist()
opf_name = next(n for n in names if n.endswith('.opf'))
base = opf_name.rsplit('/', 1)[0] + '/' if '/' in opf_name else ''
opf = zin.read(opf_name).decode('utf-8')
if 'copyright_xhtml' not in opf:
    opf = opf.replace('<item id="title_page_xhtml"',
                      '<item id="copyright_xhtml" href="text/copyright.xhtml" media-type="application/xhtml+xml" />\n    <item id="title_page_xhtml"', 1)
    opf = re.sub(r'(<itemref idref="title_page_xhtml"[^>]*/>)', r'\1\n    <itemref idref="copyright_xhtml" />', opf, count=1)
if ISBN and 'backcover_xhtml' not in opf:
    opf = opf.replace('<item id="title_page_xhtml"',
                      '<item id="backcover_xhtml" href="text/backcover.xhtml" media-type="application/xhtml+xml" properties="svg" />\n    <item id="title_page_xhtml"', 1)
    opf = opf.replace('</spine>', '  <itemref idref="backcover_xhtml" />\n  </spine>', 1)
opf = re.sub(r'\s*<dc:identifier id="isbn">[^<]*</dc:identifier>', '', opf)
if ISBN:
    opf = opf.replace('<dc:title', f'<dc:identifier id="isbn">urn:isbn:{ISBN.replace("-", "")}</dc:identifier>\n    <dc:title', 1)
opf = re.sub(r'(<dc:creator[^>]*>)[^<]*(</dc:creator>)', lambda m_: m_.group(1) + e(c['author_name']) + m_.group(2), opf, count=1)
now = datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
opf = re.sub(r'(<meta property="dcterms:modified">)[^<]*(</meta>)', rf'\g<1>{now}\2', opf)
if 'copyright_xhtml' not in opf or 'idref="copyright_xhtml"' not in opf:
    sys.exit('แก้ content.opf ไม่สำเร็จ (โครงสร้างไม่ใช่แบบ pandoc)')

cover_img, cover_bytes = None, None
if ISBN:  # รูปปกใน EPUB = item ที่ <meta name="cover"> ชี้ แทนด้วยปกใหม่ (แปลงเป็นชนิดไฟล์เดิม)
    m = re.search(r'<meta name="cover" content="([^"]+)"', opf)
    it = m and re.search(r'<item[^>]*id="%s"[^>]*href="([^"]+)"' % re.escape(m.group(1)), opf)
    if it:
        cover_img = base + it.group(1)
        from PIL import Image
        buf = io.BytesIO(); im = Image.open(OUT / 'cover.jpg').convert('RGB')
        im.save(buf, 'PNG' if cover_img.lower().endswith('.png') else 'JPEG', quality=90); cover_bytes = buf.getvalue()
    else:
        print('‼ หา cover image ใน EPUB ไม่เจอ ไม่ได้เปลี่ยนปก EPUB')
out_epub = OUT / os.path.basename(src_epub)
with zipfile.ZipFile(out_epub, 'w') as zout:
    zout.writestr(zipfile.ZipInfo('mimetype'), zin.read('mimetype'), compress_type=zipfile.ZIP_STORED)  # ต้องเป็นไฟล์แรกและไม่บีบอัด
    for n in names:
        if n in ('mimetype', base + 'text/copyright.xhtml', base + 'text/backcover.xhtml'):
            continue
        data = opf.encode('utf-8') if n == opf_name else zin.read(n)
        if ISBN and n == cover_img:
            data = cover_bytes
        zout.writestr(n, data, compress_type=zipfile.ZIP_DEFLATED)
    zout.writestr(base + 'text/copyright.xhtml', XHTML.encode('utf-8'), compress_type=zipfile.ZIP_DEFLATED)
    if ISBN:
        zout.writestr(base + 'text/backcover.xhtml', back_cover_xhtml(c, ISBN).encode('utf-8'), compress_type=zipfile.ZIP_DEFLATED)
chk = zipfile.ZipFile(out_epub)
assert chk.namelist()[0] == 'mimetype' and chk.testzip() is None
spine = re.findall(r'idref="([^"]+)"', chk.read(opf_name).decode('utf-8'))[:5]
print(f'EPUB spine: {" > ".join(spine)}  ISBN metadata: {"ใส่แล้ว" if ISBN else "ยังไม่ใส่"}  -> {out_epub}')
if not ISBN:
    print('‼ ไฟล์นี้ยังเป็นช่อง ISBN ว่าง ใช้ตรวจโครงเท่านั้น ห้ามอัปขึ้นร้าน')
