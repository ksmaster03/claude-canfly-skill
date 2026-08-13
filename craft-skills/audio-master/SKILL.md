---
name: audio-master
description: >-
  Remaster / master เสียงเพลงหรือ audio ให้ดัง เนียน เหมือนเพลงค่าย ด้วย Matchering 2.0
  (reference-based mastering, CPU-only, pip) — เลือกเพลง reference ที่ master มาดีแนวเดียวกัน
  แล้ว match RMS/EQ/peak/stereo width อัตโนมัติ. Trigger เมื่อผู้ใช้พิมพ์ /audio-master หรือขอ
  "remaster เสียง / master เพลง / ทำให้เพลงดังขึ้น-เนียนขึ้น / เสียงเบา-บาง ช่วยปรับ /
  mastering / จูนเสียงเพลงให้เหมือนเพลงค่าย".
---

# /audio-master — Reference-based mastering ด้วย Matchering 2.0

ทดสอบบน Windows 11 (CPU-only, ไม่ต้องมี NVIDIA GPU). พิสูจน์แล้วกับเพลง Suno
"หมด token เหมือนหมดลม" (2026-07-15): master 3:15 เสร็จใน ~1 นาทีบน CPU.

## เครื่องมือ
- **Matchering 2.0** (`pip install matchering` — ติดตั้งแล้วใน Python 3.12 หลัก, v2.0.6, GPLv3,
  github.com/sergree/matchering). Pure NumPy/SciPy DSP — ไม่ใช้ neural net, เร็ว, deterministic,
  ไม่มีปัญหา Smart App Control (รันผ่าน python ปกติ).
- หลักการ: วิเคราะห์เพลง **reference** (เพลงค่ายที่ master มาดี) แล้วปรับ **target** ให้
  RMS / frequency response / peak / stereo width เท่ากัน. ผลลัพธ์ = ดังเท่าเพลงค่าย โทนสมดุล.

## ขั้นตอน
1. **เลือก reference** — สำคัญที่สุด. เพลงแนว/พลังงานเดียวกับ target ที่ master เชิงพาณิชย์แล้ว.
   แหล่งในเครื่อง: `$MEDIA/bgm\*.mp3` (YouTube Audio Library, master มาดี — เช่น
   "Everything (feat. Rodina & Alfie Tito)" = upbeat pop มี vocal). หรือให้ผู้ใช้ชี้เพลงอ้างอิงเอง.
2. **รัน** (target/reference รับ mp3/wav ได้ตรงๆ):
   ```python
   import matchering as mg
   mg.log(print)
   mg.process(
       target=r"<เพลงต้นฉบับ>",
       reference=r"<เพลงอ้างอิง>",
       results=[mg.pcm24(r"<out>_master_24bit.wav"),
                mg.pcm16(r"<out>_master_16bit.wav")],
   )
   ```
   ใช้ 24-bit ต่องานตัดต่อ/MV, 16-bit สำหรับแจกจ่าย. ต้องการ mp3 ก็ encode ต่อด้วย ffmpeg
   (`-c:a libmp3lame -b:a 320k`).
3. **QA**: `ffmpeg -i out.wav -af volumedetect -f null -` → mean_volume ควรขยับขึ้นจาก target เดิม
   อย่างมีนัย (เช่น -14 → -9 dB) และ max ~0 dB โดยไม่แตก; ฟังเทียบ A/B ช่วง chorus.

## Gotchas
- ⛔ target กับ reference เป็น**ไฟล์เดียวกัน/เพลงเดียวกัน**ไม่ได้ — matchering จะ error โดยตั้งใจ.
- reference แนวไม่ตรง (เช่น EDM หนักเบสกับเพลงโฟล์ค) → โทนเพี้ยน; เลือกแนวใกล้กันเสมอ.
- Matchering กู้ความถี่ที่ mp3 บีบหายไปไม่ได้ (เป็น DSP ไม่ใช่ generative) — ถ้าต้นฉบับ
  192kbps แตกมาก พิจารณา **Apollo** (JusperLee/Apollo, ผ่าน jarredou/Apollo-Colab-Inference
  รัน CPU ได้ ~2-10 นาที/เพลง) restore ก่อนแล้วค่อย master.
- ทางลัดไม่มี reference: `ffmpeg -af loudnorm=I=-9:TP=-1:LRA=8` = ดังขึ้นอย่างเดียว ไม่ปรับโทน.
- อย่าใช้ resemble-enhance / DeepFilterNet กับเพลง — เป็นโมเดล speech จะพังเสียงดนตรี.
