# -*- coding: utf-8 -*-
"""ปกหน้าแบบหนังสือจริง (แนว Packt): พื้นเข้ม ชื่อเรื่องใหญ่ ภาพศิลป์กลางปก รูปผู้เขียน + โลโก้สำนักพิมพ์ด้านล่าง

  python front_cover.py <book.json> [out.jpg]        ค่าเริ่มต้น: <โฟลเดอร์ book.json>/out/cover.jpg

- ภาพศิลป์: book.json "cover_art" หรือ <โปรเจกต์>/images/cover-plain.jpg (ภาพปกที่ยังไม่มีตัวหนังสือ)
- รูปผู้เขียน: assets/author_cutout.png (ตัดพื้นหลังด้วย rembg u2net_human_seg จาก <รูปผู้เขียน>.png)
- โลโก้: assets/logo.png + คำว่า <แบรนด์> (Grow ขาว / Genius เขียว) เขียนเป็นข้อความ
ขนาด 1600x2400 (2:3) · ห้ามใส่ letter-spacing กับข้อความไทย
"""
import colorsys, html, io, json, os, pathlib, sys
from PIL import Image

HERE = pathlib.Path(__file__).resolve().parent
SK = HERE.parent
e = html.escape


def art_path(c):
    if c.get('cover_art') and os.path.exists(c['cover_art']):
        return c['cover_art']
    proj = pathlib.Path(c['book_pdf']).resolve().parent.parent
    for n in ('images/cover-plain.jpg', 'images/cover-plain.png', 'images/cover.jpg', 'images/cover.png'):
        if (proj / n).exists():
            return str(proj / n)
    return None


def accent(img_path, default='#34D399'):
    """สีเด่นที่อิ่มตัวที่สุดของภาพศิลป์ ใช้เป็นสีเน้น (ต้องสว่างพอบนพื้นเข้ม)"""
    if not img_path:
        return default
    im = Image.open(img_path).convert('RGB').resize((64, 96))
    best, score = None, 0
    for (r, g, b) in list(im.getdata()) if not hasattr(im, 'get_flattened_data') else im.get_flattened_data():
        h, l, s = colorsys.rgb_to_hls(r / 255, g / 255, b / 255)
        sc = s * (1 - abs(l - 0.55) * 1.6)
        if sc > score and 0.35 < l < 0.8:
            best, score = (h, s), sc
    if not best:
        return default
    r, g, b = colorsys.hls_to_rgb(best[0], 0.62, min(1, max(0.65, best[1])))
    return '#%02x%02x%02x' % (int(r * 255), int(g * 255), int(b * 255))


