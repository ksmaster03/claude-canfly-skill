---
name: pptx-embed-video
description: ฝังคลิปที่เล่นเองลงเด็ค PowerPoint ที่มีอยู่ ต่อเด็คอื่นท้ายเล่ม และเลื่อนเลขหน้าให้ต่อกัน ด้วย python-pptx + PowerPoint COM. Trigger เมื่อพิมพ์ /pptx-embed-video หรือขอ "ใส่คลิปในสไลด์ / ฝังวิดีโอใน pptx / ให้วิดีโอเล่นเอง / นำสไลด์นี้มาต่อท้าย / รวมสองเด็ค".
---

# /pptx-embed-video: ใส่คลิปในเด็คเดิม แล้วต่อเด็คอื่นท้ายเล่ม

ใช้เมื่อมีเด็ค .pptx อยู่แล้ว และต้องเพิ่มสไลด์วิดีโอหรือรวมเด็ค โดยไม่สร้างเด็คใหม่ ทดสอบแล้วกับเด็คบริษัท 24 สไลด์ที่ต่อท้ายด้วยเด็คอีกฉบับ 41 สไลด์

ต้องมี: Windows ที่ติดตั้ง PowerPoint · `python-pptx` · ไฟล์ปลายทางต้องปิดอยู่ ถ้าผู้ใช้เปิดค้างให้ขอให้ปิดก่อน · เขียนไฟล์ผลลัพธ์ชื่อใหม่เสมอ ห้ามทับต้นฉบับ

## ลำดับงาน

1. **บีบคลิป** ให้เด็คเปิดลื่น (120 วิ ได้ 29.3 MiB)
   ```bash
   ffmpeg -v error -y -i in.mp4 -c:v libx264 -preset slow -crf 25 -pix_fmt yuv420p -profile:v high -level 4.1 -c:a aac -b:a 160k -movflags +faststart out_pptx.mp4
   ```
2. **เตรียมสไลด์ด้วย python-pptx** คัดลอกกล่องข้อความจากสไลด์ต้นแบบในเล่มด้วย `copy.deepcopy(shape._element)` แล้วแก้ที่ `run.text` รูปแบบจะตรงทั้งเล่ม ห้ามใช้ `text_frame.text = ...`
   ```python
   mv = s.shapes.add_movie(VIDEO, left, top, w, h, poster_frame_image=POSTER, mime_type='video/mp4')
   lst = prs.slides._sldIdLst; el = list(lst)[-1]; lst.remove(el); lst.insert(1, el)   # ย้ายสไลด์ใหม่ไปเป็นสไลด์ที่ 2
   ```
3. **เลื่อนเลขหน้า** ถ้าเล่มมีเลขหน้าเป็นข้อความ เช่น `05 / 23` ให้จับด้วย regex `(\d+) / <จำนวนเดิม>$` ในแต่ละ run แล้ว `assert` ว่าเลขเดิมเท่ากับตำแหน่งเดิม ก่อนเขียนเลขใหม่ assert นี้จับสไลด์ที่ลำดับเพี้ยนได้
4. **ตั้งให้คลิปเล่นเอง และต่อเด็ค** บันทึกไฟล์ก่อน แล้วรัน
   ```bash
   powershell -NoProfile -ExecutionPolicy Bypass -File <skill_dir>/scripts/ppt_finish.ps1 -Mode finish -Deck "<ไฟล์ปลายทาง>" [-Append "<เด็คที่ต่อ>"] [-Slide 2]
   ```
   ต้องเห็น `video effect type=83 trigger=3` · path ต้องเป็น absolute ใช้ `\` ถ้ารันจาก Python ให้ผ่าน `os.path.abspath()`
5. **เลื่อนเลขหน้าส่วนที่ต่อ** เปิดไฟล์ด้วย python-pptx อีกรอบ แก้เลขหน้าตามข้อ 3 แล้ว save การบันทึกซ้ำไม่ทำให้ค่าเล่นเองหาย ตรวจแล้วใน XML ของสไลด์ยังมี `nodeType="afterEffect"` กับ `presetClass="mediacall"`
6. **ตรวจ**
   - `python -I <pptx skill>/scripts/office/validate.py out.pptx --original src.pptx`
   - export ภาพด้วย `ppt_finish.ps1 -Mode export -Deck <ไฟล์> -OutDir <โฟลเดอร์> -Slides 1,2,25` (เปิดแบบอ่านอย่างเดียว ใช้กับเด็คต้นฉบับได้) แล้วเทียบกับต้นฉบับด้วยตา เพราะ InsertFromFile ย้ายสไลด์เข้าเล่มปลายทาง
   - ‼ **ยังไม่เคยเปิดเล่นจริงในโหมดนำเสนอ** ตรวจได้แค่ค่าใน COM กับ XML บอกผู้ใช้ทุกครั้งว่าต้องเปิดฟังเสียงเองก่อนใช้งาน

## กับดัก

- `PlayOnEntry = -1` อย่างเดียวยังเล่นเมื่อคลิก (trigger=1) ต้องตั้ง `Timing.TriggerType = 3` บน effect ชนิด 83 ด้วย
- python-pptx ล้มตอน import ถ้ารันจากโฟลเดอร์ที่มีไฟล์ชื่อชนไลบรารีมาตรฐาน เช่น `xml.py` ในโฟลเดอร์ memory ให้รันด้วย `python -I`
- คอนโซล cp1252 พิมพ์ชื่อไฟล์ไทยไม่ได้ ใส่ `sys.stdout.reconfigure(encoding='utf-8')` ต้นสคริปต์
- หัวเรื่องไทยที่มีสระล่างชนบรรทัดถัดไปในเล่มที่ตั้งระยะบรรทัดแคบ ("รู้จัก" ที่ 0.8) เปลี่ยนคำดีกว่าขยับกล่อง
- เด็คที่รวมเนื้อหาเฉพาะลูกค้าให้ตั้งชื่อไฟล์แยก อย่าทับฉบับทั่วไป และอย่าเขียนลงโฟลเดอร์ที่แชร์กันโดยไม่ถาม
