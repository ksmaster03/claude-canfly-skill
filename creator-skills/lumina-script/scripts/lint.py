# -*- coding: utf-8 -*-
# ตรวจบทพูดสำหรับ Lumina TTS ก่อนส่ง: แท็กถูกไหม ยาวเกินไหม เป็นธรรมชาติพอไหม
# ใช้: python lint.py <script.txt>      (exit 1 เมื่อมี ERROR)
import io, re, sys

EMO = "ปกติ มีความสุข ตื่นเต้น กระตือรือร้น ปิติยินดี อิ่มเอิบใจ ชัยชนะ ทึ่ง ประหลาดใจ เจ้าชู้ อยากรู้อยากเห็น พึงพอใจ สงบ เยือกเย็น ใจเย็น ซาบซึ้ง รักใคร่ เชื่อใจ เห็นอกเห็นใจ คาดหวัง ลึกลับ โกรธ บ้าคลั่ง เกรี้ยวกราด หงุดหงิด ปั่นป่วน ถูกคุกคาม ขยะแขยง ดูถูก อิจฉา ประชดประชัน เสียดสี เศร้า หดหู่ โศกเศร้า ผิดหวัง เจ็บปวด รู้สึกผิด เบื่อหน่าย เหนื่อย ถูกปฏิเสธ ถวิลหา อาลัยอาวรณ์ ขอโทษ ลังเล ไม่มั่นคง สับสน ยอมจำนน วิตกกังวล ตื่นตระหนก ตื่นตกใจ กลัว ภูมิใจ มั่นใจ ห่างเหิน สงสัย ครุ่นคิด มุ่งมั่น ล้อเล่น".split()
SOUND = ["@หัวเราะ", "@นึกคำ", "@คิดทบทวน", "@ครุ่นคิด", "@นึกออก", "@ประหลาดใจ"]
FILLER_WORDS = ["เอ่อ", "อ่า", "อืม", "เฮ้อ", "ฮู่ว", "เอ้อ", "อ้อ", "โห", "เฮ้ย", "อ๋อ", "เดี๋ยวนะ", "คือ", "แบบว่า", "ยังไงดี"]
LIMIT = 5000

src = io.open(sys.argv[1], encoding="utf-8").read().strip()
err, warn = [], []
tags = re.findall(r"@[^\s@]+", src)
for t in tags:
    base = re.sub(r"[.,!?]+$", "", t)
    if base in SOUND:
        continue
    m = re.match(r"@(อารมณ์|หยุดพัก|ความเร็ว|ระดับเสียง|สะกดคำ)=(.+)$", base)
    if not m:
        err.append(f"แท็กที่ Lumina ไม่รู้จัก จะถูกอ่านออกเสียง: {t}")
        continue
    k, v = m.groups()
    if k == "อารมณ์" and v not in EMO:
        err.append(f"ไม่มีอารมณ์ชื่อนี้: {t}")
    if k == "หยุดพัก" and not re.fullmatch(r"\d+(\.\d+)?(ms|s)", v):
        err.append(f"หยุดพักต้องเป็น 200ms / 500ms / 1s: {t}")
    if k in ("ความเร็ว", "ระดับเสียง"):
        try:
            f = float(v)
            lo, hi = (0.6, 1.5) if k == "ความเร็ว" else (0.5, 2.0)
            if not lo <= f <= hi:
                warn.append(f"ค่าอยู่นอกช่วงที่หน้าเว็บให้เลือก ({lo}-{hi}): {t}")
        except ValueError:
            err.append(f"ต้องเป็นตัวเลข: {t}")
for m in re.finditer(r"@\S*[^\s]@", src):
    err.append(f"แท็กติดกันไม่มีเว้นวรรค: {m.group(0)}")

spoken = re.sub(r"@[^\s@]+", "", src)
if len(src) > LIMIT:
    err.append(f"ยาว {len(src)} ตัวอักษร เกิน {LIMIT}")