def cover_html(c, H=2400):
    art = art_path(c)
    acc = accent(art)
    F = (SK / 'fonts' / 'kanit').as_uri(); A = (SK / 'assets').as_uri()
    # ขึ้นบรรทัดเฉพาะที่ช่องว่างในชื่อ (ห้ามให้เบราว์เซอร์ตัดกลางวลีไทย) แล้วให้ JS ย่อตัวอักษรจนทุกบรรทัดพอดีกว้าง
    t_raw, s_raw = c.get('cover_title') or c['title'], c.get('subtitle', '')   # cover_title = ชื่อบนปก ใส่ช่องว่างตรงจุดที่ยอมให้ขึ้นบรรทัดใหม่
    if not s_raw and len(t_raw) > 26:  # ชื่อยาวไม่มีชื่อรอง: ตัดหลัง ! หรือ : แรกไปเป็นชื่อรองบนปก
        import re as _re
        m = _re.match(r'^(.{4,40}?[!:])\s+(.+)$', t_raw)
        if m:
            t_raw, s_raw = m.group(1).rstrip(':'), m.group(2)
    # ตัดบรรทัดได้เฉพาะที่ช่องว่าง (แต่ละวลีห้ามแตก) แล้วให้ JS ย่อจนไม่เกิน 3 บรรทัดและไม่มีวลีล้น
    import re as _r2
    t_raw = _r2.sub(r'\(([^)]*)\)', lambda m: '(' + m.group(1).replace(' ', ' ') + ')', t_raw)  # ข้อความในวงเล็บห้ามแยกบรรทัด
    title = ' '.join(f'<span>{e(w)}</span>' for w in t_raw.split(' '))
    sub = e(s_raw)
    n = len(c['title'])
    tsize = 168 if n <= 14 else 142 if n <= 22 else 118 if n <= 34 else 98
    plain = bool(art) and 'plain' in os.path.basename(art)
    pos = 'center' if plain else c.get('cover_art_pos', 'center 72%')
    # ปกเดิมที่มีตัวหนังสือฝัง: ให้กรอบเริ่มที่ cover_art_start (สัดส่วนความสูงภาพ) ใต้ตัวหนังสือเดิมพอดี ตัวคนจะไม่โดนตัดหัว
    art_ratio = (lambda im: im.height / im.width)(Image.open(art)) if art else 1.5
    art_start = -1 if plain else float(c.get('cover_art_start', 0.37))  # ปกเดิมที่มีตัวหนังสือ: ใช้ส่วนล่าง ให้ข้อความด้านบนหลุดกรอบ
    art_tag = (f'<div class="art" style="background-image:url({pathlib.Path(art).as_uri()});background-position:{pos}"></div>' if art else '')  # as_uri เข้ารหัสช่องว่างแล้ว ไม่ต้องครอบเครื่องหมายคำพูด
    pen = f'<div class="pen">{e(c["pen_name"])}</div>' if c.get('pen_name') else ''
    scrim_h = 0
    art_top = 700  # ภาพเริ่มใต้หัวเรื่อง ขอบบนคม ไม่มีแถบไล่มืดทับ (ผู้ใช้ไม่ต้องการให้ทับหัวคนในภาพ)
    price = f'<div class="price"><small>ราคา</small>{int(c["price"])} บาท</div>' if int(c.get('price') or 0) else ''  # เล่มฟรีไม่ใส่ป้ายราคา
    return f"""<html lang="th"><head><meta charset="utf-8"><style>
@font-face{{font-family:S;font-weight:400;src:url('{F}/Kanit-Regular.ttf')}}
@font-face{{font-family:S;font-weight:600;src:url('{F}/Kanit-SemiBold.ttf')}}
@font-face{{font-family:S;font-weight:700;src:url('{F}/Kanit-Bold.ttf')}}
@font-face{{font-family:S;font-weight:800;src:url('{F}/Kanit-ExtraBold.ttf')}}
html,body{{margin:0}}
.c{{width:1600px;height:{H}px;position:relative;overflow:hidden;font-family:S;color:#fff;
   background:radial-gradient(120% 70% at 85% 55%, #16213d 0%, #0b1122 55%, #070b16 100%)}}
.art{{position:absolute;left:0;right:0;top:{art_top}px;bottom:640px;background-size:cover;background-position:center;
   opacity:1}}  /* ขอบบน-ล่างตัดตรง ไม่ไล่จาง (ผู้ใช้สั่ง) */
.scrim{{position:absolute;left:0;right:0;top:0;height:{scrim_h}px;background:linear-gradient(to bottom, rgba(7,11,22,.78) 0%, rgba(7,11,22,.45) 60%, rgba(7,11,22,0) 100%)}}
.head,.kick{{text-shadow:0 3px 10px rgba(0,0,0,.9), 0 0 28px rgba(0,0,0,.65)}}
.kick{{position:absolute;left:120px;top:120px;font-size:34px;font-weight:600;color:#cbd5e1}}
.kick b{{color:{acc};font-weight:700}}
h1{{position:absolute;left:120px;right:120px;top:190px;margin:0;font-size:{tsize}px;line-height:1.12;font-weight:800}}
h1 span{{white-space:nowrap}}
.sub{{position:absolute;left:120px;right:260px;top:auto;font-size:52px;line-height:1.45;font-weight:600;color:#e2e8f0}}
.ed{{font-size:46px;font-weight:700;color:{acc};margin-top:34px}}
.head{{position:absolute;left:120px;right:120px;top:190px}}
.head h1{{position:static}}
.head .sub{{position:static;margin-top:40px;max-width:1240px}}
.author{{position:absolute;left:70px;bottom:190px;height:430px}}
.author img{{height:100%;display:block;-webkit-mask-image:linear-gradient(to right, transparent 0%, #000 26%), linear-gradient(to bottom, #000 80%, #000 100%)}}
.names{{position:absolute;left:520px;bottom:318px;max-width:560px}}
.price{{position:absolute;right:110px;bottom:292px;background:{acc};color:#0b1122;font-size:54px;font-weight:800;padding:18px 40px;border-radius:999px;white-space:nowrap}}
.price small{{font-size:34px;font-weight:700;margin-right:10px}}
.name{{font-size:64px;font-weight:800;line-height:1.2}}
.pen{{font-size:40px;font-weight:600;color:#cbd5e1;margin-top:10px}}
.bar{{position:absolute;left:0;right:0;bottom:0;height:190px;background:rgba(3,6,14,.92);border-top:4px solid {acc}}}
.logo{{position:absolute;right:120px;bottom:48px;display:flex;align-items:center;gap:26px}}
.logo img{{height:96px}}
.logo span{{font-family:'Segoe UI',Arial,sans-serif;font-size:66px;font-weight:700}}
.logo .g{{color:#fff}} .logo .n{{color:#34D399}}
.url{{position:absolute;left:120px;bottom:70px;font-size:34px;color:#94a3b8;font-family:'Segoe UI',Arial,sans-serif}}
</style></head><body><div class="c">
{art_tag}
<div class="kick"><b>E-BOOK</b> · ฉบับ {e(c['year_be'])}</div>
<div class="head"><h1>{title}</h1><div class="sub">{sub}</div><div class="ed">พิมพ์ครั้งที่ {e(str(c['edition']))}</div></div>
<div class="author"><img src="{A}/author_cutout.png"></div>
<div class="names"><div class="name">{e(c['author_name'])}</div></div>
{price}
<div class="bar"></div>
<div class="url">myweekend.fun</div>
<div class="logo"><img src="{A}/logo.png"><span><span class="g">Grow</span><span class="n">Genius</span></span></div>
</div><script>document.fonts.ready.then(function(){{const h=document.querySelector('h1');let f=parseFloat(getComputedStyle(h).fontSize);const W=h.clientWidth;const lh=()=>parseFloat(getComputedStyle(h).lineHeight);while(f>56&&([...h.children].some(s=>s.offsetWidth>W)||h.offsetHeight>lh()*3+4)){{f-=2;h.style.fontSize=f+'px';}}const hd=document.querySelector('.head'),ar=document.querySelector('.art');if(ar){{const bt=hd.getBoundingClientRect().bottom+56;if(bt>{art_top})ar.style.top=bt+'px';}}const AS=({art_start});if(ar&&AS>=0){{const sh=ar.clientWidth*({art_ratio});ar.style.backgroundPosition='center '+(-AS*sh)+'px';}}}});</script></body></html>"""


