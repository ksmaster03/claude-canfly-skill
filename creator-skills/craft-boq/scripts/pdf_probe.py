# -*- coding: utf-8 -*-
"""
pdf_probe.py — สำรวจไฟล์แบบ PDF ก่อนถอดแบบ  (craft-boq step 1)

ใช้:
  python pdf_probe.py "แบบ.pdf"                              # รายงานโครงสร้างไฟล์
  python pdf_probe.py "แบบ.pdf" --outdir out --dpi 200       # + เรนเดอร์ทุกหน้าเป็น PNG
  python pdf_probe.py "แบบ.pdf" --crop 3 0.28 0.36 0.66 0.90 --dpi 450 --name B1_front
        # ซูมเฉพาะส่วน : --crop <เลขหน้า(1-based)> <x0> <y0> <x1> <y1>  (สัดส่วน 0-1 ของหน้าที่แสดง)

ต้องมี : pip install pymupdf
"""
import argparse, os, re, sys

try:
    import fitz  # PyMuPDF
except ImportError:
    sys.exit("ต้องติดตั้งก่อน:  pip install pymupdf")

VIEW = re.compile(r"(FRONT|BACK|SIDE|SECTION|SEC\.|ELEVATION|ELE|PLAN|DETAIL)", re.I)
CODE = re.compile(r"\b([A-Z]{1,3}-?\d{1,2})\b")


def probe(path):
    d = fitz.open(path)
    print(f"ไฟล์      : {os.path.basename(path)}")
    print(f"จำนวนหน้า : {d.page_count}")
    print()
    print(f"{'หน้า':>4} {'ขนาด':>11} {'ชนิด':<14} {'vector':>7} {'text':>6}  วิว / รหัสที่พบ")
    print("-" * 100)
    drawings, images = [], []
    for i, p in enumerate(d):
        t = p.get_text()
        nv = len(p.get_drawings())
        ni = len(p.get_images(full=True))
        kind = "vector CAD" if nv > 50 else ("ภาพ/3D" if ni else "ว่าง/สแกน")
        (drawings if nv > 50 else images).append(i + 1)
        views = sorted({v.upper() for v in VIEW.findall(t)})
        codes = sorted(set(CODE.findall(t)))[:14]
        w, h = p.rect.width, p.rect.height
        print(f"{i+1:>4} {w:.0f}x{h:.0f}".ljust(17)
              + f"{kind:<14} {nv:>7} {len(t.strip()):>6}  "
              + (", ".join(views) + ("  |  " + " ".join(codes) if codes else "")))
    print()
    print(f"หน้าที่ถอดแบบได้ (vector) : {drawings}")
    print(f"หน้าภาพ/3D               : {images}")
    print()
    print("⚠ ข้อความไทยในแบบมักสกัดไม่ออก (ฟอนต์ไม่ฝัง ToUnicode) แต่ตัวเลขออกครบ")
    print("  ให้เรนเดอร์เป็น PNG แล้วอ่านด้วยตาเสมอ อย่าเชื่อ text extraction อย่างเดียว")
    return d


def render_all(d, outdir, dpi):
    os.makedirs(outdir, exist_ok=True)
    for i, p in enumerate(d):
        f = os.path.join(outdir, f"p{i+1:02d}.png")
        p.get_pixmap(dpi=dpi).save(f)
    print(f"\nเรนเดอร์ {d.page_count} หน้า -> {outdir}  ({dpi} dpi)")


def render_crop(d, page1, box, dpi, outdir, name):
    os.makedirs(outdir, exist_ok=True)
    p = d[page1 - 1]
    r = p.rect
    clip = fitz.Rect(r.x0 + box[0] * r.width, r.y0 + box[1] * r.height,
                     r.x0 + box[2] * r.width, r.y0 + box[3] * r.height)
    pix = p.get_pixmap(dpi=dpi, clip=clip)
    f = os.path.join(outdir, f"{name or f'p{page1:02d}_crop'}.png")
    pix.save(f)
    print(f"crop -> {f}  ({pix.width}x{pix.height} px)")
    if pix.width > 2200:
        print("  ⚠ กว้างเกิน ~2200 px จะถูกย่อตอนอ่าน ทำให้ซูมไม่ขึ้น — ตัดให้แคบลงหรือลด dpi")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("pdf")
    ap.add_argument("--outdir", default=None)
    ap.add_argument("--dpi", type=int, default=200)
    ap.add_argument("--crop", nargs=5, metavar=("PAGE", "X0", "Y0", "X1", "Y1"))
    ap.add_argument("--name", default=None)
    a = ap.parse_args()

    doc = probe(a.pdf)
    if a.crop:
        render_crop(doc, int(a.crop[0]), [float(x) for x in a.crop[1:]],
                    a.dpi, a.outdir or ".", a.name)
    elif a.outdir:
        render_all(doc, a.outdir, a.dpi)
