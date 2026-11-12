# make_vo.py <PROJ> — เสียงพากย์ AI ด้วย edge-tts (ดีฟอลต์ th-TH-NiwatNeural +6%) -> vo/<id>.wav + vo_durs.json
# ใช้ช่อง "th" ของ script.json ตรง ๆ (ไม่ผ่าน Tinglish) — ให้เขียนคำอ่านไทยของชื่อสินค้า/ศัพท์อังกฤษลงไปเอง
# ตัดความเงียบหัว-ท้ายออก เพื่อให้ timeline ของ build.py แม่น
import json, subprocess as sp, os, sys, concurrent.futures as cf
from pathlib import Path
P = Path(sys.argv[1]); (P/"vo").mkdir(exist_ok=True)
ET = r"~/.local/bin/edge-tts.exe"
cfg = json.load(open(P/"config.json", encoding="utf-8")) if (P/"config.json").exists() else {}
VOICE = cfg.get("voice", "th-TH-NiwatNeural"); RATE = cfg.get("rate", "+6%")
segs = json.load(open(P/"script.json", encoding="utf-8"))
only = set(sys.argv[2:])
env = dict(os.environ, PYTHONIOENCODING="utf-8")
def one(s):
    i = s["id"]; txt = P/"vo"/f"{i}.txt"; wav = P/"vo"/f"{i}.wav"
    same = txt.exists() and txt.read_text(encoding="utf-8") == s["th"] and wav.exists()
    if not same or i in only:
        txt.write_text(s["th"], encoding="utf-8")   # ส่งผ่านไฟล์ (-f) ไม่ใช่ argument: Git Bash กลืนอักษรไทย
        sp.run([ET, "--voice", VOICE, f"--rate={RATE}", "-f", str(txt), "--write-media", str(P/"vo"/f"{i}.mp3")], check=True, env=env, capture_output=True)
        sp.run(["ffmpeg","-y","-v","error","-i",str(P/"vo"/f"{i}.mp3"),"-af",
                "silenceremove=start_periods=1:start_threshold=-50dB,areverse,silenceremove=start_periods=1:start_threshold=-50dB,areverse",
                "-ar","48000","-ac","1",str(wav)], check=True)
    d = float(sp.check_output(["ffprobe","-v","error","-show_entries","format=duration","-of","csv=p=0",str(wav)]))
    return i, round(d, 3)
with cf.ThreadPoolExecutor(5) as ex: durs = dict(ex.map(one, segs))
json.dump(durs, open(P/"vo_durs.json", "w"), indent=1)
print(durs); print("VO total", round(sum(durs.values()), 1), "s")
