---
name: song-release
description: ปล่อยเพลงบรรเลงของช่องเป็นคลิปเพลงเต็มแนวตั้ง (ภาพนิ่ง + คลื่นเสียงสีทอง) แล้วตั้งเวลาลง YouTube + Facebook + TikTok ผ่าน reel-bridge ใช้เมื่อแฟนถามชื่อ bgm ในคลิป. Trigger เมื่อพิมพ์ /song-release หรือขอ "อัปเพลงนี้ขึ้นทุก platform / ปล่อยเพลง bgm ของช่อง / ทำคลิปเพลงเต็มเพลง / แฟนถามเพลงประกอบ".
---

# /song-release: ปล่อยเพลงบรรเลงของช่องขึ้น YT + FB + TikTok

ใช้จริงครั้งแรก 9 พ.ย. 2569 กับเพลง **Leave Behind Light** (take2 ที่ใช้เป็น bgm ในคลิปแปลเพลง LP)
แฟน @phillhamonic789 ถามว่าเพลงประกอบชื่ออะไร ผู้ใช้จึงสั่งให้ปล่อยเพลงเต็ม
งานต้นแบบอยู่ที่ `$WORK\leave-behind-light\` ได้ YT https://youtu.be/fRRS94Jr5lA (ตั้งเวลา 10 พ.ย. 19:30) FB 10 พ.ย. 19:30 และ TT 11 พ.ย. 12:00

## กฎเรื่องเครดิต (ผู้ใช้เลือกเอง 9 พ.ย. 2569)

- **ไม่พูดถึง Suno** ทั้งบนจอ คำบรรยาย และคอมเมนต์
- **ไม่อ้างว่าใครแต่ง** ผู้ใช้เลือก "ไม่พูดเรื่องคนแต่ง" แทนที่จะบอกว่าพี่โกสินทร์แต่งทำนอง ถ้าจะเปลี่ยนต้องถามผู้ใช้ใหม่
- เครดิตที่ใช้: **"เล่นโดย ลินดา ผู้ช่วย AI"**
- บอกให้ชัดว่า**ไม่ใช่เพลงของ Linkin Park** เป็นเพลงบรรเลงของช่องเอง
- เพลงบน Suno ปล่อยเป็น private ไว้เหมือนเดิม
- ไม่ลง Spotify หรือ distributor ถ้าไม่ได้สั่ง

## ลำดับงาน

1. **หาไฟล์เพลงและชื่อเพลง**
   - ชื่อเพลงจาก Suno อ่านได้จาก SQLite ประวัติเบราว์เซอร์ `$PROJECTS/suno-bridge\suno-data\Default\History` (ตาราง urls ช่อง title ของ `suno.com/song/<id>`)
   - ก๊อปไฟล์ wav มาเป็น `<proj>/song.wav` โฟลเดอร์งานคือ `$WORK\<slug>\`
2. **ภาพพื้นหลัง**
   - ก๊อป `references/bg_example.html` เป็น `<proj>/bg.html` แล้วแก้ชื่อเพลง คำโปรย และเครดิต
   - ฟอนต์ Kanit/Trirong ใช้จาก `$MEDIA/fonts/google`
   - เว้นแถบ y 900 ถึง 1050 ไว้ให้คลื่นเสียง
   - แปลงเป็นภาพ: `cd $PROJECTS/reel-bridge && NODE_PATH=$PROJECTS/reel-bridge/node_modules node <skill_dir>/scripts/bg_to_png.cjs <proj>` ได้ `bg.png` กับ `cover.jpg`
3. **เรนเดอร์** `bash <skill_dir>/scripts/render_song.sh <proj> <Name>` ได้ `<Name>_9x16.mp4` และ `chk60.jpg`
   - รันเบื้องหลัง เพลง 70 วิใช้ราว 80 วิ เพลง 194 วิได้ไฟล์ 27.7 MB
   - เปิด `chk60.jpg` ดูว่าคลื่นสีทองชัด ไม่ใช่สีเขียว และข้อความไทยไม่ลอย
4. **ข้อความโพสต์** ใช้ `references/youtube_example.txt` และ `references/caption_example.txt` เป็นแบบ
   - เนื้อหา: ชื่อเพลง, เป็นเพลงประกอบคลิปไหน, เล่นโดยลินดา ผู้ช่วย AI, ไม่ใช่เพลง LP, ขอบคุณคนที่ถาม, แฮชแท็ก
   - ไม่ใช้อีโมจิ ไม่ใช้ขีดยาว
5. **เช็กตาราง** ด้วย `node sched-list.mjs` (YT + FB) และ `node tt-sched-list.mjs` ใน reel-bridge กับ `$PROJECTS/reel-auto/posted.json`
   - เพดานวันละ 3 คลิปต่อแพลตฟอร์ม ช่อง 09:00 / 12:00 / 19:30
   - วันที่เต็มแล้วให้เลื่อนวัน แต่ละแพลตฟอร์มลงคนละวันได้
6. **อัป** (เมื่อผู้ใช้สั่งในเทิร์นนั้นเท่านั้น) ใน `$PROJECTS/reel-bridge` รันพร้อมกันได้ เพราะแยกโปรไฟล์กัน:
   ```bash
   node yt-upload.mjs <proj> --video <proj>/<Name>_9x16.mp4 --schedule "YYYY-MM-DD HH:MM"
   node fb-upload.mjs <proj> --video <proj>/<Name>_9x16.mp4 --schedule "YYYY-MM-DD HH:MM"
   node tt-upload.mjs <proj> --video <proj>/<Name>_9x16.mp4 --schedule "YYYY-MM-DD HH:MM"   # นาทีต้องลงท้าย 0 หรือ 5
   ```
7. **บันทึกช่องเวลา** ต่อท้าย `$PROJECTS/reel-auto/posted.json` (สำรองไฟล์ก่อน) จะได้ไม่ให้ reel-auto ตั้งเวลาทับ
8. **หลังเพลงขึ้น** เก็บลิงก์ FB/TT จากหน้าเพจ แล้วตอบแฟนที่ถามพร้อมลิงก์ YouTube (ผ่านแผน plan-yt-*.json ของ yt-comments.mjs)

## กับดัก

- **เพลงยาวเกิน 180 วิ YouTube จะลงเป็นวิดีโอยาว ไม่ใช่ Shorts**
  - ช่องที่เปิดสร้างรายได้จะมีหน้า Monetization บังคับเลือก ไม่งั้นค้างไปไม่ถึงหน้า Visibility
  - `yt-upload.mjs` ตั้งเป็น Off ให้แล้ว (แก้เมื่อ 9 พ.ย. 2569) บอกผู้ใช้ว่าเปิดเองได้ใน Studio
  - วิดีโอยาวจะอยู่แท็บ Videos ไม่ใช่ Shorts ถ้าจะลบร่างให้ใช้ `YT_TAB=upload node yt-delete.mjs "<ชื่อ>" --draft-title`
- **คลื่นเสียงเป็นสีเขียวหรือจาง** ถ้าไม่ใส่ `aformat=channel_layouts=mono` (สเตอริโอช่องที่สองใช้สีดีฟอลต์) และ `draw=full` (ดีฟอลต์ `draw=scale` จาง) สคริปต์ใส่ให้แล้ว
- **อย่าใส่ zoompan แบบ `z=1+0.0004*on`** ค่าซูมโตทุกเฟรม เพลง 3 นาทีจะครอปชื่อเพลงหาย ภาพนิ่งเฉย ๆ ดีกว่า
- `fb-upload.mjs` อาจคืน ok:true แต่ log ว่า "ไม่เห็นข้อความยืนยัน" ให้เช็กที่ `business.facebook.com/latest/posts/scheduled_posts`
- TikTok เปิดป้าย "เนื้อหาที่สร้างโดย AI" ให้ทุกคลิปอยู่แล้ว ตรงกับเครดิตลินดา ผู้ช่วย AI
- Python บน Windows เปิดพาธ `/tmp/...` ของ Git Bash ไม่ได้ ใช้ `cygpath -w`

## รายงานผู้ใช้

ตาราง ช่อง · เวลาโพสต์ · ลิงก์ (FB/TT มีลิงก์หลังโพสต์ขึ้น) แล้วตามด้วยข้อความเครดิตที่ใช้ การตั้ง Monetization: Off และป้าย AI ของ TikTok
