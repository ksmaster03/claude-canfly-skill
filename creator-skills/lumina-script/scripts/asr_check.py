# -*- coding: utf-8 -*-
# Kosin 17/10/2026 ตรวจเสียงพากย์เทียบบท: ถอดเสียงด้วย faster-whisper โดยใส่รายชื่อเฉพาะ (vocab) เป็น initial_prompt
# แล้วชี้ช่วงของบทที่ตัวถอดเสียงได้ยินไม่ตรง พร้อมเวลา และคำอังกฤษที่ได้ยินแต่ไม่อยู่ใน vocab (ชื่อที่น่าจะออกเสียงเพี้ยน)
# ใช้: python asr_check.py <voice.mp3> <บท.txt> ["Milvus, Qdrant, ..."] [clip.json]
#   clip.json (ไม่บังคับ) ใช้ตาราง "show" แปลงคำอ่านไทยกลับเป็นคำที่ตัวถอดเสียงพิมพ์ (พีจีเวกเตอร์ -> pgvector, ห้าสิบดอลลาร์ -> $50)
#   ไม่ใส่ จะเทียบเฉพาะตัวอักษรไทย ชื่ออังกฤษที่ถอดออกมาเป็นภาษาอังกฤษจะขึ้นว่า (หาย) ทั้งที่พูดถูก
#   บท.txt คือบทที่ส่งเข้า Lumina (มีแท็ก @... ได้ จะตัดออกเอง)
#   ไม่ใส่ vocab ก็ได้ แต่ชื่อแบรนด์/ชื่อคนจะถูกถอดเพี้ยนบ่อยแม้เสียงพูดถูก ทำให้แยกไม่ออกว่าเสียงผิดหรือตัวถอดผิด
# ผล: ไม่มีบรรทัด "ไม่ตรง" และไม่มีคำอังกฤษแปลกปลอม = ผ่าน
import difflib, io, re, sys
from faster_whisper import WhisperModel
sys.stdout.reconfigure(encoding="utf-8")

audio, script = sys.argv[1], sys.argv[2]
vocab = [v.strip() for v in (sys.argv[3] if len(sys.argv) > 3 else "").split(",") if v.strip()]
ref_text = re.sub(r"@\S+", " ", io.open(script, encoding="utf-8").read())
if len(sys.argv) > 4:
    import json
    for a, b in json.load(io.open(sys.argv[4], encoding="utf-8")).get("show", []):
        ref_text = ref_text.replace(a, f" {b} ")
m = WhisperModel("mobiuslabsgmbh/faster-whisper-large-v3-turbo", device="cpu", compute_type="int8")
prompt = ("Vocabulary: " + ", ".join(vocab) + ".") if vocab else None
segs, _ = m.transcribe(audio, language="th", beam_size=5, word_timestamps=True, initial_prompt=prompt)
segs = list(segs)
end = max((s.end for s in segs), default=0)
# เศษท้ายไฟล์ (0.45 วินาทีสุดท้าย) whisper มักแต่งคำขึ้นเอง ตัดทิ้ง
words = [(w.start, w.word) for s in segs for w in (s.words or []) if w.start < end - 0.45]
print("== ได้ยิน")
print("".join(w for _, w in words).strip())

keep = lambda s: re.sub(r"[^ก-ฮะาำเ-ไa-z0-9]", "", s.lower())
hyp, ht = [], []
for t, w in words:
    for ch in keep(w):
        hyp.append(ch); ht.append(t)
ref = keep(ref_text)
# ตำแหน่งตัวอักษรใน ref -> ข้อความต้นฉบับ เพื่อพิมพ์ช่วงที่ไม่ตรงเป็นคำที่อ่านออก
idx = [i for i, ch in enumerate(ref_text) if keep(ch)]
sm = difflib.SequenceMatcher(None, ref, "".join(hyp), autojunk=False)
print(f"\n== ตรงกัน {sm.ratio():.3f}")
bad = 0
for op, a1, a2, b1, b2 in sm.get_opcodes():
    if op == "equal" or (a2 - a1) + (b2 - b1) < 3:
        continue
    lo, hi = idx[max(0, a1 - 6)] if a1 < len(idx) else len(ref_text), idx[min(len(idx) - 1, a2 + 5)] + 1 if idx else 0
    t = ht[min(b1, len(ht) - 1)] if ht else 0
    print(f"ไม่ตรง {t:6.1f}s  บท: …{ref_text[lo:hi].strip()}…  |  ได้ยิน: {''.join(hyp[b1:b2]) or '(หาย)'}")
    bad += 1
eng = sorted({w.strip(" .,") for _, w in words if re.search(r"[A-Za-z]{3,}", w)})
odd = [e for e in eng if not any(e.lower() in v.lower() or v.lower() in e.lower() for v in vocab)]
print(f"\n== คำอังกฤษที่ได้ยินแต่ไม่อยู่ใน vocab: {odd if odd else 'ไม่มี'}")
print("ผ่าน" if not bad and not odd else f"ต้องตรวจ {bad} จุด + คำอังกฤษ {len(odd)} คำ")
