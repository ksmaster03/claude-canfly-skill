# -*- coding: utf-8 -*-
# เขียนบท Lumina ทีละบรรทัดจาก <proj>/clip.json  ได้ <proj>/vo/lines/NN_<who>.txt
# ข้อความพูด = say ตัด | และ * ออก  ต่อหน้าด้วย line["tag"] (แท็กอารมณ์ เช่น "@อารมณ์=ครุ่นคิด @ความเร็ว=0.8")
# line["pause"] = {"<เลขวลีนับจาก 0>": "500ms"} ใส่ @หยุดพัก หลังวลีนั้น  ถ้ามี @ความเร็ว ที่ไม่ใช่ 1.0 จะตั้งกลับให้ท้ายบรรทัด
# line["tags"] = {"<เลขวลีนับจาก 0>": "@ความเร็ว=1.0 @อารมณ์=เชื่อใจ"} แท็กกลางบรรทัดหลังวลีนั้น (30 ต.ค. 2569 ท่อนแร็ปของพี่ไมค์) ห้ามใส่แท็กใน say เพราะ say ขึ้นเป็นซับ
# ใช้: python make_vo_lines.py <proj>
import io, json, os, sys
sys.stdout.reconfigure(encoding="utf-8")
D = os.path.abspath(sys.argv[1])
clip = json.load(io.open(f"{D}/clip.json", encoding="utf-8"))
os.makedirs(f"{D}/vo/lines", exist_ok=True)
total = 0
for l in clip["lines"]:
    ph = [p.replace("*", "") for p in l["say"].split("|")]
    if "@" in l["say"]: sys.exit(f"บรรทัด {l['id']}: มีแท็กใน say ให้ย้ายไปช่อง tags")
    pause = {int(k): v for k, v in l.get("pause", {}).items()}
    mid = {int(k): v for k, v in l.get("tags", {}).items()}
    out = []
    for i, p in enumerate(ph):
        out.append(p)
        if i in pause:
            out.append(f"@หยุดพัก={pause[i]}")
        if i in mid:
            out.append(mid[i])
    tag = l.get("tag", "@อารมณ์=ปกติ")
    txt = tag + " " + " ".join(out)
    last_speed = ([x for x in [tag] + [mid[k] for k in sorted(mid)] if "@ความเร็ว=" in x] or [""])[-1]
    if "@ความเร็ว=" in last_speed and "@ความเร็ว=1.0" not in last_speed:
        txt += " @ความเร็ว=1.0"
    who = l["scene"]["who"]
    io.open(f"{D}/vo/lines/{l['id']:02d}_{who}.txt", "w", encoding="utf-8", newline="\n").write(txt + "\n")
    n = len("".join(ph).replace(" ", ""))
    total += n
    print(f"{l['id']:02d} {who} {n:3d}  {txt}")
print("ตัวอักษรพูดรวม", total, "≈", round(total / 10), "วินาที (กะ 10 ตัวอักษรต่อวินาที)")
