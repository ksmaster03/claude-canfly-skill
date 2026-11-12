# build_music.py <PROJ> — เวอร์ชัน "ไม่มีเสียงพากย์": ตัดภาพลงบาร์ของเพลง + เล่าข้อมูลด้วยตัวหนังสือบนจอ
# อ่าน <PROJ>/config.json (ใช้ title/subtitle/credit/end_note/accent/crop/name ร่วมกับ build.py)
#      + music.json  = {"music": "<wav/mp3>", "bar": 1.7647, "phase": 0.12, "name": "..._Music"}
#      + music_script.json = [{"kicker","lines":[...],"chip","flash":bool,"shots":[[key,start,(bars)]]}, ...]
#        section สุดท้ายใส่ "rest": true = ยืดถึงจบเพลง (การ์ดปิด)
# วัด bar/phase ด้วย vdomindset/references/downbeat.py เท่านั้น อย่าคำนวณจาก BPM ที่ขอ Suno
import json, subprocess as sp, os, sys, shutil, re
from pathlib import Path
P = Path(sys.argv[1]).resolve(); SRC = P/"src"
cfg = json.load(open(P/"config.json", encoding="utf-8"))
mc = json.load(open(P/"music.json", encoding="utf-8"))
secs = json.load(open(P/"music_script.json", encoding="utf-8"))
W, H, FPS = 1920, 1080, 30
BAR, PH = mc["bar"], mc["phase"]

def probe(f):
    return float(sp.check_output(["ffprobe","-v","error","-show_entries","format=duration","-of","csv=p=0",str(f)]))
MUS = probe(mc["music"])

def crop_for(k, st):
    for r in cfg.get("crop", {}).get(k, []):
        if r.get("from", -1) <= st < r.get("to", 1e9):
            z = r["z"]; x = "0" if r.get("anchor") == "left" else "(iw-ow)/2"
            return f"crop=iw/{z}:ih/{z}:{x}:0,"
    return ""

# ---------- timeline บนกริดบาร์ ----------
bar_t = lambda b: PH + b*BAR          # เวลาของบาร์ที่ b
tl = []; b = 0
for i, s in enumerate(secs):
    nb = sum((x[2] if len(x) > 2 else 1) for x in s["shots"])
    st = 0.0 if i == 0 else bar_t(b)               # ช็อตแรกเริ่มที่ 0 (กิน phase ก่อนดาวน์บีตแรก)
    en = MUS if s.get("rest") else bar_t(b + nb)
    tl.append(dict(seg=s, b0=b, nb=nb, start=st, end=en)); b += nb
TOTAL = tl[-1]["end"]
print(f"bars {b}  music {MUS:.2f}s  video {TOTAL:.2f}s")

# ---------- shots + transitions ----------
# ทุกรอยต่อเป็น xfade ที่ "กึ่งกลางตรงบีต": ช็อตถูกเรนเดอร์ยาวเกินขอบบาร์ไปข้างละครึ่งของ transition (handle)
# ภายในหัวข้อ = crossfade สั้น (TR_IN เฟรม) · ข้ามหัวข้อ = transition เด่น (TR_SEC เฟรม) วนตามรายการ
# ช่วงที่มี "flash": true ใช้ fadewhite · ใส่ "tr": "<ชื่อ xfade>" ในช่วงเพื่อบังคับเองได้
TR_IN, TR_SEC = mc.get("tr_in_frames", 8), mc.get("tr_sec_frames", 16)      # ต้องเป็นเลขคู่
SEC_TR = mc.get("sec_transitions", ["zoomin","circleopen","slideleft","smoothup","wipeleft","radial",
                                    "hblur","smoothright","diagtl","circlecrop","slideup","squeezeh"])
shots = []   # (key, st0, B_start_frame, tr_frames_into_this, tr_name)
si = 0
for g in tl:
    s = g["seg"]; bb = g["b0"]
    for j, x in enumerate(s["shots"]):
        k, st0 = x[0], x[1]; nbx = x[2] if len(x) > 2 else 1
        B = 0 if bb == 0 else round(bar_t(bb)*FPS)
        if not shots: d, name = 0, None
        elif j == 0:
            d = TR_SEC; name = s.get("tr") or ("fadewhite" if s.get("flash") else SEC_TR[si % len(SEC_TR)]); si += 1
        else: d, name = TR_IN, "fade"
        shots.append((k, st0, B, d, name, s.get("id", "x"), j)); bb += nbx
