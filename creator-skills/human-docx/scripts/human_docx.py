# -*- coding: utf-8 -*-
r"""
Reusable python-docx helpers for the human-docx skill.

Import this module and call the functions below to build a .docx that reads
as plain, human-written prose: no emoji, no icons, no horizontal rules, no
colored highlight boxes. Structure comes from paragraph breaks and sparing
bold, not from decoration.

Usage from another script:

    import sys
    sys.path.insert(0, r"~\.claude\skills\human-docx\scripts")
    from human_docx import new_document, add_para, add_rich, add_page_break, save

    doc = new_document()
    add_para(doc, "เรียน เพื่อนพนักงานทุกท่าน", space_after=10)
    add_para(doc, "เนื้อความย่อหน้าแรก ...", space_after=10)
    save(doc, r"$WORK\out\my-letter.docx")

Or run this file directly for a short demo document (see __main__ below).
"""

from docx import Document
from docx.shared import Pt, RGBColor, Cm
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

# Thai body font. "Leelawadee UI" ships with Windows 10/11 and renders Thai
# cleanly on screen; "TH Sarabun New" is the Thai government/document
# standard font if the recipient expects an official look and has it
# installed. English-only documents read more naturally in "Calibri" or
# "Georgia" than in a Thai UI font.
THAI_FONT = "Leelawadee UI"
THAI_FONT_OFFICIAL = "TH Sarabun New"
ENGLISH_FONT = "Calibri"


def new_document(margin_cm=2.5):
    """Create a Document with sane margins. Call once per output file."""
    doc = Document()
    for s in doc.sections:
        s.top_margin = Cm(margin_cm)
        s.bottom_margin = Cm(margin_cm)
        s.left_margin = Cm(margin_cm)
        s.right_margin = Cm(margin_cm)
    return doc


def style_run(run, size=12, bold=False, color=None, italic=False, font=THAI_FONT):
    """Apply font/size/weight/color to one run, including the Thai/complex-
    script and east-asian font slots so Word doesn't silently substitute a
    different face for Thai glyphs."""
    run.font.name = font
    run.font.size = Pt(size)
    run.bold = bold
    run.italic = italic
    if color:
        run.font.color.rgb = RGBColor(*color)
    rpr = run._element.get_or_add_rPr()
    rfonts = rpr.find(qn('w:rFonts'))
    if rfonts is None:
        rfonts = OxmlElement('w:rFonts')
        rpr.insert(0, rfonts)
    for attr in ('w:ascii', 'w:hAnsi', 'w:cs', 'w:eastAsia'):
        rfonts.set(qn(attr), font)
    szcs = OxmlElement('w:szCs')
    szcs.set(qn('w:val'), str(int(size * 2)))
    rpr.append(szcs)
    return run


def add_para(doc, text="", size=12, bold=False, color=None, italic=False,
             space_after=8, space_before=0, indent=None, align=None,
             font=THAI_FONT, line_spacing=1.35):
    """Add one plain paragraph. Default line spacing (1.35) and space_after
    (8pt) give prose room to breathe without looking like a template's tight
    list spacing."""
    p = doc.add_paragraph()
    if text:
        style_run(p.add_run(text), size, bold, color, italic, font)
    pf = p.paragraph_format
    pf.space_after = Pt(space_after)
    pf.space_before = Pt(space_before)
    pf.line_spacing = line_spacing
    if align is not None:
        p.alignment = align
    if indent is not None:
        pf.left_indent = Cm(indent)
    return p


def add_rich(doc, parts, size=12, space_after=8, space_before=0,
             font=THAI_FONT, line_spacing=1.35):
    """Add one paragraph built from multiple runs, e.g. to bold a single date
    or name inline without breaking the sentence into a separate line.

    parts: list of (text, bold) tuples, or (text, bold, color) tuples.
    """
    p = doc.add_paragraph()
    for part in parts:
        if len(part) == 2:
            txt, bold = part
            color = None
        else:
            txt, bold, color = part
        style_run(p.add_run(txt), size, bold, color, False, font)
    pf = p.paragraph_format
    pf.space_after = Pt(space_after)
    pf.space_before = Pt(space_before)
    pf.line_spacing = line_spacing
    return p


def add_page_break(doc):
    doc.add_page_break()


def save(doc, path):
    """Save, with a clear error if the file is open in Word (common when
    re-generating a file you just sent the user for review)."""
    try:
        doc.save(path)
    except PermissionError as e:
        raise PermissionError(
            f"Cannot write {path} — it's likely open in Word right now. "
            "Close it (or ask the user to) before regenerating."
        ) from e
    return path


if __name__ == "__main__":
    demo = new_document()
    add_para(demo, "เรียน คุณผู้อ่าน", space_after=10)
    add_para(
        demo,
        "นี่คือตัวอย่างย่อหน้าเดียวที่เขียนต่อเนื่องกันไปตามธรรมชาติ "
        "ไม่มีสัญลักษณ์ตกแต่ง ไม่มีเส้นคั่น และไม่มีตารางไฮไลต์สี "
        "โครงสร้างของเอกสารเกิดจากการขึ้นย่อหน้าใหม่และการเน้นคำสำคัญด้วยตัวหนาเป็นครั้งคราวเท่านั้น",
        space_after=10,
    )
    add_rich(demo, [
        ("ตัวอย่างการเน้นข้อความบางส่วน เช่น ", False),
        ("วันศุกร์ที่ 25 กันยายน 2569", True),
        (" โดยไม่ต้องขึ้นบรรทัดใหม่หรือใส่ไอคอนกำกับ", False),
    ], space_after=10)
    add_para(demo, "ขอแสดงความนับถือ", space_after=2)
    add_para(demo, "[ชื่อผู้เขียน]", space_after=0)
    save(demo, "human_docx_demo.docx")
    print("wrote human_docx_demo.docx")
