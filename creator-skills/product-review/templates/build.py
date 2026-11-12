# build.py <PROJ> — ประกอบคลิปรีวิวสินค้า 16:9 จากคลิปเว็บผู้ผลิต + VO + ซับ ASS + ป้ายหัวข้อ/สเปก + BGM ducking
# อ่าน <PROJ>/config.json + script.json + vo_durs.json ; คลิปต้นฉบับอยู่ที่ <PROJ>/src/<key>.mp4
# ใช้: python build.py <PROJ> [--fresh]   (--fresh = ลบช็อตเก่าทิ้ง ตัดใหม่ทั้งหมด)
import json, subprocess as sp, os, sys, re, shutil
from pathlib import Path
P = Path(sys.argv[1]).resolve(); SRC = P/"src"; FRESH = "--fresh" in sys.argv
cfg = json.load(open(P/"config.json", encoding="utf-8"))
W, H, FPS = 1920, 1080, 30
LEAD0 = cfg.get("lead0", 3.0)   # ช่วงไตเติลก่อน VO แรก
GAP = cfg.get("gap", 0.75)      # เว้นหลัง VO แต่ละช่วง
VO_IN = 0.25                    # VO เริ่มหลังภาพตัดเข้า
segs = json.load(open(P/"script.json", encoding="utf-8"))
durs = json.load(open(P/"vo_durs.json"))
SKILL = Path(__file__).resolve().parent.parent

def probe(f):
    return float(sp.check_output(["ffprobe","-v","error","-show_entries","format=duration","-of","csv=p=0",str(f)]))
srclen = {}
def slen(k):
    if k not in srclen: srclen[k] = probe(SRC/f"{k}.mp4")
    return srclen[k]

def crop_for(k, st):
    """config.crop = {"02": [{"from":88,"to":124,"z":1.34,"anchor":"left"}, {"z":1.12}]}
    ใช้ครอปจากขอบบน (ตัดซับ/ป้ายที่ฝังมาด้านล่างคลิปผู้ผลิต) — กฎแรกที่ช่วงเวลาตรงชนะ"""
    for r in cfg.get("crop", {}).get(k, []):
        if r.get("from", -1) <= st < r.get("to", 1e9):
            z = r["z"]; x = "0" if r.get("anchor") == "left" else "(iw-ow)/2"
            return f"crop=iw/{z}:ih/{z}:{x}:0,"
    return ""

# ---------- timeline ----------
t = 0.0; tl = []
for i, s in enumerate(segs):
    lead = LEAD0 if i == 0 else VO_IN
    D = lead + durs[s["id"]] + GAP + s.get("tail", 0)
    tl.append(dict(seg=s, start=t, dur=D, vo_at=t+lead)); t += D
TOTAL = t
print("TOTAL", round(TOTAL, 2))

def alloc(shots, D):
    n = len(shots); avail = [max(0.5, slen(k)-st-0.05) for k, st in shots]
    a = [D/n]*n
    for _ in range(10):
        over = sum(max(0, a[i]-avail[i]) for i in range(n))
        if over < 1e-3: break
        free = [i for i in range(n) if a[i] < avail[i]-1e-3]
        a = [min(a[i], avail[i]) for i in range(n)]
        if not free: break
        for i in free: a[i] += over/len(free)
    a[-1] += D - sum(a)   # ถ้าทุกช็อตสั้นหมด ช็อตสุดท้ายจะ loop
    return a

