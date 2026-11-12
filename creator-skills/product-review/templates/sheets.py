# sheets.py <PROJ> [keys...] — ทำ contact sheet ไว้ "ดู" คลิปต้นฉบับด้วย Read ก่อนเลือกช็อต
#   คลิปสั้น (<20 วิ): 6 เฟรมต่อแถว รวม 6 คลิปต่อภาพ -> <PROJ>/sheets/grpN.jpg
#   คลิปยาว (>=20 วิ): 1 เฟรม/วินาที มีเลขวินาทีกำกับ -> <PROJ>/sheets/long_KEY_N.jpg (ใช้หา in-point)
import sys, json, subprocess as sp
from pathlib import Path
P = Path(sys.argv[1]); SD = P/"sheets"; SD.mkdir(exist_ok=True)
font = "arialbd.ttf"
if not (SD/font).exists(): sp.run(["cp", "C:/Windows/Fonts/arialbd.ttf", str(SD/font)])
V = json.load(open(P/"videos.json", encoding="utf-8"))
keys = sys.argv[2:] or [v["key"] for v in V]
short, longs = [], []
for v in V:
    if v["key"] not in keys: continue
    try: d = float(v["dur"]); w, h = map(int, v["wh"].split("x"))
    except Exception: continue
    if w < h*1.5 and not sys.argv[2:]: continue   # ข้ามเวอร์ชันมือถือ (แนวตั้ง/4:3) ถ้ามีคู่แนวนอนอยู่แล้ว
    (longs if d >= 20 else short).append((v["key"], d))
def run(args): sp.run(["ffmpeg","-v","error","-y",*args], check=True, cwd=SD)
for k, d in short:
    run(["-i", str((P/"src"/f"{k}.mp4").resolve()), "-vf",
         f"fps=6/{d},scale=320:180:force_original_aspect_ratio=decrease,pad=320:180:-1:-1,"
         f"drawtext=fontfile={font}:text='{k} %{{pts\\:hms}}':x=4:y=4:fontsize=16:fontcolor=yellow:box=1:boxcolor=black@0.6,tile=6x1",
         "-frames:v", "1", f"s_{k}.jpg"])
for i in range(0, len(short), 6):
    g = short[i:i+6]
    if len(g) == 1:   # vstack ต้องมี 2 อินพุตขึ้นไป
        sp.run(["cp", str(SD/f"s_{g[0][0]}.jpg"), str(SD/f"grp{i//6}.jpg")]); continue
    run([*sum([["-i", f"s_{k}.jpg"] for k, _ in g], []), "-filter_complex",
         "".join(f"[{j}]" for j in range(len(g))) + f"vstack={len(g)}", f"grp{i//6}.jpg"])
for k, d in longs:
    for n, st in enumerate(range(0, int(d), 72)):   # 72 วิ ต่อภาพ (8x9)
        run(["-ss", str(st), "-i", str((P/"src"/f"{k}.mp4").resolve()), "-vf",
             f"fps=1,scale=240:135,drawtext=fontfile={font}:text='%{{eif\\:t+{st}\\:d}}':x=3:y=3:fontsize=20:fontcolor=yellow:box=1:boxcolor=black@0.7,tile=8x9",
             "-frames:v", "1", f"long_{k}_{n}.jpg"])
print("\n".join(sorted(str(x) for x in SD.glob("*.jpg") if not x.name.startswith("s_"))))
