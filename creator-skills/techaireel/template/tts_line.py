# -*- coding: utf-8 -*-
"""พากย์เพิ่มทีละประโยคด้วย Gemini โดยใช้เสียงและสไตล์เดียวกับ tts_gemini.py
ใช้ตอนเติมประโยคใหม่ ไม่ต้องยิงทั้งก้อนซ้ำ   python tts_line.py <id> <ไฟล์ข้อความ.txt> <beat>
ข้อความต้องส่งเป็นไฟล์ เพราะ Git Bash กลืนอักขระไทยใน argument"""
import io, json, os, subprocess, sys
sys.path.insert(0, r"~/.claude/skills/tinglish")
from respell import make_respeller

ROOT = r"__ROOT__"
src = io.open(os.path.join(ROOT, "tts_gemini.py"), encoding="utf-8").read()
# ดึงเฉพาะค่าคงที่กับฟังก์ชัน ไม่รันลูปก้อนของไฟล์นั้น
exec(src.split("data = json.load")[0])

lid, beat = int(sys.argv[1]), sys.argv[3]
text = io.open(sys.argv[2], encoding="utf-8").read().strip()
vo = make_respeller()(text)
raw = os.path.join(RAW, "line_%02d_raw.wav" % lid)
synth(vo, raw, load_keys())

out = os.path.join(OUT, "line_%02d.wav" % lid)
trim = ("silenceremove=start_periods=1:start_threshold=-40dB:start_silence=0.06,"
        "areverse,silenceremove=start_periods=1:start_threshold=-40dB:start_silence=0.08,areverse")
subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", raw, "-af", trim, out], check=True)
dur = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", out],
                           capture_output=True, text=True).stdout)

p = os.path.join(ROOT, "script/script.json")
data = json.load(io.open(p, encoding="utf-8"))
data["lines"] = [ln for ln in data["lines"] if ln["id"] != lid]
data["lines"].append({"id": lid, "beat": beat, "text": text, "vo": vo,
                      "audio": os.path.basename(out), "dur": round(dur, 3)})
data["lines"].sort(key=lambda ln: ln["id"])
io.open(p, "w", encoding="utf-8").write(json.dumps(data, ensure_ascii=False, indent=2))
print("ประโยค %d ยาว %.2f วิ" % (lid, dur))
