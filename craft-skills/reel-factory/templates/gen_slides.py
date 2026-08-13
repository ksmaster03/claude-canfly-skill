# gen_slides.py <PROJ> — สร้างสไลด์กราฟิกบนแบรนด์ (fallback เมื่อ image provider ล่ม)
# ออกภาพ 1080x1920 ต่อ segment ที่ img/{id}.png : gradient + glow + ไอคอนวาดมือ + คีย์เวิร์ดสั้น
# อ่าน script.json: seg.get("slide") = ข้อความสั้นบนสไลด์, seg.get("icon") = ชนิดไอคอน
#   icon: orb | modules | folder | doc_head | doc_steps | terminal (ไม่ระบุ = วนตามลำดับ)
import json, sys, math
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageFilter

PROJ = Path(sys.argv[1])
cfg = json.load(open(PROJ/"config.json", encoding="utf-8")) if (PROJ/"config.json").exists() else {}
ACCENT = tuple(cfg.get("accent", [198,96,63]))
W, H = 1080, 1920
FONT = r"C:/Windows/Fonts/tahoma.ttf"; FONTB = r"C:/Windows/Fonts/tahomabd.ttf"
WHITE = (245,242,238)
def light(c, f): return tuple(min(255,int(v+(255-v)*f)) for v in c)
def dark(c, f): return tuple(int(v*f) for v in c)

def fnt(sz, b=True):
    try: return ImageFont.truetype(FONTB if b else FONT, sz)
    except: return ImageFont.truetype(FONT, sz)