END = round(TOTAL*FPS)
sd = P/"shots_music_tr"; sd.mkdir(exist_ok=True)
files = []
for i, (k, st0, B, d, name, sid, j) in enumerate(shots):
    nxt_B, nxt_d = (shots[i+1][2], shots[i+1][3]) if i+1 < len(shots) else (END, 0)
    head_f = d//2; nf = (nxt_B - B) + head_f + nxt_d//2
    out = sd/f"{sid}_{j}_{k}_{st0}_{nf}.mp4"; files.append(out)
    if out.exists(): continue
    vf = (f"{crop_for(k, st0)}scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},"
          f"fps={FPS},eq=saturation=1.1:contrast=1.04,format=yuv420p,settb=1/{FPS},setpts=N")
    sp.run(["ffmpeg","-v","error","-y","-stream_loop","-1","-ss",f"{st0:.3f}","-i",str(SRC/f"{k}.mp4"),
            "-vf",vf,"-frames:v",str(nf),"-an","-c:v","libx264","-preset","veryfast","-crf","16",str(out)], check=True)
# ต่อเป็นก้อนละ ~12 ช็อต (ffmpeg เปิด 100 อินพุตพร้อมกันกิน RAM) แล้วต่อก้อนด้วย xfade อีกชั้น — offset คำนวณเป็นเฟรมเป๊ะ
def chain(items, out):
    """items = [(file, offset_frames_into_this, d_frames, name)] ตัวแรก offset/d ไม่ใช้"""
    inp = []; fc = []; prev = "[0:v]"
    for i, (f, off, d, name) in enumerate(items):
        inp += ["-i", str(f)]
        if i == 0: continue
        lab = f"[c{i}]"
        fc.append(f"{prev}[{i}:v]xfade=transition={name}:duration={d/FPS:.6f}:offset={off/FPS:.6f}{lab}")
        prev = lab
    if len(items) == 1: sp.run(["ffmpeg","-v","error","-y","-i",str(items[0][0]),"-c","copy",str(out)], check=True); return
    (P/"xf.txt").write_text(";\n".join(fc))
    sp.run(["ffmpeg","-v","error","-y",*inp,"-filter_complex_script",str(P/"xf.txt"),"-map",prev,
            "-c:v","libx264","-preset","veryfast","-crf","15","-pix_fmt","yuv420p",str(out)], check=True)
