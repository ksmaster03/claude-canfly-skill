---
name: stills-to-promo-clip
description: ทำคลิปโปรโมตจากภาพนิ่งสมจริง (chatgpt-bridge) ให้เป็น footage 2.5D ใน Blender บนเครื่องไม่มีการ์ดจอ แล้วซ้อนตัวหนังสือไทย motion และเพลง. Trigger เมื่อพิมพ์ /stills-to-promo-clip หรือขอ "ทำ footage จากภาพนิ่ง / ทำภาพให้มีมิติ 2.5D / ตัดคลิปโปรโมตด้วย Blender / ใส่ตัวหนังสือ motion ลงคลิป".
---

# stills-to-promo-clip

ภาพนิ่งสมจริง → footage ที่กล้องขยับแล้วเห็นมิติ → คลิปโปรโมตพร้อมตัวหนังสือไทยและเพลง
ทุกขั้นรันจริงแล้วเมื่อ 13 ต.ค. 2026 บน i7-1165G7 ไม่มีการ์ดจอแยก (Blender 5.2, Cycles CPU)

สคริปต์อยู่ใน `scripts/` ของ skill นี้ เป็นตัวที่ใช้กับงานจริง คัดลอกไปไว้ในโฟลเดอร์งานแล้วแก้ตารางช็อตด้านบนไฟล์
สคริปต์อ้างโฟลเดอร์จากตำแหน่งตัวเอง (`out/`, `hires/`, `depth/`, `frames_v2/`, `clips_v2/` อยู่ข้างสคริปต์)

## ต้องมี

- Blender 5.x (`blender.exe -b --python ...`)
- Python ที่มี `onnxruntime`, `opencv-python`, `av` (PyAV), `Pillow`, `scipy`, `numpy` — ไม่ต้องมี ffmpeg
- Node + Playwright (ใช้ตัวใน `$PROJECTS/chatgpt-bridge` ได้)
- โมเดล ONNX สองตัว (ดาวน์โหลดครั้งเดียว):
  - `https://huggingface.co/onnx-community/depth-anything-v2-small/resolve/main/onnx/model.onnx` → `depth_anything_v2_small.onnx`
  - `https://huggingface.co/Xenova/2x_APISR_RRDB_GAN_generator-onnx/resolve/main/onnx/model.onnx` → `apisr_2x.onnx`

## ขั้นตอน

1. **ภาพนิ่ง** `bash run_footage.sh [id-filter]` อ่าน `prompts.json` (`[{id, prompt, image?}]`) แล้วสั่ง chatgpt-bridge ทีละภาพ ทีละ process ลองซ้ำ 3 รอบ ข้ามภาพที่มีแล้ว ผลอยู่ `out/<id>.png` (1672x941)
   - พรอมต์ขึ้นต้นด้วย `Generate an image.` ต่อท้ายด้วยบล็อกสไตล์เดียวกันทุกฉาก
   - สินค้าจริง: แนบรูปทางการเป็น `image` แล้วเขียนว่า "must be this exact model" ไม่งั้นได้เครื่องหน้าตาอื่น
   - **เปิดดูทุกภาพ** แชตใหม่บางครั้งคืนภาพของแชตก่อนหน้า (สัญญาณ: เสร็จเร็วผิดปกติ ราว 18 วินาที)
2. **ขยาย + ความลึก** `python prep_stills.py <โฟลเดอร์โมเดล> [id-filter]` → `hires/<id>.png` (2560x1440) และ `depth/<id>.npy` ราว 1 นาทีต่อภาพ
   - โมเดลขยายตัวนี้ฝึกกับภาพวาด ทำผิวคนเรียบเกิน ให้ผสม 50/50 กับ Lanczos ธรรมดาก่อนใช้
3. **footage 2.5D** แก้ `FRAMES` และ `MOVES` ใน `make_footage_v2.py` แล้ว
   `blender.exe -b --python make_footage_v2.py -- test <id>` ดูเฟรมแรก/สุดท้ายก่อน จากนั้น `-- render`
   - หลักการ: ดัน mesh ตามแนวรังสีของกล้องตั้งต้น ภาพจึงเหมือนต้นฉบับเมื่อกล้องอยู่ที่เดิม และเกิด parallax เมื่อกล้องเลื่อน
   - ขอบภาพไม่โผล่ตราบที่ `|x| <= 0.8*forward` และ `|y| <= 0.45*forward` (สคริปต์ assert ให้)
   - วัสดุเป็น emission ล้วน 6 samples ไม่ต้อง denoise ได้ราว 2 วินาทีต่อเฟรมที่ 1080p
   - เขียนเป็นเฟรม JPG รันซ้ำแล้วทำต่อจากเฟรมที่ค้าง
