# make_vo.py <PROJ> — VO ด้วย edge-tts + Tinglish respell -> vo/*.wav + vo_durs.json
import json, os, sys, subprocess
from pathlib import Path
PROJ = Path(sys.argv[1])
ET = r"~/.local/bin/edge-tts.exe"; SR = 24000
cfg = json.load(open(PROJ/"config.json", encoding="utf-8")) if (PROJ/"config.json").exists() else {}
VOICE = cfg.get("voice", "th-TH-NiwatNeural")
sys.path.insert(0, r"~/.claude/skills/tinglish")
from respell import make_respeller
respell = make_respeller()
def dur(p): return float(subprocess.run(["ffprobe","-v","error","-show_entries","format=duration","-of","default=nw=1:nk=1",p],capture_output=True,text=True).stdout.strip())
vo = PROJ/"vo"; vo.mkdir(exist_ok=True)
segs = json.load(open(PROJ/"script.json", encoding="utf-8"))
env = dict(os.environ, PYTHONIOENCODING="utf-8"); durs = {}
for s in segs:
    gen = respell(s["th"]); mp3 = str(vo/f"{s['id']}.mp3"); wav = str(vo/f"{s['id']}.wav")
    subprocess.run([ET,"--voice",VOICE,"--text",gen,"--write-media",mp3], check=True, env=env, capture_output=True)
    subprocess.run(["ffmpeg","-y","-i",mp3,"-ar",str(SR),"-ac","1",wav], check=True, capture_output=True)
    durs[s["id"]] = round(dur(wav),3); print(f"[{s['id']}] {durs[s['id']]}s :: {gen}")
json.dump(durs, open(PROJ/"vo_durs.json","w"), indent=2)
print("VO DONE total", round(sum(durs.values()),1), "s")
