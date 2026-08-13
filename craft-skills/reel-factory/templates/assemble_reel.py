# assemble_reel.py <PROJ> — ประกอบ Reel 9:16: Ken Burns + แบนเนอร์ + ซับ ASS + VO + BGM(บูสต์+ดัก) + SFX + loudnorm
# ต้องมีก่อน: <PROJ>/script.json, <PROJ>/vo_durs.json, <PROJ>/vo/*.wav, <PROJ>/img/*.png
import json, subprocess, sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

PROJ = Path(sys.argv[1])
cfg = json.load(open(PROJ/"config.json", encoding="utf-8")) if (PROJ/"config.json").exists() else {}
NAME = cfg.get("name", "Reel"); BANNER = cfg.get("banner", "")
ACCENT = tuple(cfg.get("accent", [13,148,136])); BGM = cfg.get("bgm", r"$MEDIA/edit/assets/bgm_bed.m4a")
SUBS = cfg.get("subtitles", True)  # ปิดซับล่างได้ด้วย {"subtitles": false}
IMG=PROJ/"img"; VO=PROJ/"vo"; CL=PROJ/"clips"; VID=PROJ/"vid"; CL.mkdir(exist_ok=True)
W,H,FPS=1080,1920,30; GAP=0.35
FONT=r"C:/Windows/Fonts/tahoma.ttf"; FONTB=r"C:/Windows/Fonts/tahomabd.ttf"
SFX={"title_boom":r"$MEDIA/sfx/kit/title_boom.mp3","open_whoosh":r"$MEDIA/sfx/kit/open_whoosh.mp3",
     "trans_whoosh":r"$MEDIA/sfx/kit/trans_whoosh.mp3","ding":r"$MEDIA/sfx/kit/ding.mp3"}
segs=json.load(open(PROJ/"script.json",encoding="utf-8")); durs=json.load(open(PROJ/"vo_durs.json"))
def run(c): subprocess.run(c,check=True,capture_output=True)
def dur(p): return float(subprocess.run(["ffprobe","-v","error","-show_entries","format=duration","-of","default=nw=1:nk=1",p],capture_output=True,text=True).stdout.strip())

tl=[]; t=0.0
for s in segs:
    d=durs[s["id"]]+GAP; tl.append({**s,"start":round(t,3),"dur":round(d,3)}); t+=d
total=round(t,3)

# VO track (concat + gaps)
sil=PROJ/"sil.wav"; run(["ffmpeg","-y","-f","lavfi","-i","anullsrc=r=24000:cl=mono","-t",str(GAP),str(sil)])
vlist=PROJ/"vo_list.txt"
with open(vlist,"w",encoding="utf-8") as f:
    for s in segs: f.write(f"file '{(VO/(s['id']+'.wav')).as_posix()}'\nfile '{sil.as_posix()}'\n")
vo_full=PROJ/"vo_full.wav"; run(["ffmpeg","-y","-f","concat","-safe","0","-i",str(vlist),"-c","copy",str(vo_full)])

# ต่อฐานวิดีโอต่อฉาก: ถ้ามีคลิป vid/{id}.mp4 (เช่นจาก Google Flow/Veo) ใช้คลิปนั้น (fit ความยาว VO);
# ไม่งั้น Ken Burns บนภาพนิ่ง img/{id}.png
for i,seg in enumerate(tl):
    out=str(CL/f"{seg['id']}.mp4"); d=seg["dur"]; fr=max(2,int(round(d*FPS)))
    vclip=VID/f"{seg['id']}.mp4"
    if vclip.exists():
        vd=dur(str(vclip)); fit=f"scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},setsar=1,fps={FPS},format=yuv420p"
        if vd>=d:  # ยาวกว่า -> ตัด
            run(["ffmpeg","-y","-i",str(vclip),"-t",f"{d}","-vf",fit,"-an","-c:v","libx264","-preset","medium","-crf","20","-pix_fmt","yuv420p",out])
        else:      # สั้นกว่า -> ยืด (slow) ให้พอดี
            f=round(d/vd,4)
            run(["ffmpeg","-y","-i",str(vclip),"-vf",f"setpts={f}*PTS,{fit}","-t",f"{d}","-an","-c:v","libx264","-preset","medium","-crf","20","-pix_fmt","yuv420p",out])
    else:
        img=str(IMG/f"{seg['id']}.png")
        z="min(1.0+0.0009*on,1.12)" if i%2==0 else "if(lte(on,1),1.12,max(1.12-0.0009*on,1.0))"
        vf=(f"scale=1620:2880:force_original_aspect_ratio=increase,crop=1620:2880,"
            f"zoompan=z='{z}':d={fr}:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s={W}x{H}:fps={FPS},setsar=1,format=yuv420p")
        run(["ffmpeg","-y","-loop","1","-i",img,"-t",f"{d}","-r",str(FPS),"-vf",vf,"-c:v","libx264","-preset","medium","-crf","20","-pix_fmt","yuv420p",out])
clist=PROJ/"clips_list.txt"
with open(clist,"w",encoding="utf-8") as f:
    for seg in tl: f.write(f"file '{(CL/(seg['id']+'.mp4')).as_posix()}'\n")
base=PROJ/"base.mp4"; run(["ffmpeg","-y","-f","concat","-safe","0","-i",str(clist),"-c","copy",str(base)])

# overlay banner + bottom caption box
def fnt(sz,b=True):
    try: return ImageFont.truetype(FONTB if b else FONT,sz)
    except: return ImageFont.truetype(FONT,sz)
