# Render each PDF page to PNG so the layout can be checked with the Read tool.
# usage: python -I pdf_to_png.py <in.pdf> <out_prefix> [dpi=110]   -> <out_prefix>-p1.png ...
import sys
import fitz  # PyMuPDF

pdf, prefix = sys.argv[1], sys.argv[2]
dpi = int(sys.argv[3]) if len(sys.argv) > 3 else 110
doc = fitz.open(pdf)
for i, page in enumerate(doc):
    out = f"{prefix}-p{i + 1}.png"
    page.get_pixmap(dpi=dpi).save(out)
    print(out)