# ---------- shots (ลงกริดเฟรมสะสม กันภาพเลื่อนจากเสียง) ----------
sd = P/"shots"
if FRESH and sd.exists(): shutil.rmtree(sd)
sd.mkdir(exist_ok=True)
lst = []; cum = 0.0
for g in tl:
    s = g["seg"]; a = alloc(s["shots"], g["dur"])
    for j, ((k, st), d) in enumerate(zip(s["shots"], a)):
        f0 = round(cum*FPS); cum += d; nf = round(cum*FPS) - f0
        out = sd/f"{s['id']}_{j}_{k}_{st}_{nf}.mp4"; lst.append(out)   # ชื่อไฟล์ผูกกับค่า = แก้บทแล้วตัดใหม่เฉพาะช็อตที่เปลี่ยน
        if out.exists(): continue
        vf = (f"{crop_for(k, st)}scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},"
              f"fps={FPS},eq=saturation=1.06:contrast=1.02,format=yuv420p")
        sp.run(["ffmpeg","-v","error","-y","-stream_loop","-1","-ss",f"{st:.3f}","-i",str(SRC/f"{k}.mp4"),
                "-vf",vf,"-frames:v",str(nf),"-an","-c:v","libx264","-preset","veryfast","-crf","16",str(out)], check=True)
(P/"concat.txt").write_text("".join(f"file '{x.as_posix()}'\n" for x in lst))
sp.run(["ffmpeg","-v","error","-y","-f","concat","-safe","0","-i",str(P/"concat.txt"),"-c","copy",str(P/"video_raw.mp4")], check=True)