def render(c, out_jpg, H=2400, style=None):
    from playwright.sync_api import sync_playwright
    tmp = pathlib.Path(out_jpg).resolve().with_suffix('.html')
    style = style or c.get('cover_style', 'dark')
    html_ = cover_html_light(c, H) if style == 'light' else cover_html_v3(c, H) if style == 'v3' else cover_html(c, H)
    io.open(tmp, 'w', encoding='utf-8').write(html_)
    with sync_playwright() as p:
        b = p.chromium.launch(channel='chrome')
        pg = b.new_page(viewport={'width': 1600, 'height': H})
        pg.goto(tmp.as_uri()); pg.evaluate('document.fonts.ready.then(()=>1)'); pg.wait_for_timeout(900)
        pg.screenshot(path=str(out_jpg), type='jpeg', quality=90, clip={'x': 0, 'y': 0, 'width': 1600, 'height': H})
        b.close()
    tmp.unlink()
    return out_jpg


def cover_html_light(c, H=2400):
    """แบบที่ 2 (แนวปกหนังสือขายดีไทย เช่น SE-ED): พื้นขาว ชื่อเรื่องใหญ่สองสี รูปผู้เขียนใหญ่ด้านล่าง"""
    import re as _re
    art = art_path(c)
    acc = accent(art, '#e0457b')
    F = (SK / 'fonts' / 'kanit').as_uri(); A = (SK / 'assets').as_uri()
    t_raw, s_raw = c.get('cover_title') or c['title'], c.get('subtitle', '')   # cover_title = ชื่อบนปก ใส่ช่องว่างตรงจุดที่ยอมให้ขึ้นบรรทัดใหม่
    if not s_raw and len(t_raw) > 26:
        m = _re.match(r'^(.{4,40}?[!:])\s+(.+)$', t_raw)
        if m:
            t_raw, s_raw = m.group(1).rstrip(':'), m.group(2)
    words = t_raw.split()
    first, rest = (words[0], ' '.join(words[1:])) if len(words) > 1 else (t_raw, '')
    rest = _re.sub(r'\(([^)]*)\)', lambda m: '(' + m.group(1).replace(' ', ' ') + ')', rest)
    rest_html = ' '.join(f'<span>{e(w)}</span>' for w in rest.split(' '))
    plain = bool(art) and 'plain' in os.path.basename(art)
    pos = 'center' if plain else c.get('cover_art_pos', 'center 72%')
    art_tag = (f'<div class="art" style="background-image:url({pathlib.Path(art).as_uri()});background-position:{pos}"></div>' if art else '')
    pen = f'<div class="pen">{e(c["pen_name"])}</div>' if c.get('pen_name') else ''
    return f"""<html lang="th"><head><meta charset="utf-8"><style>
@font-face{{font-family:S;font-weight:400;src:url('{F}/Kanit-Regular.ttf')}}
@font-face{{font-family:S;font-weight:600;src:url('{F}/Kanit-SemiBold.ttf')}}
@font-face{{font-family:S;font-weight:700;src:url('{F}/Kanit-Bold.ttf')}}
@font-face{{font-family:S;font-weight:800;src:url('{F}/Kanit-ExtraBold.ttf')}}
html,body{{margin:0}}
.c{{width:1600px;height:{H}px;position:relative;overflow:hidden;font-family:S;color:#141821;background:#fbfaf7}}
.art{{position:absolute;left:0;right:0;bottom:0;height:62%;background-size:cover;opacity:.55;
   -webkit-mask-image:linear-gradient(to bottom, transparent 0%, #000 45%)}}
.tag{{position:absolute;left:110px;top:110px;background:{acc};color:#fff;font-size:40px;font-weight:700;padding:14px 34px;border-radius:14px}}
.logo{{position:absolute;right:110px;top:112px;display:flex;align-items:center;gap:20px}}
.logo img{{height:78px}} .logo span{{font-family:'Segoe UI',Arial,sans-serif;font-size:54px;font-weight:700}}
.logo .g{{color:#141821}} .logo .n{{color:#16a34a}}
.head{{position:absolute;left:110px;right:110px;top:250px}}
.t1{{font-size:230px;line-height:1.08;font-weight:800;color:{acc};white-space:nowrap}}
.t2{{font-size:150px;line-height:1.12;font-weight:800;color:#141821}}
.t2 span{{white-space:nowrap}}
.sub{{font-size:54px;line-height:1.45;font-weight:600;color:#3b4252;margin-top:30px;max-width:1300px}}
.author{{position:absolute;right:0;bottom:0;height:980px}}
.author img{{height:100%;display:block;-webkit-mask-image:linear-gradient(to right, transparent 0%, #000 34%)}}
.names{{position:absolute;left:110px;bottom:160px;max-width:560px;padding:26px 30px;background:rgba(251,250,247,.9);border-radius:18px}}
.name{{font-size:74px;font-weight:800;line-height:1.2;color:#141821}}
.pen{{font-size:44px;font-weight:600;color:{acc};margin-top:8px}}
.ed{{position:absolute;left:110px;bottom:80px;font-size:34px;color:#475569}}
</style></head><body><div class="c">
{art_tag}
<div class="tag">E-BOOK · ฉบับ {e(c['year_be'])}</div>
<div class="logo"><img src="{A}/logo.png"><span><span class="g">Grow</span><span class="n">Genius</span></span></div>
<div class="head"><div class="t1">{e(first)}</div><div class="t2">{rest_html}</div><div class="sub">{e(s_raw)}</div></div>
<div class="author"><img src="{A}/author_cutout.png"></div>
<div class="names"><div class="name">{e(c['author_name'])}</div>{pen}</div>
<div class="ed">พิมพ์ครั้งที่ {e(str(c['edition']))} · myweekend.fun</div>
</div><script>(function(){{const W=document.querySelector('.head').clientWidth;
const fit=(el,min,lines)=>{{let f=parseFloat(getComputedStyle(el).fontSize);const lh=()=>parseFloat(getComputedStyle(el).lineHeight);
while(f>min&&(el.scrollWidth>W+2||[...el.children].some(s=>s.offsetWidth>W)||(lines&&el.offsetHeight>lh()*lines+4))){{f-=3;el.style.fontSize=f+'px';}}}};
fit(document.querySelector('.t1'),90,0);fit(document.querySelector('.t2'),70,2);}})();</script></body></html>"""


