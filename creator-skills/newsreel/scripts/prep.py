# -*- coding: utf-8 -*-
# ตรวจ clip.json ของคลิปเล่าข่าว เติมเครดิตภาพ วางแม่แบบฉาก และเขียนบทเปล่าไว้ใส่แท็ก Lumina
# ใช้: python prep.py <project_dir>
# ทำ: (1) ตรวจวลีซับ ภาพ ความยาวบท ฉากปิดท้าย  (2) เติม scene.credit จาก credits.json
#     (3) คัดลอก news.html เป็น <project_dir>/scenes.html  (4) เขียน vo_plain.txt ย่อหน้าละหนึ่งบรรทัดของ clip.json
import io
import json
import os
import re
import shutil
import sys

d = sys.argv[1]
here = os.path.dirname(os.path.abspath(__file__))
clip = json.load(io.open(f"{d}/clip.json", encoding="utf-8"))
credits = json.load(io.open(f"{d}/credits.json", encoding="utf-8")) if os.path.exists(f"{d}/credits.json") else {}
err, warn, chars, shots = [], [], 0, 0
lines = clip["lines"]
for l in lines:
    sc, say = l["scene"], l["say"]
    plain = say.replace("|", "").replace("*", "")
    chars += len(re.sub(r"\s", "", plain))
    if re.search(r"[0-9%]", plain):
        err.append(f"บรรทัด {l['id']}: say มีเลขอารบิกหรือ % ให้เขียนเป็นคำอ่าน แล้วใส่คู่แปลงใน show")
    if "—" in plain or "–" in plain:
        err.append(f"บรรทัด {l['id']}: มีขีดยาว")
    for p in say.split("|"):
        n = len(p.replace("*", "").strip())
        if n > 26:
            warn.append(f"บรรทัด {l['id']}: วลี \"{p[:30]}\" ยาว {n} ตัวอักษร (ควรไม่เกิน 26)")
    if sc["type"] == "photo":
        imgs = sc["img"] if isinstance(sc["img"], list) else [sc["img"]]
        shots += len(imgs)
        for im in imgs:
            if not os.path.exists(f"{d}/{im}"):
                err.append(f"บรรทัด {l['id']}: ไม่มีไฟล์ {im}")
            elif im not in credits and "credit" not in sc:
                warn.append(f"บรรทัด {l['id']}: {im} ไม่มีใน credits.json ต้องใส่ scene.credit เอง และยืนยันสิทธิ์ใช้ภาพ")
        if "credit" not in sc and imgs[0] in credits:
            sc["credit"] = [credits[im]["credit"] if im in credits else "" for im in imgs] if len(imgs) > 1 else credits[imgs[0]]["credit"]
    else:
        shots += 1
if lines[-1]["scene"]["type"] != "cta":
    err.append("บรรทัดสุดท้ายต้องเป็นฉาก cta ชวนกดไลก์ กดติดตาม")
sec = chars / 10.0   # Lumina เสียงโคลนพูดราว 10 ตัวอักษรต่อวินาที
print(f"บรรทัด {len(lines)} · ตัวอักษรพูด {chars} · ประมาณ {sec:.0f} วินาที · ช็อตภาพ {shots} · เฉลี่ย {sec / max(1, shots):.1f} วินาทีต่อช็อต")
if sec / max(1, shots) > 7:
    warn.append("ช็อตเฉลี่ยยาวเกิน 7 วินาที ต้นแบบอยู่ที่ราว 5 วินาที ให้เพิ่มภาพหรือใส่ img เป็นรายการหลายภาพ")
if chars > 4600:
    warn.append("บทยาวใกล้เพดาน 5,000 ตัวอักษรของ Lumina (แท็กนับด้วย) ให้แบ่งสร้างเป็นสองไฟล์แล้วต่อกัน")
io.open(f"{d}/clip.json", "w", encoding="utf-8", newline="\n").write(json.dumps(clip, ensure_ascii=False, indent=1))
shutil.copyfile(f"{here}/news.html", f"{d}/scenes.html")
io.open(f"{d}/vo_plain.txt", "w", encoding="utf-8", newline="\n").write(
    "\n".join(re.sub(r"\s+", " ", l["say"].replace("|", " ").replace("*", "")).strip() for l in lines) + "\n")
for w in warn:
    print("WARN", w)
for e in err:
    print("ERROR", e)
print("scenes.html และ vo_plain.txt พร้อมแล้ว" if not err else "แก้ ERROR ก่อนไปต่อ")
sys.exit(1 if err else 0)