ov=Image.new("RGBA",(W,H),(0,0,0,0)); dr=ImageDraw.Draw(ov)
ac=ACCENT+(235,)
dr.rectangle([0,150,W,250],fill=ac); dr.rectangle([0,250,W,258],fill=tuple(int(c*0.6) for c in ACCENT)+(235,))
dr.ellipse([42,180,80,218],fill=(255,255,255,255))
if BANNER: dr.text((105,176),BANNER,font=fnt(54),fill=(255,255,255,255))
if SUBS:
    dr.rectangle([0,H-470,W,H-150],fill=(0,0,0,150)); dr.rectangle([0,H-470,W,H-462],fill=ACCENT+(255,))
banner=PROJ/"overlay.png"; ov.save(banner)

# ASS overlay (libass shape ไทยถูกต้อง): หัวข้อสไลด์ seg['slide'] เสมอ + ซับ seg['cap'] ถ้า SUBS
def fmt(x):
    h=int(x//3600);m=int(x%3600//60);s=x%60; return f"{h:d}:{m:02d}:{s:05.2f}"
has_titles = any(seg.get("slide") for seg in tl)
use_ass = has_titles or SUBS
if use_ass:
    ass=PROJ/"caps.ass"
    hdr=("[Script Info]\nScriptType: v4.00+\nPlayResX: 1080\nPlayResY: 1920\nWrapStyle: 0\nScaledBorderAndShadow: yes\n\n"
         "[V4+ Styles]\nFormat: Name,Fontname,Fontsize,PrimaryColour,SecondaryColour,OutlineColour,BackColour,Bold,Italic,Underline,StrikeOut,ScaleX,ScaleY,Spacing,Angle,BorderStyle,Outline,Shadow,Alignment,MarginL,MarginR,MarginV,Encoding\n"
         "Style: Title,Tahoma,62,&H00FFFFFF,&H00FFFFFF,&H00301808,&H90000000,-1,0,0,0,100,100,0,0,1,3,2,2,90,90,520,1\n"
         "Style: Cap,Tahoma,54,&H00FFFFFF,&H00FFFFFF,&H00403010,&H80000000,-1,0,0,0,100,100,0,0,1,3,1,2,80,80,190,1\n\n"
         "[Events]\nFormat: Layer,Start,End,Style,Name,MarginL,MarginR,MarginV,Effect,Text\n")
    with open(ass,"w",encoding="utf-8") as f:
        f.write(hdr)
        for seg in tl:
            if seg.get("slide"):
                ts=seg["start"]+0.05; te=seg["start"]+seg["dur"]-0.05
                f.write(f"Dialogue: 0,{fmt(ts)},{fmt(te)},Title,,0,0,0,,{seg['slide']}\n")
            if SUBS:
                cs=seg["start"]+0.05; ce=seg["start"]+durs[seg["id"]]+0.25
                f.write(f"Dialogue: 0,{fmt(cs)},{fmt(ce)},Cap,,0,0,0,,{seg['cap']}\n")

# final: video(overlay [+ass]) + audio(VO + BGM บูสต์+ดัก + SFX) + limiter + loudnorm
if use_ass:
    ass_esc=str(ass).replace("\\","/").replace(":","\\:")
    vchain=f"[0:v][1:v]overlay=0:0[bv];[bv]ass='{ass_esc}'[v]"
else:
    vchain="[0:v][1:v]overlay=0:0[v]"
USE_BGM = bool(BGM)  # config {"bgm": false} = ปิดเพลง (เหลือ VO + SFX)
sfx_segs=[(seg,SFX[seg["sfx"]]) for seg in tl if seg.get("sfx") in SFX]
inp=["-i",str(base),"-i",str(banner),"-i",str(vo_full)]
if USE_BGM: inp+=["-i",BGM]
for seg,sp in sfx_segs: inp+=["-i",sp]
P=[vchain]
if USE_BGM:
    P.append("[2:a]aresample=48000,aformat=channel_layouts=stereo,asplit=2[vo][vokey]")
    # BGM bed ของเครื่องนี้เบามาก -> บูสต์ +12dB แล้ว duck ใต้ VO
    P.append(f"[3:a]atrim=0:{total},volume=4.0,afade=t=in:st=0:d=1.2,afade=t=out:st={total-2.5:.2f}:d=2.5,aresample=48000,aformat=channel_layouts=stereo[bg0]")
    P.append("[bg0][vokey]sidechaincompress=threshold=0.05:ratio=8:attack=20:release=350[bgd]")
    labels=["[vo]","[bgd]"]
else:
    P.append("[2:a]aresample=48000,aformat=channel_layouts=stereo[vo]")
    labels=["[vo]"]
sfx_base = 4 if USE_BGM else 3
for i,(seg,sp) in enumerate(sfx_segs):
    ms=int(seg["start"]*1000); v=0.45 if seg["sfx"]=="ding" else 0.65
    P.append(f"[{sfx_base+i}:a]adelay={ms}|{ms},volume={v},aresample=48000,aformat=channel_layouts=stereo[sfx{i}]")
    labels.append(f"[sfx{i}]")
P.append("".join(labels)+f"amix=inputs={len(labels)}:normalize=0:dropout_transition=0[mx];[mx]alimiter=limit=0.95,loudnorm=I=-14:TP=-1:LRA=11[a]")
final=PROJ/f"{NAME}_9x16.mp4"
run(["ffmpeg","-y",*inp,"-filter_complex",";".join(P),"-map","[v]","-map","[a]",
     "-c:v","libx264","-preset","medium","-crf","20","-pix_fmt","yuv420p",
     "-c:a","aac","-b:a","192k","-ar","48000","-ac","2","-movflags","+faststart","-t",str(total),str(final)])
print("FINAL", final, dur(str(final)), "s")