# ---------- ASS ----------
def ts(x):
    x = max(0, x); h = int(x//3600); m = int(x%3600//60); s_ = x%60
    return f"{h}:{m:02d}:{s_:05.2f}"
r_, g_, b_ = cfg.get("accent", [255, 107, 20])
ACC = f"&H00{b_:02X}{g_:02X}{r_:02X}"
head = f"""[Script Info]
ScriptType: v4.00+
PlayResX: {W}
PlayResY: {H}
WrapStyle: 2
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Sub,Prompt SemiBold,56,&H00FFFFFF,&H00FFFFFF,&H00000000,&H64000000,0,0,0,0,100,100,0,0,1,3.2,1.5,2,140,140,58,222
Style: Kicker,Prompt SemiBold,46,&H00FFFFFF,&H00FFFFFF,&H00101010,&H00000000,0,0,0,0,100,100,0,0,3,14,0,7,70,70,62,222
Style: Chip,Prompt SemiBold,40,&H00FFFFFF,&H00FFFFFF,&H40101010,&H00000000,0,0,0,0,100,100,0,0,3,16,0,9,70,70,112,222
Style: Credit,Prompt Medium,34,&H40FFFFFF,&H00FFFFFF,&H00000000,&HA0000000,0,0,0,0,100,100,0,0,1,1.5,1,9,48,48,30,222
Style: Title,Prompt ExtraBold,128,&H00FFFFFF,&H00FFFFFF,&H00000000,&H80000000,0,0,0,0,100,100,0,0,1,0,6,5,100,100,0,222
Style: TitleSub,Prompt SemiBold,52,&H00FFFFFF,&H00FFFFFF,&H00000000,&H80000000,0,0,0,0,100,100,0,0,1,2,3,5,100,100,0,222
Style: End,Prompt SemiBold,40,&H00FFFFFF,&H00FFFFFF,&H00000000,&H80000000,0,0,0,0,100,100,0,0,1,2,2,5,100,100,0,222

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
# ระวัง: แท็ก ASS อย่าง \fad \an \1c \b ใน f-string ปกติจะกลายเป็นอักขระควบคุมของ Python เงียบ ๆ
# จึงต่อสตริงแท็กด้วย r"..." เสมอ
ev = []
FADE = r"{\fad(250,200)}"
CREDIT = cfg.get("credit", "")
title_a, title_b = cfg["title"]          # ["HOVERAir", "AQUA"] คำหลังเป็นสีแบรนด์
ev.append(f"Dialogue: 2,{ts(0.4)},{ts(LEAD0+0.2)},Title,,0,0,0,," + r"{\fad(400,300)\pos(960,470)}" + f"{title_a} " + "{\\c" + ACC + "}" + title_b)
ev.append(f"Dialogue: 2,{ts(0.8)},{ts(LEAD0+0.2)},TitleSub,,0,0,0,," + r"{\fad(400,300)\pos(960,600)}" + cfg.get("subtitle", "รีวิวละเอียด"))
if CREDIT:
    ev.append(f"Dialogue: 2,{ts(1.2)},{ts(LEAD0+0.2)},TitleSub,,0,0,0,," + r"{\fad(400,300)\pos(960,680)\fs40\c" + ACC + "}" + f"โดย {CREDIT}")
    ev.append(f"Dialogue: 3,{ts(LEAD0+0.3)},{ts(tl[-1]['start']-0.1)},Credit,,0,0,0,," + r"{\fad(500,300)}" + CREDIT)
# การ์ดปิด: ฉากมืดรองหลัง + เครดิตช่อง + เครดิตแหล่งภาพ/เพลง
eg = tl[-1]; e0 = eg["vo_at"] + durs[eg["seg"]["id"]] + 0.3; e1 = eg["start"] + eg["dur"]
ev.append(f"Dialogue: 3,{ts(e0-0.2)},{ts(e1)},Credit,,0,0,0,," + r"{\fad(500,600)\an7\pos(0,0)\1c&H000000&\1a&H50&\bord0\shad0\p1}m 0 0 l 1920 0 1920 1080 0 1080{\p0}")
if CREDIT:
    ev.append(f"Dialogue: 4,{ts(e0)},{ts(e1)},Title,,0,0,0,," + r"{\fad(400,600)\pos(960,430)\fs96}" + CREDIT)
    ev.append(f"Dialogue: 4,{ts(e0+0.3)},{ts(e1)},End,,0,0,0,," + r"{\fad(400,600)\pos(960,560)\c" + ACC + "}" + f"รีวิวโดย {CREDIT}")
if cfg.get("end_note"):
    ev.append(f"Dialogue: 4,{ts(e0+0.6)},{ts(e1)},End,,0,0,0,," + r"{\fad(400,600)\pos(960,650)\fs30}" + cfg["end_note"])
sec = 0
for g in tl:
    s = g["seg"]; st, en = g["start"], g["start"]+g["dur"]
    if s.get("kicker"):
        sec += 1
        ev.append(f"Dialogue: 1,{ts(st+0.15)},{ts(en-0.1)},Kicker,,0,0,0,,{FADE}" + r"{\3a&H30&}{\c" + ACC + "}" + f"{sec:02d}" + r"{\c&HFFFFFF&}" + f"   {s['kicker']}")
    if s.get("chip"):
        ev.append(f"Dialogue: 1,{ts(st+0.8)},{ts(en-0.1)},Chip,,0,0,0,,{FADE}{s['chip']}")
    # ซับ: ท่อนคั่นด้วย | แบ่งเวลาตามจำนวนตัวอักษรที่กินที่ (ไม่นับสระบน/ล่าง วรรณยุกต์)
    parts = s["sub"].split("|"); vo0 = g["vo_at"]; vd = durs[s["id"]]
    w = [max(6, len(re.sub(r"[\u0e31\u0e34-\u0e3a\u0e47-\u0e4e\s]", "", p))) for p in parts]
    acc = vo0
    for p, wi in zip(parts, w):
        d = vd*wi/sum(w)
        ev.append(f"Dialogue: 0,{ts(acc)},{ts(acc+d-0.04)},Sub,,0,0,0,,{p}")
        acc += d
(P/"subs.ass").write_text(head+"\n".join(ev)+"\n", encoding="utf-8-sig")
assert not any(ord(c) < 32 and c not in "\r\n" for c in (P/"subs.ass").read_text(encoding="utf-8-sig")), "ASS มีอักขระควบคุม (escape ใน f-string พัง)"

# ---------- audio ----------
BG = cfg["bgm"]                       # รายการเพลง ต่อกันด้วย crossfade 3 วิ
WH = [f"$MEDIA/sfx/whoosh_0{i}.wav" for i in (1, 2, 3)]
inp = []; fc = []
for i, b in enumerate(BG):
    if i == 0 and cfg.get("bgm_skip"): inp += ["-ss", str(cfg["bgm_skip"])]   # ข้ามอินโทรเงียบของเพลงแรก
    inp += ["-i", b]
chain = "[0:a]"
for i in range(1, len(BG)):
    chain += f"[{i}:a]acrossfade=d=3:c1=tri:c2=tri"
    if i < len(BG)-1: chain += f"[b{i}];[b{i}]"
fc.append(f"{chain},atrim=0:{TOTAL:.3f},aresample=48000,aformat=channel_layouts=stereo,volume={cfg.get('bgm_vol',0.55)},"
          f"afade=t=in:d=0.8,afade=t=out:st={TOTAL-4:.3f}:d=4[bgm]" if len(BG) > 1 else
          f"[0:a]atrim=0:{TOTAL:.3f},aresample=48000,aformat=channel_layouts=stereo,volume={cfg.get('bgm_vol',0.55)},"
          f"afade=t=in:d=0.8,afade=t=out:st={TOTAL-4:.3f}:d=4[bgm]")
n = len(BG); vo_labels = []
for i, g in enumerate(tl):
    inp += ["-i", str(P/"vo"/f"{g['seg']['id']}.wav")]
    ms = int(g["vo_at"]*1000)
    fc.append(f"[{n}:a]aformat=channel_layouts=stereo,adelay={ms}|{ms}[v{i}]"); vo_labels.append(f"[v{i}]"); n += 1
fc.append("".join(vo_labels)+f"amix=inputs={len(vo_labels)}:normalize=0,asplit=2[vo][sc]")
sfx_labels = []
for i, g in enumerate(tl):
    if i == 0 or g["seg"].get("sfx") != "whoosh": continue
    inp += ["-i", WH[i % 3]]; ms = max(0, int((g["start"]-0.22)*1000))
    fc.append(f"[{n}:a]aformat=channel_layouts=stereo,aresample=48000,volume=0.45,adelay={ms}|{ms}[x{i}]"); sfx_labels.append(f"[x{i}]"); n += 1
fc.append("[bgm][sc]sidechaincompress=threshold=0.02:ratio=8:attack=20:release=450:makeup=1[bgd]")
fc.append(f"[bgd][vo]{''.join(sfx_labels)}amix=inputs={2+len(sfx_labels)}:normalize=0,alimiter=limit=0.9,"
          f"loudnorm=I=-14:TP=-1.5:LRA=11,aresample=48000,alimiter=limit=0.84:level=false,apad[aout]")   # loudnorm รอบเดียวพุ่งเกิน TP ได้ ต้องมี limiter ปิดท้าย
(P/"afilter.txt").write_text(";\n".join(fc))
sp.run(["ffmpeg","-v","error","-y",*inp,"-filter_complex_script",str(P/"afilter.txt"),"-map","[aout]",
        "-t",f"{TOTAL:.3f}","-c:a","pcm_s16le",str(P/"mix.wav")], check=True)

# ---------- final ----------
fd = P/"fonts"
if not fd.exists():
    fd.mkdir()
    for f in Path(os.path.expanduser("~/AppData/Local/Microsoft/Windows/Fonts")).glob("Prompt-*.ttf"): shutil.copy(f, fd)
os.chdir(P)   # ฟิลเตอร์ ass ต้องใช้พาธสั้นแบบ relative (พาธ C:\ ต้อง escape ยุ่งมาก)
name = cfg.get("name", "Product_Review_TH") + ".mp4"
sp.run(["ffmpeg","-v","error","-y","-i","video_raw.mp4","-i","mix.wav",
        "-vf","ass=subs.ass:fontsdir=fonts:shaping=complex,"
              f"fade=t=in:d=0.6,fade=t=out:st={TOTAL-1.2:.3f}:d=1.2",
        "-map","0:v","-map","1:a","-c:v","libx264","-preset","medium","-crf",str(cfg.get("crf",20)),"-pix_fmt","yuv420p",
        "-c:a","aac","-b:a","192k","-movflags","+faststart","-shortest",name], check=True)
print("DONE", P/name, round(probe(P/name), 2), "s")