def gradient_bg():
    top = dark(ACCENT, 0.16); bot = dark(ACCENT, 0.42)
    img = Image.new("RGB", (W, H), top)
    px = img.load()
    for y in range(H):
        t = y / (H-1)
        col = tuple(int(top[i] + (bot[i]-top[i])*t) for i in range(3))
        for x in range(W): px[x, y] = col
    # radial clay glow behind icon
    glow = Image.new("L", (W, H), 0); gd = ImageDraw.Draw(glow)
    gd.ellipse([W//2-430, 620, W//2+430, 1160], fill=200)
    glow = glow.filter(ImageFilter.GaussianBlur(140))
    tint = Image.new("RGB", (W, H), light(ACCENT, 0.25))
    img = Image.composite(tint, img, glow)
    return img

# ---- icon drawers (วาดในกรอบ ~ cx,cy รัศมี R) ----
def rr(d, box, r, **kw): d.rounded_rectangle(box, radius=r, **kw)

def ic_orb(d, cx, cy, R):
    d.ellipse([cx-R, cy-R, cx+R, cy+R], fill=light(ACCENT,0.15), outline=WHITE, width=6)
    d.ellipse([cx-R*0.5, cy-R*0.5, cx+R*0.2, cy+R*0.2], fill=light(ACCENT,0.55))
    for a in range(0, 360, 45):  # sparkle rays
        x = cx + math.cos(math.radians(a))*(R+40); y = cy + math.sin(math.radians(a))*(R+40)
        d.line([cx+math.cos(math.radians(a))*(R+14), cy+math.sin(math.radians(a))*(R+14), x, y], fill=WHITE, width=5)

def ic_modules(d, cx, cy, R):
    s = int(R*0.82); g = int(R*0.16)
    pos = [(-1,-1),(0,-1,1),(-1,0),(0,0)]
    coords = [(-s-g//2,-s-g//2),(g//2,-s-g//2),(-s-g//2,g//2),(g//2,g//2)]
    for i,(dx,dy) in enumerate(coords):
        hot = (i==3)
        rr(d,[cx+dx,cy+dy,cx+dx+s,cy+dy+s],26,
           fill=light(ACCENT,0.55) if hot else dark(ACCENT,0.75),
           outline=WHITE, width=5)

def ic_folder(d, cx, cy, R):
    w=int(R*1.7); h=int(R*1.15); x=cx-w//2; y=cy-h//2+20
    d.polygon([(x,y),(x+w*0.34,y),(x+w*0.44,y-34),(x+w,y-34)], fill=dark(ACCENT,0.7))  # tab-less top
    rr(d,[x,y,x+w,y+h],28, fill=light(ACCENT,0.28), outline=WHITE, width=6)
    # single document peeking
    dw=int(w*0.42); dh=int(h*0.7); dx=cx-dw//2; dy=y-dh//2
    rr(d,[dx,dy,dx+dw,dy+dh],16, fill=WHITE)
    for i in range(3): d.line([dx+18,dy+30+i*26,dx+dw-18,dy+30+i*26], fill=dark(ACCENT,0.6), width=6)

def ic_doc_head(d, cx, cy, R):
    w=int(R*1.25); h=int(R*1.7); x=cx-w//2; y=cy-h//2
    rr(d,[x,y,x+w,y+h],22, fill=WHITE, outline=light(ACCENT,0.2), width=4)
    rr(d,[x+16,y+16,x+w-16,y+16+int(h*0.22)],14, fill=light(ACCENT,0.5))  # highlighted head
    for i in range(4): d.line([x+22,y+int(h*0.42)+i*30,x+w-22,y+int(h*0.42)+i*30], fill=dark(ACCENT,0.55), width=6)

def ic_doc_steps(d, cx, cy, R):
    w=int(R*1.25); h=int(R*1.7); x=cx-w//2; y=cy-h//2
    rr(d,[x,y,x+w,y+h],22, fill=WHITE, outline=light(ACCENT,0.2), width=4)
    for i in range(4):
        yy=y+34+i*int((h-60)/4)
        d.ellipse([x+22,yy,x+22+22,yy+22], fill=light(ACCENT,0.5))
        d.line([x+60,yy+11,x+w-24,yy+11], fill=dark(ACCENT,0.5), width=7)

def ic_terminal(d, cx, cy, R):
    w=int(R*1.8); h=int(R*1.25); x=cx-w//2; y=cy-h//2
    rr(d,[x,y,x+w,y+h],22, fill=dark(ACCENT,0.35), outline=WHITE, width=6)
    d.rectangle([x,y+8,x+w,y+46], fill=dark(ACCENT,0.55))
    for i,c in enumerate([(231,111,81),(244,180,90),(120,200,120)]):
        d.ellipse([x+22+i*34,y+18,x+22+i*34+18,y+36], fill=c)
    d.text((x+30,y+74), ">_", font=fnt(96), fill=light(ACCENT,0.7))
    # check badge
    bx,by=x+w-70,y+h-70
    d.ellipse([bx-46,by-46,bx+46,by+46], fill=(120,200,120))
    d.line([bx-22,by,bx-4,by+20], fill=WHITE, width=10); d.line([bx-4,by+20,bx+26,by-20], fill=WHITE, width=10)

ICONS = {"orb":ic_orb,"modules":ic_modules,"folder":ic_folder,"doc_head":ic_doc_head,"doc_steps":ic_doc_steps,"terminal":ic_terminal}
ORDER = ["orb","modules","folder","doc_head","doc_steps","terminal"]

def wrap(d, text, font, maxw):
    words = text.split(); lines=[]; cur=""
    for w0 in words:
        t=(cur+" "+w0).strip()
        if d.textlength(t, font=font) <= maxw: cur=t
        else: lines.append(cur); cur=w0
    if cur: lines.append(cur)
    return lines

segs = json.load(open(PROJ/"script.json", encoding="utf-8"))
IMG = PROJ/"img"; IMG.mkdir(exist_ok=True)
for i, seg in enumerate(segs):
    img = gradient_bg(); d = ImageDraw.Draw(img)
    icon = seg.get("icon") or ORDER[i % len(ORDER)]
    ICONS.get(icon, ic_orb)(d, W//2, 880, 210)
    # NOTE: ตัวหนังสือหัวข้อ (seg['slide']) render ผ่าน libass ใน assemble_reel.py
    # (PIL ไม่มี raqm บนเครื่องนี้ -> วรรณยุกต์/สระซ้อนไทยหาย) วาดแค่พื้นหลัง+ไอคอน
    if seg.get("slide"):
        d.line([W//2-70,1150,W//2+70,1150], fill=light(ACCENT,0.5), width=8)
    img.save(IMG/f"{seg['id']}.png")
    print(f"[slide] {seg['id']} icon={icon} :: {seg.get('slide','')}")
print("SLIDES DONE", len(segs))
