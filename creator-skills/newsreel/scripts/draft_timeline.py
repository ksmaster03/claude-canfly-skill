# -*- coding: utf-8 -*-
# สร้าง timeline.json แบบประมาณเวลา (10 ตัวอักษรต่อวินาที) ไว้ดูภาพก่อนใช้เครดิต Lumina
# ใช้: python draft_timeline.py <project_dir>
# เมื่อได้เสียงจริงแล้ว ให้รัน align.py ของ explainreel ทับ timeline.json นี้
import io
import json
import re
import sys

d = sys.argv[1]
clip = json.load(io.open(f"{d}/clip.json", encoding="utf-8"))
HEAD, TAIL, CPS = clip.get("head", 0.4), clip.get("tail", 1.4), 10.0


def show(s):
    for a, b in clip.get("show", []):
        s = s.replace(a, f" {b} ")
    return re.sub(r"\s+", " ", s).strip()


t, lines = HEAD, []
for k, l in enumerate(clip["lines"]):
    subs = []
    for p in l["say"].split("|"):
        subs.append({"t": round(t, 2), "text": show(p.replace("*", "")), "em": p.startswith("*")})
        t += max(0.35, len(re.sub(r"\s", "", p.replace("*", ""))) / CPS)
    lines.append({"id": l["id"], "start": 0.3 if k == 0 else round(subs[0]["t"] - 0.05, 2), "scene": l["scene"], "subs": subs})
for a, b in zip(lines, lines[1:] + [None]):
    a["end"] = b["start"] if b else round(t, 2)
total = round(t + TAIL, 2)
io.open(f"{d}/timeline.json", "w", encoding="utf-8", newline="\n").write(json.dumps({"total": total, "head": HEAD, "lines": lines}, ensure_ascii=False))
print("draft total", total, "วินาที ·", len(lines), "บรรทัด")
print("เวลาเริ่มของแต่ละบรรทัด:", " ".join(str(l["start"]) for l in lines))