if re.search(r"\d", spoken):
    err.append("มีตัวเลขในบทพูด ให้เขียนเป็นคำไทย: " + ", ".join(sorted(set(re.findall(r"\d[\d,.%]*", spoken)))[:8]))
lat = sorted(set(re.findall(r"[A-Za-z]{2,}", spoken)))
if lat:
    warn.append("มีคำอังกฤษ ให้เขียนเป็นคำอ่านไทย (สกิล tinglish): " + ", ".join(lat[:8]))
if "—" in src or "–" in src:
    warn.append("มีขีดยาว ให้ใช้เว้นวรรคหรือ ... แทน")

paras = [p for p in re.split(r"\n\s*\n", src) if p.strip()]
n_emo = len(re.findall(r"@อารมณ์=", src))
n_sound = sum(src.count(s + " ") + src.count(s + "\n") + src.endswith(s) for s in SOUND)
n_break = len(re.findall(r"@หยุดพัก=", src))
n_fill = sum(spoken.count(w) for w in FILLER_WORDS)
emos = re.findall(r"@อารมณ์=(\S+)", src)
for i, p in enumerate(paras, 1):
    if "@อารมณ์=" not in p:
        warn.append(f"ย่อหน้า {i} ไม่มีแท็กอารมณ์ เสียงจะค้างอารมณ์ของย่อหน้าก่อน")
    if re.search(r"(@(นึกคำ|คิดทบทวน|ครุ่นคิด|นึกออก))\s*$", p.strip()):
        warn.append(f"ย่อหน้า {i} จบด้วยแท็กเสียงคิด ควรมีคำพูดต่อท้าย")
for a, b in zip(emos, emos[1:]):
    pass
run = max((len(list(g)) for _, g in __import__("itertools").groupby(emos)), default=0)
if run >= 3:
    warn.append(f"อารมณ์เดียวกันติดกัน {run} ครั้ง ลองสลับให้มีขึ้นลง")
if len(set(emos)) < min(5, max(1, len(paras) // 2)):
    warn.append(f"ใช้อารมณ์แค่ {len(set(emos))} แบบ เสียงจะราบ")
sp = re.findall(r"@ความเร็ว=(\S+)", src)
if sp and float(sp[-1]) != 1.0:
    warn.append("ความเร็วไม่ได้ตั้งกลับเป็น 1.0 ก่อนจบ")
per100 = (n_sound + n_fill) * 100 / max(1, len(spoken))
if per100 < 0.35:
    warn.append("เสียงคิดและคำเอ่อน้อยมาก (ต่ำกว่า 1 จุดต่อ 300 ตัวอักษร) จะฟังเหมือนอ่านสคริปต์")
if per100 > 1.6:
    warn.append("เสียงคิดและคำเอ่อถี่เกิน (เกิน 1 จุดต่อ 60 ตัวอักษร) จะฟังเหมือนพูดติดขัด")
if n_break == 0:
    warn.append("ไม่มี @หยุดพัก เลย ไม่มีจังหวะหายใจ")
if not re.search(r"(นะ|เลย|อะ|เนี่ย|แหละ|สิ|ล่ะ|ครับ|ค่ะ|ไง)(\s|$)", spoken):
    warn.append("ไม่มีคำลงท้ายแบบภาษาพูด (นะ เลย อะ เนี่ย แหละ)")

print(f"ยาว {len(src)} ตัวอักษร (ไม่นับแท็ก {len(spoken.strip())}) · {len(paras)} ย่อหน้า · ประมาณ {len(spoken.strip()) / 12.5:.0f} วินาที")
print(f"อารมณ์ {n_emo} จุด {len(set(emos))} แบบ · เสียงคิด/หัวเราะ {n_sound} · คำเอ่อในบท {n_fill} · หยุดพัก {n_break}")
for e in err:
    print("ERROR", e)
for w in warn:
    print("WARN ", w)
print("ผ่าน" if not err else "ไม่ผ่าน")
sys.exit(1 if err else 0)