def cover_html_v3(c, H=2400):
    """แบบที่ 3 (ต.ค. 2569) ปรับจากปกขายดีไทย: โลโก้สำนักพิมพ์มุมซ้ายบน · ชื่อเรื่องใหญ่มีคำเน้นสี 1 คำ ·
    ชื่อผู้เขียน + บทบาทใต้ชื่อเรื่อง · ประโยคดึง (cover_hook) สีเน้นตัวใหญ่ · ภาพศิลป์เต็มกว้างไม่มีอะไรทับ ·
    แถบล่าง: รูปผู้เขียนเล็ก + ป้ายหลักฐาน (cover_proof ตัวเลขจริงเท่านั้น) + ป้ายราคาเฉพาะเล่มขาย"""
    import re as _re
    art = art_path(c)
    acc = c.get('cover_accent') or accent(art)
    F = (SK / 'fonts' / 'kanit').as_uri(); A = (SK / 'assets').as_uri()
    t_raw, s_raw = c.get('cover_title') or c['title'], c.get('subtitle', '')   # cover_title = ชื่อบนปก ใส่ช่องว่างตรงจุดที่ยอมให้ขึ้นบรรทัดใหม่
    if not s_raw and len(t_raw) > 26:
        m = _re.match(r'^(.{4,40}?[!:])\s+(.+)$', t_raw)
        if m:
            t_raw, s_raw = m.group(1).rstrip(':'), m.group(2)
    t_raw = _re.sub(r'\(([^)]*)\)', lambda m: '(' + m.group(1).replace(' ', '\u00a0') + ')', t_raw)
    aw = c.get('cover_accent_word', '')
    def word(w):
        h = e(w)
        if aw and aw in w:
            h = h.replace(e(aw), f'<b>{e(aw)}</b>', 1)
        return f'<span>{h}</span>'
    title = ' '.join(word(w) for w in t_raw.split(' '))
    hook = e(c.get('cover_hook', ''))
    sub = e(s_raw) if c.get('cover_show_subtitle', True) else ''
    proof = e(c.get('cover_proof', ''))
    role = e(c.get('author_role', 'ผู้แต่ง'))
    plain = bool(art) and 'plain' in os.path.basename(art)
    art_ratio = (lambda im: im.height / im.width)(Image.open(art)) if art else 1.5
    art_start = -1 if plain else float(c.get('cover_art_start', 0.37))
    art_tag = (f'<div class="art" style="background-image:url({pathlib.Path(art).as_uri()});background-position:center"></div>' if art else '')
    price = f'<div class="price"><small>ราคา</small>{int(c["price"])} บาท</div>' if int(c.get('price') or 0) else ''
    # 3 ต.ค. 2569 ผู้ใช้สั่ง: แถบล่างเหลือรูปผู้เขียน + ชื่อ (ชื่ออยู่ขวาของรูป ไม่ซ้อนรูป) เอาเว็บ จำนวนบท และราคาออก
    #   อยากได้ป้ายเดิมกลับมาเฉพาะเล่ม ใส่ "cover_show_meta": true ใน book.json
    meta = ((f'<div class="proof">{proof}</div>' if proof else '') + price + '<div class="url">myweekend.fun</div>') if c.get('cover_show_meta') else ''
    return f"""<html lang="th"><head><meta charset="utf-8"><style>
@font-face{{font-family:K;font-weight:400;src:url('{F}/Kanit-Regular.ttf')}}
@font-face{{font-family:K;font-weight:500;src:url('{F}/Kanit-Medium.ttf')}}
@font-face{{font-family:K;font-weight:600;src:url('{F}/Kanit-SemiBold.ttf')}}
@font-face{{font-family:K;font-weight:700;src:url('{F}/Kanit-Bold.ttf')}}
@font-face{{font-family:K;font-weight:800;src:url('{F}/Kanit-ExtraBold.ttf')}}
html,body{{margin:0}}
.c{{width:1600px;height:{H}px;position:relative;overflow:hidden;font-family:K;color:#fff;background:#0a0e1a}}
.logo{{position:absolute;left:110px;top:92px;display:flex;align-items:center;gap:18px}}
.logo img{{height:74px}} .logo span{{font-size:52px;font-weight:700}} .logo .n{{color:#34D399}}
.kick{{position:absolute;right:110px;top:112px;font-size:32px;font-weight:500;color:#cbd5e1}}
.head{{position:absolute;left:110px;right:110px;top:230px;text-shadow:0 3px 12px rgba(0,0,0,.6)}}
h1{{margin:0;font-size:150px;line-height:1.1;font-weight:800}}
h1 span{{white-space:nowrap}} h1 b{{color:{acc};font-weight:800}}
.by{{margin-top:26px;font-size:44px;font-weight:700;line-height:1.3}}
.by small{{display:block;font-size:34px;font-weight:400;color:#cbd5e1}}
.hook{{margin-top:40px;font-size:86px;line-height:1.18;font-weight:800;color:{acc}}}
.sub{{margin-top:16px;font-size:40px;line-height:1.45;font-weight:400;color:#e2e8f0;max-width:1300px}}
.art{{position:absolute;left:0;right:0;top:1000px;bottom:400px;background-size:cover}}
.bot{{position:absolute;left:0;right:0;bottom:0;height:400px;background:#0a0e1a}}
.author{{position:absolute;left:90px;bottom:60px;height:290px}}
.aname{{position:absolute;left:400px;bottom:150px;text-align:left;line-height:1.25}}
.aname b{{display:block;font-size:54px;font-weight:700}} .aname small{{display:block;font-size:36px;font-weight:400;color:#cbd5e1;margin-top:6px}}
.author img{{height:100%;display:block;-webkit-mask-image:linear-gradient(to right, transparent 0%, #000 22%), linear-gradient(to bottom, #000 82%, transparent 100%);-webkit-mask-composite:source-in}}
.proof{{position:absolute;left:900px;bottom:230px;font-size:46px;font-weight:700;color:#fff;border:3px solid {acc};border-radius:20px;padding:14px 30px;max-width:640px}}
.price{{position:absolute;right:110px;bottom:190px;background:{acc};color:#0a0e1a;font-size:58px;font-weight:800;padding:14px 42px;border-radius:999px;white-space:nowrap}}
.price small{{font-size:36px;font-weight:700;margin-right:10px}}
.url{{position:absolute;right:110px;bottom:60px;font-size:30px;color:#94a3b8}}
</style></head><body><div class="c">
{art_tag}
<div class="bot"></div>
<div class="logo"><img src="{A}/logo.png"><span>Grow<span class="n">Genius</span></span></div>
<div class="kick">E-BOOK · {e(c['year_be'])}</div>
<div class="head"><h1>{title}</h1>
{f'<div class="hook">{hook}</div>' if hook else ''}{f'<div class="sub">{sub}</div>' if sub else ''}</div>
<div class="author"><img src="{A}/author_cutout.png"></div>
<div class="aname"><b>{e(c['author_name'])}</b><small>{role}</small></div>
{meta}
</div><script>document.fonts.ready.then(function(){{
const h=document.querySelector('h1');let f=parseFloat(getComputedStyle(h).fontSize);const W=h.clientWidth;
const lh=()=>parseFloat(getComputedStyle(h).lineHeight);
while(f>70&&([...h.children].some(s=>s.offsetWidth>W)||h.offsetHeight>lh()*2+4)){{f-=3;h.style.fontSize=f+'px';}}
const hk=document.querySelector('.hook');if(hk){{let g=parseFloat(getComputedStyle(hk).fontSize);while(g>54&&hk.offsetHeight>parseFloat(getComputedStyle(hk).lineHeight)*2+4){{g-=3;hk.style.fontSize=g+'px';}}}}
const ar=document.querySelector('.art');const bt=document.querySelector('.head').getBoundingClientRect().bottom+60;
if(ar){{ar.style.top=Math.max(bt,700)+'px';const AS=({art_start});if(AS>=0){{const sh=ar.clientWidth*({art_ratio});ar.style.backgroundPosition='center '+(-AS*sh)+'px';}}}}
}});</script></body></html>"""


if __name__ == '__main__':
    cfg = pathlib.Path(sys.argv[1]).resolve()
    c = json.load(io.open(cfg, encoding='utf-8'))
    out = pathlib.Path(sys.argv[2]) if len(sys.argv) > 2 else cfg.parent / 'out' / 'cover.jpg'
    out.parent.mkdir(exist_ok=True)
    print(render(c, out), 'accent', accent(art_path(c)), 'art', art_path(c))
