# -*- coding: utf-8 -*-
# add_intro.py <proj> : ใส่ฉากเปิดท่อนเพลง (ไม่มีเสียงพูด) ไว้หน้าคลิป หลังรัน align.py แล้ว
#   อ่าน clip.json ช่อง "intro": {"dur": 6.5, "scene": {...ฉาก mv ไม่มี who...}}
#   เลื่อนทุกบรรทัดใน timeline.json ไป dur วินาที และแทรกฉากเปิดเป็นบรรทัดแรก (id 0) เขียน head ใหม่ให้ mix ใส่ช่องว่างหน้าเสียงพากย์
#   รันซ้ำไม่ได้ (เช็กจาก id 0) ต้องรัน align.py ใหม่ก่อน
# สร้าง 20 ต.ค. 2569: ผู้ใช้ให้เปิดคลิปด้วยเพลงจริงจากคลัง TikTok แล้วเฟดออกก่อนเสียงพูด ห้ามทับเสียงพูด
import io
import json
import sys

d = sys.argv[1]
clip = json.load(io.open(f"{d}/clip.json", encoding="utf-8"))
intro = clip.get("intro")
if not intro:
    sys.exit("clip.json ไม่มีช่อง intro")
D = float(intro["dur"])
tl = json.load(io.open(f"{d}/timeline.json", encoding="utf-8"))
L = tl["lines"]
if L and L[0]["id"] == 0:
    sys.exit("timeline.json มีฉากเปิดอยู่แล้ว รัน align.py ใหม่ก่อน")
for l in L:
    for s in l["subs"]:
        s["t"] = round(s["t"] + D, 2)
    l["start"] = round(l["start"] + D, 2)
    l["end"] = round(l["end"] + D, 2)
# บรรทัดแรกเดิมเริ่มที่ 0.3 แบบตายตัว ให้เริ่มตรงวลีแรกจริง ฉากเปิดจะได้ค้างจนเสียงพูดเริ่ม
L[0]["start"] = round(L[0]["subs"][0]["t"] - 0.05, 2)
first = {"id": 0, "start": 0.0, "end": L[0]["start"], "scene": intro["scene"],
         "subs": [{"t": 0.0, "text": "", "em": False}], "sub": ""}
tl["lines"] = [first] + L
tl["head"] = round(tl.get("head", 0.4) + D, 2)
tl["total"] = round(tl["total"] + D, 2)
tl["intro"] = D
io.open(f"{d}/timeline.json", "w", encoding="utf-8", newline="\n").write(json.dumps(tl, ensure_ascii=False))
print(f"ฉากเปิด {D}s · เสียงพูดเริ่ม {L[0]['subs'][0]['t']}s · total {tl['total']}s")