4. **ลุคฟิล์ม + เข้ารหัส** `python post_footage.py [id-filter]` ใส่ขอบมืด เกรดสี เกรน แล้วเข้ารหัส H.264 ด้วย PyAV → `clips_v2/<id>.mp4`
5. **ตัวหนังสือ motion** เขียนหน้า HTML 1920x1080 พื้นโปร่ง มีฟังก์ชัน `window.render(t)` ที่ตั้ง style ของทุกชิ้นจากเวลา (ไม่ใช้ CSS animation) แล้วถ่ายทีละเฟรม:
   `OV_HTML=<ไฟล์>.html OV_OUT=<โฟลเดอร์> node capture_overlay_env.mjs [from] [to]` (แก้ค่า `HERE` ในไฟล์ให้ชี้โฟลเดอร์งาน และรันจากโฟลเดอร์ที่มี playwright)
6. **เพลง** `mix_music.py` ปรับความเร็วเพลงให้บีตลงจุดตัดภาพด้วย `resample_poly` แล้ววางจุดเข้าท่อนใหญ่ให้ตรงวินาทีที่ชื่อเรื่องขึ้น ถอด MP3 ด้วย PyAV
7. **ตัดรวม** แก้ `CUT` ใน `assemble_promo.py` แล้ว `blender.exe -b --python assemble_promo.py` (sequencer: คลิป + เฟรม overlay แบบ alpha over + เสียง → MP4 พร้อม AAC)

## กับดักที่เจอจริง

- **อย่ารัน Blender สองงานพร้อมกัน** บน CPU ตัวนี้ แต่ละงานเหลือความเร็วราวหนึ่งในสาม
- **Playwright ในโฟลเดอร์เก่าอาจชี้เบราว์เซอร์รุ่นที่ไม่ได้ลง** ให้ `npx playwright install chromium` ในโฟลเดอร์นั้น หรือส่ง `executablePath`
- **ข้อความไทย** ให้เบราว์เซอร์วาดเท่านั้น Blender กับ PIL (ไม่มี raqm) วางสระลอย
- **Blender 5.x**: ตั้งค่า node ของ compositor ผ่าน `node.inputs[...]` และผูก tree ด้วย `scene.compositing_node_group`; ออกวิดีโอต้องตั้ง `image_settings.media_type = "VIDEO"` ก่อน `file_format = "FFMPEG"`; fcurve อยู่ใน `action.layers[].strips[].channelbags[]`
- **ผลทดสอบความละเอียดต่ำหลอกตา** bloom และหมอกดูหนากว่าภาพจริง
- **ฝุ่นลอย** ต้องเป็นจุดกลมขอบนุ่มและจางมาก จุดสี่เหลี่ยมคมดูเป็นสิ่งสกปรกบนภาพ
- **เพลง**: ใช้เพลงที่มีสัญญาอนุญาต (เช่น CC BY จาก incompetech พร้อมเครดิต) ไม่ดึงเสียงเพลงลิขสิทธิ์จาก YouTube

## ตรวจผล

- ดึงเฟรมจาก MP4 ด้วย cv2 มาต่อเป็นแผ่นแล้วเปิดดู: ตัวหนังสือไม่ทับหน้า/สินค้า ภาษาไทยถูก
- เช็กสตรีมด้วย PyAV: จำนวนเฟรม ความยาว และมีเสียง
- ‼ Claude ฟังเสียงและดูการเคลื่อนไหวจริงไม่ได้ ต้องให้คนเปิดดูหนึ่งรอบก่อนเผยแพร่

## ข้อจำกัด

คนและวัตถุในภาพไม่ขยับ มีแค่กล้อง แสงกะพริบ และฝุ่น ถ้าต้องการคนเคลื่อนไหวจริงต้องใช้เครื่องมือแปลงภาพเป็นวิดีโอ
