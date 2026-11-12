# -*- coding: utf-8 -*-
# timeline ซ้อม (ยังไม่มีเสียง) กะเวลาทีละวลีจากจำนวนตัวอักษร ใช้ดูหน้าตาและจังหวะก่อนอัดเสียง
# ใช้: python sr_preview.py <proj> [ตัวอักษรต่อวินาที=11]
#   11 ตัวอักษร/วิ ใกล้จังหวะคลิปต้นแบบ (6.3 พยางค์/วิ)  เสียง Lumina ช้ากว่าราว 10 ตัวอักษร/วิ
# เขียนทับ <proj>/timeline.json แล้วพิมพ์เวลาที่ควรดึงภาพตรวจ (กลางฉาก และหลังเลขข้อ)
import io
import json
import re
import sys

d = sys.argv[1]
CPS = float(sys.argv[2]) if len(sys.argv) > 2 else 11.0
clip = json.load(io.open(f"{d}/clip.json", encoding="utf-8"))
HEAD, TAIL = clip.get("head", 0.4), clip.get("tail", 1.0)


def show(s):
    for a, b in clip.get("show", []):
        s = s.replace(a, f" {b} ")
    return re.sub(r"\s+", " ", s).strip()


keep = lambda s: re.sub(r"[^ก-ฮะาำเ-ไ]", "", s)
lines, t, shots = [], HEAD, []
for k, l in enumerate(clip["lines"]):
    subs, t0 = [], t
    for p in l["say"].split("|"):
        n = max(2, len(keep(p)))
        subs.append({"t": round(t - 0.08, 2), "text": show(p.replace("*", "")), "em": p.startswith("*")})
        t += n / CPS + 0.07
    t += l.get("hold", 0)
    lines.append({"id": l["id"], "start": 0.3 if k == 0 else round(t0 - 0.13, 2), "scene": l["scene"], "subs": subs})
for a, b in zip(lines, lines[1:] + [None]):
    a["end"] = b["start"] if b else round(t, 2)
    shots.append(round(a["start"] + (a["end"] - a["start"]) * 0.7, 2))
total = round(t + TAIL, 2)
io.open(f"{d}/timeline.json", "w", encoding="utf-8", newline="\n").write(
    json.dumps({"total": total, "head": HEAD, "lines": lines}, ensure_ascii=False))
# บทพูดล้วน ฉากละบรรทัด ใช้เป็นบทอ่านหน้ากล้อง (A-roll) บทตั้งต้นของ Lumina หรือป้อนเสียงซ้อม
io.open(f"{d}/vo.txt", "w", encoding="utf-8", newline="\n").write(
    "\n".join(" ".join(re.sub(r"^[~#*]+|\*", "", p).strip() for p in l["say"].split("|")) for l in clip["lines"]) + "\n")
for l in lines:
    print(l["id"], l["start"], "dur %.1f" % (l["end"] - l["start"]), l["scene"].get("frame", "split" if l["scene"].get("panel") else "close"),
          "|", l["scene"].get("kw", ""), "|", " / ".join(x["text"] for x in l["subs"])[:70])
print("total", total)
print("shots:", " ".join(str(x) for x in shots))