CH = 12; parts = []
for c0 in range(0, len(shots), CH):
    idx = list(range(c0, min(c0+CH, len(shots))))
    base = shots[idx[0]][2] - shots[idx[0]][3]//2          # เฟรมของไฟล์ก้อนนี้เริ่มที่ (B - head)
    items = [(files[idx[0]], 0, 0, None)]
    for i in idx[1:]:
        B, d = shots[i][2], shots[i][3]
        items.append((files[i], (B - d//2) - base, d, shots[i][4]))
    out = sd/f"_part{c0//CH}.mp4"; chain(items, out); parts.append((out, base, shots[idx[0]][3], shots[idx[0]][4]))
items = [(parts[0][0], 0, 0, None)]
for f, base, d, name in parts[1:]:
    items.append((f, base, d, name))      # base = B-d/2 ของช็อตแรกในก้อน = offset ในไทม์ไลน์รวม
chain(items, P/"video_music_raw.mp4")

# ---------- ASS (ต่อแท็กด้วย r"..." เสมอ — \f \a \1 \b ใน f-string กลายเป็นอักขระควบคุม) ----------
def ts(x):
    x = max(0, x); return f"{int(x//3600)}:{int(x%3600//60):02d}:{x%60:05.2f}"
r_, g_, b_ = cfg.get("accent", [255, 107, 20]); ACC = f"&H00{b_:02X}{g_:02X}{r_:02X}"
head = f"""[Script Info]
ScriptType: v4.00+
PlayResX: {W}
PlayResY: {H}
WrapStyle: 0
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Head,Prompt ExtraBold,104,&H00FFFFFF,&H00FFFFFF,&H00000000,&H90000000,0,0,0,0,100,100,0,0,1,4,6,1,90,260,110,222
Style: Hook,Prompt ExtraBold,128,&H00FFFFFF,&H00FFFFFF,&H00000000,&H90000000,0,0,0,0,100,100,0,0,1,4,7,5,120,120,0,222
Style: Kicker,Prompt SemiBold,56,&H00FFFFFF,&H00FFFFFF,&H00101010,&H00000000,0,0,0,0,100,100,0,0,3,14,0,7,70,70,62,222
Style: Chip,Prompt SemiBold,48,&H00FFFFFF,&H00FFFFFF,&H40101010,&H00000000,0,0,0,0,100,100,0,0,3,16,0,9,70,70,112,222
Style: Credit,Prompt Medium,34,&H40FFFFFF,&H00FFFFFF,&H00000000,&HA0000000,0,0,0,0,100,100,0,0,1,1.5,1,9,48,48,30,222
Style: Title,Prompt ExtraBold,128,&H00FFFFFF,&H00FFFFFF,&H00000000,&H80000000,0,0,0,0,100,100,0,0,1,0,6,5,100,100,0,222
Style: TitleSub,Prompt SemiBold,52,&H00FFFFFF,&H00FFFFFF,&H00000000,&H80000000,0,0,0,0,100,100,0,0,1,2,3,5,100,100,0,222
Style: End,Prompt SemiBold,40,&H00FFFFFF,&H00FFFFFF,&H00000000,&H80000000,0,0,0,0,100,100,0,0,1,2,2,5,100,100,0,222

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
ev = []; FADE = r"{\fad(200,150)}"
CLUSTER = re.compile("[^ัำ-ฺ็-๎][ัำ-ฺ็-๎]*")   # อักษรฐาน + สระบน/ล่าง/วรรณยุกต์/สระอำ ห้ามแยกจากกัน
def reveal(text, dur_ms, stagger=40, fade=280, blur=10, out_ms=200, out_stagger=0, color="", t0=0):
    """ตัวอักษรขึ้นทีละตัว จากเบลอเป็นคม แล้วจางออกตอนจบ — ต่อแท็กด้วย r"..." เท่านั้น"""
    o = ""; cl = CLUSTER.findall(text)
    for i, c in enumerate(cl):
        t = t0 + i*stagger; e1 = dur_ms - (len(cl)-1-i)*out_stagger; e0 = e1 - out_ms
        o += ("{" + (r"\c" + color if color else "") + r"\alpha&HFF&\blur" + str(blur)
              + r"\t(" + f"{t},{t+fade}" + r",\alpha&H00&\blur0)\t(" + f"{e0},{e1}" + r",\alpha&HFF&\blur" + str(blur) + ")}" + c)
    return o
def ms(a, z): return int((z - a)*1000)
CREDIT = cfg.get("credit", ""); title_a, title_b = cfg["title"]
t_end0 = tl[0]["end"]
_d = ms(0.3, t_end0)
ev.append(f"Dialogue: 2,{ts(0.3)},{ts(t_end0)},Title,,0,0,0,," + r"{\pos(960,470)\fscx112\fscy112\t(0,700,\fscx100\fscy100)}"
          + reveal(f"{title_a} ", _d, stagger=60, fade=420, blur=16, out_ms=260)
          + reveal(title_b, _d, stagger=60, fade=420, blur=16, out_ms=260, color=ACC, t0=60*(len(title_a)+1)))
ev.append(f"Dialogue: 2,{ts(0.8)},{ts(t_end0)},TitleSub,,0,0,0,," + r"{\fad(300,200)\pos(960,600)}" + cfg.get("subtitle", "รีวิวละเอียด"))
if CREDIT:
    ev.append(f"Dialogue: 2,{ts(1.3)},{ts(t_end0)},TitleSub,,0,0,0,," + r"{\fad(300,200)\pos(960,680)\fs40\c" + ACC + "}" + f"โดย {CREDIT}")
    ev.append(f"Dialogue: 3,{ts(t_end0)},{ts(tl[-1]['start'])},Credit,,0,0,0,," + r"{\fad(400,300)}" + CREDIT)
FULL = r"\an7\pos(0,0)\bord0\shad0\p1}m 0 0 l 1920 0 1920 1080 0 1080{\p0}"
sec = 0
for i, g in enumerate(tl):
    s = g["seg"]; st, en = g["start"], g["end"]
    if s.get("flash"):   # แฟลชขาวตอนเพลงกลับมาแรงหลังช่วงพัก
        ev.append(f"Dialogue: 5,{ts(st)},{ts(st+0.35)},Credit,,0,0,0,," + r"{\fad(0,300)\1c&HFFFFFF&\1a&H30&" + FULL)
    if s.get("kicker"):
        sec += 1
        ev.append(f"Dialogue: 1,{ts(st+0.1)},{ts(en-0.05)},Kicker,,0,0,0,,{FADE}" + r"{\3a&H30&}{\c" + ACC + "}" + f"{sec:02d}" + r"{\c&HFFFFFF&}" + f"   {s['kicker']}")
    if s.get("chip"):
        ev.append(f"Dialogue: 1,{ts(st+0.5)},{ts(en-0.05)},Chip,,0,0,0,,{FADE}{s['chip']}")
    lines = s.get("lines", [])
    if lines:   # แบ่งบาร์ของช่วงให้แต่ละบรรทัด (ลงบาร์) แล้วเลื่อนเข้าจากซ้ายเล็กน้อย
        nb = g["nb"]; cuts = [g["b0"] + round(nb*q/len(lines)) for q in range(len(lines)+1)]
        for q, ln in enumerate(lines):
            a = st if q == 0 else bar_t(cuts[q]); z = en if q == len(lines)-1 else bar_t(cuts[q+1])
            a1, z1 = a+0.08, z-0.08
            if s.get("hook"):   # ฮุก: ตัวใหญ่กลางจอ ขึ้นทีละตัว + แถบสีแบรนด์ขีดตามใต้ข้อความ
                ev.append(f"Dialogue: 2,{ts(a1)},{ts(z1)},Hook,,0,0,0,," + r"{\pos(960,800)\fscx115\fscy115\t(0,500,\fscx100\fscy100)}"
                          + reveal(ln, ms(a1, z1), stagger=55, fade=340, blur=14, out_ms=240, out_stagger=12))
                ev.append(f"Dialogue: 1,{ts(a1+0.15)},{ts(z1)},Credit,,0,0,0,," + r"{\an5\pos(960,905)\bord0\shad0\1a&H00&\1c" + ACC
                          + r"\fscx0\t(0,450,\fscx100)\fad(0,200)\p1}m -380 -6 l 380 -6 380 6 -380 6{\p0}")
            else:
                ev.append(f"Dialogue: 0,{ts(a1)},{ts(z1)},Head,,0,0,0,," + r"{\move(60,960,90,960,0,300)}"
                          + reveal(ln, ms(a1, z1), stagger=22, fade=240, blur=8, out_ms=160))
    if s.get("rest"):   # การ์ดปิด
        e0 = st + 0.2
        ev.append(f"Dialogue: 3,{ts(e0)},{ts(en)},Credit,,0,0,0,," + r"{\fad(400,800)\1c&H000000&\1a&H50&" + FULL)
        if CREDIT:
            ev.append(f"Dialogue: 4,{ts(e0)},{ts(en)},Title,,0,0,0,," + r"{\fad(300,800)\pos(960,430)\fs96}" + CREDIT)
            ev.append(f"Dialogue: 4,{ts(e0+0.3)},{ts(en)},End,,0,0,0,," + r"{\fad(300,800)\pos(960,560)\c" + ACC + "}" + f"รีวิวโดย {CREDIT}  ·  กดติดตามได้เลย")
        if cfg.get("end_note") or mc.get("end_note"):
            ev.append(f"Dialogue: 4,{ts(e0+0.6)},{ts(en)},End,,0,0,0,," + r"{\fad(300,800)\pos(960,650)\fs30}" + mc.get("end_note", cfg.get("end_note")))
(P/"subs_music.ass").write_text(head+"\n".join(ev)+"\n", encoding="utf-8-sig")
assert not any(ord(c) < 32 and c not in "\r\n" for c in (P/"subs_music.ass").read_text(encoding="utf-8-sig")), "ASS มีอักขระควบคุม"

# ---------- final: เพลง Suno master มาแล้ว ไม่ loudnorm ซ้ำ แค่เฟดท้าย ----------
fd = P/"fonts"
if not fd.exists():
    fd.mkdir()
    for f in Path(os.path.expanduser("~/AppData/Local/Microsoft/Windows/Fonts")).glob("Prompt-*.ttf"): shutil.copy(f, fd)
os.chdir(P)
name = mc.get("name", cfg.get("name", "Product_Review_TH") + "_Music") + ".mp4"
sp.run(["ffmpeg","-v","error","-y","-i","video_music_raw.mp4","-i",mc["music"],
        "-vf","ass=subs_music.ass:fontsdir=fonts:shaping=complex,"
              f"fade=t=in:d=0.4,fade=t=out:st={TOTAL-1.5:.3f}:d=1.5",
        "-af",f"volume={mc.get('gain_db',0)}dB,afade=t=out:st={TOTAL-2.5:.3f}:d=2.5",   # gain_db = เพิ่มเกนตรง ๆ ไม่บีบไดนามิก (เช็ก peak หลังเพิ่ม)
        "-map","0:v","-map","1:a","-t",f"{TOTAL:.3f}","-c:v","libx264","-preset","medium","-crf",str(cfg.get("crf",20)),
        "-pix_fmt","yuv420p","-c:a","aac","-b:a","256k","-movflags","+faststart",name], check=True)
print("DONE", P/name, round(probe(P/name), 2), "s")
