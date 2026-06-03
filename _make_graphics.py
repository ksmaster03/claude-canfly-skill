# -*- coding: utf-8 -*-
# สร้างกราฟิกสำหรับ README: assets/banner.png, assets/structure.png, assets/flag.png
# โทน ธงชาติไทย: น้ำเงิน-ขาว-แดง | ไม่มีอีโมจิ/ไอคอน AI | วาดด้วยรูปทรง+ตัวอักษรล้วน
import os
from PIL import Image, ImageDraw, ImageFont, ImageFilter

ROOT = os.path.dirname(os.path.abspath(__file__))
ASSETS = os.path.join(ROOT, "assets")
os.makedirs(ASSETS, exist_ok=True)
S = 2  # supersample แล้วย่อ เพื่อความคมชัด

# พาเลตต์ (อิงธงชาติไทย)
NAVY   = (14, 33, 71)      # น้ำเงินเข้ม
NAVY2  = (22, 64, 127)     # น้ำเงินไล่เฉด
BLUE   = (30, 79, 163)
RED    = (200, 16, 46)     # แดง
WHITE  = (255, 255, 255)
INK    = (23, 33, 56)
GRAY   = (110, 122, 148)
LGRAY  = (224, 230, 240)
BG     = (244, 246, 251)
SOFT   = (220, 230, 250)

FONTS = "C:/Windows/Fonts/"
def font(name, size):
    for f in name:
        p = FONTS + f
        if os.path.exists(p):
            return ImageFont.truetype(p, size * S)
    return ImageFont.load_default()

# Arial Black สำหรับหัวข้ออังกฤษ, Tahoma สำหรับไทย
F_DISPLAY = lambda s: font(["ariblk.ttf", "arialbd.ttf", "tahomabd.ttf"], s)
F_TH_BOLD = lambda s: font(["tahomabd.ttf"], s)
F_TH      = lambda s: font(["tahoma.ttf"], s)

def rounded(draw, box, r, fill=None, outline=None, width=1):
    box = [v * S for v in box]  # รับพิกัดแบบ logical แล้วคูณ S ให้เอง
    draw.rounded_rectangle(box, radius=r * S, fill=fill, outline=outline, width=width * S)

def center_text(draw, cx, y, text, fnt, fill):
    w = draw.textlength(text, font=fnt)
    draw.text((cx - w / 2, y), text, font=fnt, fill=fill)
    return w

def fit_font(draw, text, maker, start, max_w):
    sz = start
    while sz > 10:
        f = maker(sz)
        if draw.textlength(text, font=f) <= max_w * S:
            return f
        sz -= 2
    return maker(10)

def draw_flag(img, x, y, w, h, border=True):
    # ธงชาติไทย สัดส่วนแถบ 1:1:2:1:1 (แดง ขาว น้ำเงิน ขาว แดง)
    x, y, w, h = x * S, y * S, w * S, h * S
    unit = h / 6
    rows = [(RED, unit), (WHITE, unit), (NAVY, unit * 2), (WHITE, unit), (RED, unit)]
    layer = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    ld = ImageDraw.Draw(layer)
    cy = 0
    for color, hh in rows:
        ld.rectangle([0, cy, w, cy + hh], fill=color)
        cy += hh
    # มุมโค้ง: ใช้ mask
    mask = Image.new("L", (w, h), 0)
    ImageDraw.Draw(mask).rounded_rectangle([0, 0, w, h], radius=8 * S, fill=255)
    img.paste(layer, (x, y), mask)
    if border:
        ImageDraw.Draw(img).rounded_rectangle([x, y, x + w, y + h], radius=8 * S,
                                              outline=WHITE, width=3 * S)

