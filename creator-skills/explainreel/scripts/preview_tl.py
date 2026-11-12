# -*- coding: utf-8 -*-
# Kosin 17/10/2026 timeline สมมติ ฉากละ N วินาที ใช้ตรวจหน้าตาฉากก่อนมีเสียงจริง (เขียนทับ <proj>/timeline.json ใช้ในโฟลเดอร์ซ้อมเท่านั้น)
# ใช้: python preview_tl.py <proj> [วินาทีต่อฉาก=8]   แล้ว render_range.py <proj> shots <out> ที่เวลา start+0.85*ฉาก
import io, json, re, sys
d = sys.argv[1]
L = float(sys.argv[2]) if len(sys.argv) > 2 else 8.0
clip = json.load(io.open(f"{d}/clip.json", encoding="utf-8"))
def show(s):
    for a, b in clip.get("show", []):
        s = s.replace(a, f" {b} ")
    return re.sub(r"\s+", " ", s).strip()
lines, t = [], 0.3
for l in clip["lines"]:
    ph = l["say"].split("|")
    subs = [{"t": round(t + i * (L - 1) / len(ph), 2), "text": show(p.replace("*", "")), "em": p.startswith("*")} for i, p in enumerate(ph)]
    lines.append({"id": l["id"], "start": round(t, 2), "end": round(t + L, 2), "scene": l["scene"], "subs": subs})
    t += L
io.open(f"{d}/timeline.json", "w", encoding="utf-8", newline="\n").write(json.dumps({"total": round(t + 1.5, 2), "head": 0.4, "lines": lines}, ensure_ascii=False))
print("total", round(t, 2), "· เวลาภาพตรวจ:", " ".join("%.1f" % (x["start"] + 0.85 * L) for x in lines))
