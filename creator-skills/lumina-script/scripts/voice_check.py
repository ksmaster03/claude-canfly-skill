# -*- coding: utf-8 -*-
# Kosin 17/10/2026 เทียบน้ำเสียงไฟล์ใหม่กับเสียงอ้างอิงแบบหยาบ (ค่าเฉลี่ย MFCC ช่วงที่มีเสียงพูด + ค่ากลาง F0)
# ใช้ตอนหน้า Lumina ไม่แสดงรายชื่อเสียง แล้วต้องยืนยันว่ารหัสเสียงที่เบราว์เซอร์จำไว้คือเสียงที่ต้องการ
# ใช้: python voice_check.py <ไฟล์ใหม่> [อ้างอิงเพิ่ม...]   ไม่ใส่อ้างอิงจะใช้ชุดด้านล่าง
# อ่านผล: dist ยิ่งน้อยยิ่งใกล้ ไฟล์ใหม่ควรใกล้กลุ่มโกสินทร์3 ชัดเจน 17 ต.ค. 2569 ได้ 9 ถึง 12 กับโกสินทร์3 และ 24 กับโกสินทร์2
# เป็นการเทียบด้วยเครื่อง ไม่ใช่การฟัง บอกผู้ใช้ตามนั้น
import os, sys
import numpy as np, librosa
sys.stdout.reconfigure(encoding="utf-8")

REF = {
    "โกสินทร์3 (คลิปเครดิต 15 ต.ค.)": "$WORK/tmp/claude-credit-reel/vo/lumina.mp3",
    "โกสินทร์3 (คลิป Tesla 16 ต.ค.)": "$WORK/tmp/tesla-roadster-reel/vo/lumina.mp3",
    "โกสินทร์2 (คลิป Mods 12 ต.ค.)": "~/Videos/claude-mods-reel/lumina/lumina_kosin2.mp3",
}


def feat(p):
    y, sr = librosa.load(p, sr=16000, mono=True, duration=90)
    m = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=20)
    e = librosa.feature.rms(y=y)[0]
    n = min(m.shape[1], e.shape[0])
    keep = e[:n] > np.percentile(e[:n], 40)
    f0, vf, _ = librosa.pyin(y[: sr * 40], fmin=60, fmax=300, sr=sr)
    return m[1:, :n][:, keep].mean(1), float(np.nanmedian(f0[vf])) if vf.any() else float("nan")


new = sys.argv[1]
refs = {os.path.basename(p): p for p in sys.argv[2:]} or {k: v for k, v in REF.items() if os.path.exists(v)}
a, fa = feat(new)
print("ไฟล์ใหม่ F0 %.1f Hz  %s" % (fa, new))
for k, p in refs.items():
    b, fb = feat(p)
    print("dist %6.2f  F0 %.1f Hz  %s" % (np.linalg.norm(a - b), fb, k))