# ---------------------------------------------------------------- BANNER
def make_banner():
    W, H = 1280, 520
    img = Image.new("RGB", (W * S, H * S), NAVY)
    d = ImageDraw.Draw(img)
    # ไล่เฉดน้ำเงินแนวตั้ง
    for i in range(H * S):
        t = i / (H * S)
        c = tuple(int(NAVY[k] + (NAVY2[k] - NAVY[k]) * t) for k in range(3))
        d.line([(0, i), (W * S, i)], fill=c)
    # เส้นทแยงบางๆ เพิ่มพื้นผิว
    ov = Image.new("RGBA", (W * S, H * S), (0, 0, 0, 0))
    od = ImageDraw.Draw(ov)
    for gx in range(-H * S, W * S, 46 * S):
        od.line([(gx, 0), (gx + H * S, H * S)], fill=(255, 255, 255, 9), width=2)
    img = Image.alpha_composite(img.convert("RGBA"), ov).convert("RGB")
    d = ImageDraw.Draw(img)

    # ธงชาติไทย กลางบน
    fw, fh = 150, 100
    draw_flag(img, (W - fw) // 2, 56, fw, fh)
    d = ImageDraw.Draw(img)

    # หัวข้ออังกฤษ
    title = "CLAUDE CANFLY SKILLS"
    tf = fit_font(d, title, F_DISPLAY, 70, 1080)
    center_text(d, W // 2 * S, 196 * S, title, tf, WHITE)

    # แถบ 3 สี (แดง-ขาว-น้ำเงิน) วางใต้หัวข้อแบบมีระยะห่างชัด
    bw, bh, by = 360, 8, 292
    bx = (W - bw) // 2
    seg = bw // 3
    segs = [RED, WHITE, BLUE]
    for i, c in enumerate(segs):
        x0 = bx + i * seg
        d.rectangle([x0 * S, by * S, (x0 + seg) * S, (by + bh) * S], fill=c)

    # ซับไตเติลไทย
    center_text(d, W // 2 * S, 330 * S,
                "คลังสกิล AI สำหรับ Claude — รวม 142 สกิลพร้อมใช้งาน",
                F_TH_BOLD(30), SOFT)
    # บรรทัดล่าง
    center_text(d, W // 2 * S, 392 * S,
                "โครงสร้างมาตรฐาน Claude Code  ·  ติดตั้งเป็น /slash command ได้ทันที",
                F_TH(22), (175, 194, 232))
    center_text(d, W // 2 * S, 440 * S, "github.com/ksmaster03/claude-canfly-skill",
                F_TH(20), (130, 152, 200))

    img = img.resize((W, H), Image.LANCZOS)
    img.save(os.path.join(ASSETS, "banner.png"))
    print("banner.png")

# ---------------------------------------------------------------- STRUCTURE
def make_structure():
    W, H = 1280, 770
    img = Image.new("RGB", (W * S, H * S), BG)
    d = ImageDraw.Draw(img)

    # แถบหัวน้ำเงิน
    d.rectangle([0, 0, W * S, 116 * S], fill=NAVY)
    draw_flag(img, 60, 34, 72, 48)
    d = ImageDraw.Draw(img)
    d.text((156 * S, 30 * S), "โครงสร้างคลังสกิล Claude Canfly", font=F_TH_BOLD(34), fill=WHITE)
    d.text((156 * S, 74 * S), "142 สกิลพร้อมใช้  ·  4 ชุดเนื้อหา  ·  รวมตัวซ้ำแล้ว",
           font=F_TH(20), fill=(180, 198, 235))

    cards = [
        ("A", "อาชีพ_skill (ไทย / RIASEC)", "จัดตามบุคลิกภาพ 6 แบบ อ้างอิงอาชีพกรมการจัดหางาน", "34"),
        ("B", "Pro Bundle (หมวดสากล)", "17 หมวดธุรกิจ การตลาด ปฏิบัติการ การเงิน", "69"),
        ("C", "คำสั่งลัด Claude", "Output modes + Career/Job help (หน้า 1-2)", "20"),
        ("D", "JobsDB AI Skills", "งานที่ AI ทำแทนได้ อิงตำแหน่งงานยอดนิยม", "19"),
    ]
    mx, top, gap = 60, 150, 30
    cw = (W - mx * 2 - gap) // 2
    ch = 156

    def shadow_card(x, y, w, h, fill, outline):
        # เงาแบนบางใต้การ์ด (ไม่ใช้ GaussianBlur เพื่อความนิ่งและไม่เพี้ยน)
        d.rounded_rectangle([x * S, (y + 4) * S, (x + w) * S, (y + h + 6) * S],
                            radius=16 * S, fill=(226, 232, 242))
        d.rounded_rectangle([x * S, y * S, (x + w) * S, (y + h) * S],
                            radius=16 * S, fill=fill, outline=outline, width=2 * S)

    for i, (tag, title, desc, num) in enumerate(cards):
        col, row = i % 2, i // 2
        x = mx + col * (cw + gap)
        y = top + row * (ch + gap)
        shadow_card(x, y, cw, ch, WHITE, LGRAY)
        # แถบสีซ้าย
        d.rounded_rectangle([x * S, y * S, (x + 10) * S, (y + ch) * S], radius=5 * S, fill=NAVY)
        # ป้าย tag
        rounded(d, [x + 28, y + 30, x + 80, y + 82], 12, fill=NAVY)
        center_text(d, (x + 54) * S, (y + 38) * S, tag, F_DISPLAY(28), WHITE)
        # ชื่อ + desc
        d.text(((x + 102) * S, (y + 32) * S), title, font=F_TH_BOLD(25), fill=INK)
        d.text(((x + 102) * S, (y + 74) * S), desc, font=F_TH(17), fill=GRAY)
        # ตัวเลข + คำว่า สกิล
        nf = F_DISPLAY(40)
        nw = d.textlength(num, font=nf)
        d.text(((x + cw - 28) * S - nw, (y + 96) * S), num, font=nf, fill=RED)
        sw = d.textlength("สกิล", font=F_TH(17))
        d.text(((x + cw - 28) * S - nw - 14 * S - sw, (y + 112) * S), "สกิล", font=F_TH(17), fill=GRAY)

    # การ์ด standard เต็มความกว้าง
    y = top + 2 * (ch + gap)
    d.rounded_rectangle([mx * S, (y + 4) * S, (W - mx) * S, (y + 134) * S],
                        radius=16 * S, fill=(210, 218, 232))
    rounded(d, [mx, y, W - mx, y + 128], 16, fill=NAVY)
    draw_flag(img, mx + 28, y + 42, 66, 44)
    d = ImageDraw.Draw(img)
    d.text(((mx + 118) * S, (y + 28) * S), "standard/  —  รูปแบบมาตรฐานติดตั้งได้",
           font=F_TH_BOLD(27), fill=WHITE)
    d.text(((mx + 118) * S, (y + 72) * S),
           "ทุกสกิลในรูป <slug>/SKILL.md  ·  คัดลอกเข้า ~/.claude/skills ใช้งานทันที",
           font=F_TH(18), fill=(180, 198, 235))
    nf = F_DISPLAY(50)
    nw = d.textlength("142", font=nf)
    d.text(((W - mx - 40) * S - nw, (y + 38) * S), "142", font=nf, fill=WHITE)

    img = img.resize((W, H), Image.LANCZOS)
    img.save(os.path.join(ASSETS, "structure.png"))
    print("structure.png")

# ---------------------------------------------------------------- FLAG LOGO
def make_flag():
    W = 240
    img = Image.new("RGBA", (W * S, 160 * S), (0, 0, 0, 0))
    draw_flag(img, 0, 0, 240, 160)
    img = img.resize((W, 160), Image.LANCZOS)
    img.save(os.path.join(ASSETS, "flag.png"))
    print("flag.png")

make_banner()
make_structure()
make_flag()
print("เสร็จ — assets/")
