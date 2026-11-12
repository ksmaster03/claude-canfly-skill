---
name: talkinghead-edit-skills
description: สูตรตัดต่อคลิปคนพูด (talking head) 6 แบบจากรีล Artem Novitckii ที่ทำใน Claude Code มือถือด้วย slash command — /trial-reels (3 เวอร์ชันลง trial reels), /behind-the-person (กราฟิกหลังคน ตัดพื้นหลัง), /split-screen (ภาพบน คนล่าง ซับกลาง), /storytelling (3 ภาพ + หัวข้อ + ซับเล็ก), /explainer (คนตัดขอบล่าง ภาพอธิบายบน), /ranking-list (tier list S–F). Trigger เมื่อพิมพ์ /talkinghead-edit-skills หรือขอ "ตัดต่อคลิปคนพูดแบบ Artem / ทำ trial reels 3 แบบ / ใส่กราฟิกหลังคน / split screen คลิปพูด / tier list ทับคลิป".
---

# /talkinghead-edit-skills: 6 สูตรตัดต่อคลิปคนพูด

ที่มา: รีล Artem Novitckii (IG/FB, 22 วิ, 5.4K reactions, 835 แชร์, ศึกษา 8 พ.ย. 2569) ไฟล์ `$WORK\_study\fb-1UVxxhhRiy\` (src.mp4, sheet.jpg, f/ เฟรมทุก 0.5 วิ)
คลิปไม่มีเสียงพูด (เพลงแร็ปประกอบ) โชว์แอป Claude บนมือถือ แท็บ **Code**: แนบคลิปตัวเอง พิมพ์ `/ชื่อสกิล` แล้ว Claude เรนเดอร์ผลออกมาเป็นวิดีโอ
ตัวสกิลจริงของเขาแจกผ่าน DM ("Comment SKILLS") **เราไม่มีโค้ดของเขา** สูตรด้านล่างถอดจากภาพผลลัพธ์ แล้วจับคู่กับเครื่องมือในเครื่องเรา

## 6 สูตร (คำอธิบายจากเมนูสกิลในคลิป + สิ่งที่เห็นในผลลัพธ์)

| สกิล | คำอธิบายในเมนู | หน้าตาผลลัพธ์ |
|---|---|---|
| `/trial-reels` | 3 visually distinct versions to post as trial reels | คลิปเดิม 3 แบบ: (1) หัวข้อตัวเหลืองใหญ่บน "CAROUSELS ARE AN INSTAGRAM CHEAT CODE" + ซับกลางล่าง (2) การ์ดทวีตขาวบนหัว + ซับคำเน้นเหลือง (3) กรอบเล็กลงพื้นดำ ตัวเลขยักษ์ "8×" ใต้หัวข้อ — ไว้ลง IG Trial Reels (ฟีเจอร์ทดลองกับคนที่ไม่ได้ติดตาม) แล้วดูว่าแบบไหนชนะ |
| `/behind-the-person` | Graphs and visuals behind you, clean cutout | ตัดคนออกจากพื้นหลัง วางกริดโพสต์ IG / ตัวเลขผู้ติดตามวิ่ง "9,204 → 9,958" + การ์ดโปรไฟล์ "+9,958 new followers [Follow]" ไว้ข้างหลังตัวคน (คนบังกราฟิกบางส่วน) |
| `/split-screen` | Visuals on top, you below, captions in the middle | ครึ่งบนพื้นครีม ป้าย "Step 1" + หัวข้อ serif มีคำเอียงสีส้ม "Find a *viral* carousel" + ภาพหน้าจอเว็บ · ครึ่งล่างคลิปคน · ซับแถบดำตรงรอยต่อ "THEN I PICK ONE" (คำปัจจุบันเทา) |
| `/storytelling` | Three images, a title and a small subtitle | บนหัวเรียงการ์ด 3 ใบ (นาฬิกา TIME SPENT 2:09→4:12 วิ่ง, ภาพปกคลิป, กล่องคอมเมนต์ "CAROUSEL" ซ้ำ ๆ) + หัวข้อขาวหนา "I made this carousel in a few minutes" + ซับเล็กกรอบขาว "and it's doing extremely well" |
| `/explainer` | You cut out at the bottom, visuals explain on top | พื้นครีม หัวข้อ "Steal what *works*" + แผนภาพ ANOTHER NICHE → ลูกศรโค้ง → YOUR NICHE (กล่อง "?" แล้วเติมเป็นภาพจริง) · คนในกรอบมุมมนครึ่งล่าง ซับขาวคำเอียง "and *recreate* it" |
| `/ranking-list` | (tier list) | หัวข้อเหลืองเอียง "BEST CONTENT FORMATS" + ตาราง S A B C D E F สีรุ้งมุมซ้ายล่าง ใส่การ์ด (CAROUSELS, REELS) ลงช่องทีละใบตามที่พูด |

จุดร่วมทุกแบบ: ซับทีละ 1–3 คำ ตัวขาวหนามีเงา คำเน้นเปลี่ยนสี/เอียง · หัวข้อ serif + คำเอียงสีส้ม (โทนเดียวกับแอป Claude) · กราฟิกเคลื่อนไหวตามจังหวะคำพูด (ตัวเลขวิ่ง, การ์ดเด้งเข้า)

## ทำในเครื่องเรา (‼ ยังไม่เคยรันจริง ทั้งหัวข้อนี้)

ต้องมีคลิปคนพูดจริง (เราไม่ค่อยมี งานเพลงของเราเป็นเสียง + ภาพนิ่ง) ถ้าผู้ใช้ส่งคลิปมา:
1. **ถอดคำพูดรายคำ** faster-whisper `word_timestamps=True` ได้เวลาให้ซับและจังหวะกราฟิก (ภาษาไทยใช้ align ของ `/explainreel`)
2. **ตัดพื้นหลังคน** (behind-the-person, explainer) ยังไม่มีเครื่องมือในเครื่อง: `cv2` และ `onnxruntime` มีแล้ว แต่ rembg/mediapipe ยังไม่ได้ลง ต้องลงใน venv Python 3.12 (`~\.venvs\scrapling` มี pip) ถามผู้ใช้ก่อนลง ตัดทีละเฟรมได้ mask PNG แล้ว ffmpeg `alphamerge`
3. **กราฟิก** เขียนเป็น HTML แล้วเรนเดอร์ด้วย Chromium ทีละเฟรมแบบเอนจิน `scenes.html` ของ `/msinterview` (ตัวอักษรไทยไม่ลอย ห้ามวาดไทยด้วย ffmpeg drawtext/PIL)
4. **ซ้อนชั้น** ffmpeg: พื้นกราฟิก → คนที่ตัดขอบ → ซับ (behind-the-person) หรือ `vstack` สำหรับ split-screen
5. **trial-reels** = เรนเดอร์ 3 ธีมจากคลิปเดียว (หัวข้อใหญ่ / การ์ดทวีต / ตัวเลขยักษ์) แล้วอัปเป็น trial reel บน IG หรือ A/B ด้วยการลง FB/TT ต่างเวลา ดูยอดที่ 24 ชม.
6. ตรวจด้วย `/reel-edit-layers` ก่อนโพสต์

## ใช้กับงานคลิปแปลเพลงของเรา (ไอเดีย ยังไม่ได้ลอง)

- `/storytelling` ใกล้กับฉาก mv ของเรามากที่สุด: เพิ่มการ์ดเล็ก 3 ใบบนหัว (ปีอัลบั้ม, ภาพ MV, คอมเมนต์แฟน) ได้โดยไม่ต้องมีคนพูด
- `/ranking-list` ทำคลิป "จัดอันดับเพลง LP" ด้วย tier list ได้
- `/trial-reels` ใช้หลักเดียวกับปก: ทำ 3 หัวข้อแล้ววัดผล
