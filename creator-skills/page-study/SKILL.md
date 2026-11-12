---
name: page-study
description: ศึกษาคลิปรีลหรือเพจ Facebook ของคนอื่นแล้วสรุปเป็นความรู้ ไล่เก็บโพสต์ย้อนหลัง N วันด้วยโปรไฟล์ reel-bridge (อ่านอย่างเดียว) จัดอันดับ reaction/แชร์ หาว่ารูปแบบไหนได้ผล และถอดรีลด้วย yt-dlp + faster-whisper + contact sheet. Trigger เมื่อพิมพ์ /page-study หรือขอ "เปิดเพจนี้ดูย้อนหลัง 90 วัน / ศึกษาเพจ / ศึกษาคลิปนี้ / เก็บสกิลจากคลิป / วิเคราะห์เพจคู่แข่ง".
---

# /page-study: ศึกษาเพจและรีลของคนอื่น

ใช้จริง: รีล David Iya (7 พ.ย. 2569) → `/repo-swap-reel`, เพจ KEN CAFE 90 วัน (8 พ.ย.) → `$WORK\_study\fbpage-19uY8rF92t\STUDY.md`, รีล DevKub → `/vibe-ui-sources`
งานนี้อ่านอย่างเดียว ไม่กดไลก์ ไม่คอมเมนต์ ไม่ติดตามแทนผู้ใช้

## A. ศึกษารีลหนึ่งคลิป

```bash
export PATH="$FFMPEG_BIN:$PATH"
mkdir -p $WORK/_study/fb-<id> && cd $WORK/_study/fb-<id>
python -m yt_dlp --print "%(title)s | %(uploader)s | %(duration)s" --no-simulate -o "src.%(ext)s" "<ลิงก์ share/r/...>"
D=$(ffprobe -v error -show_entries format=duration -of csv=p=0 src.mp4)
ffmpeg -loglevel error -y -i src.mp4 -vf "fps=24/$D,scale=270:-1,tile=6x4" -frames:v 1 sheet.jpg   # 24 เฟรมเฉลี่ยทั้งคลิป
PYTHONIOENCODING=utf-8 python -c "
from faster_whisper import WhisperModel
m=WhisperModel('small',device='cpu',compute_type='int8'); s,i=m.transcribe('src.mp4'); print(i.language)
for x in s: print(f'{x.start:5.1f} {x.text}')"
```
- `--print` ได้คำบรรยายโพสต์ + ยอดวิว/รีแอคชันในชื่อ (คำบรรยายไทยออกมาเป็นตัวเพี้ยนในเทอร์มินัล อ่านจากเสียงและภาพแทน หรือใช้ `--write-info-json`)
- เปิด `sheet.jpg` ดูทุกครั้ง ชื่อเฉพาะให้ยึดตามตัวอักษรบนจอ whisper ถอดชื่อผิดบ่อย (Chatwoot→"Chatwood", Mobbin→"Mopbin", shadcn→"Chat.cn", Coolors→"coolers")
- ชื่อ repo/เว็บที่คลิปพูดถึง ตรวจของจริง (`gh api repos/...`, `gh api "search/repositories?q=<name>+in:name&sort=stars"`)

## B. ศึกษาเพจย้อนหลัง N วัน

1. สคริปต์อ่านเพจอยู่ใน reel-bridge (ใช้โปรไฟล์ FB ที่ล็อกอินไว้ ต้องรันจากโฟลเดอร์นั้นเพราะ import `common.mjs`):
   ```bash
   cd $PROJECTS/reel-bridge   # สำเนาสคริปต์เก็บไว้ที่ <skill_dir>/scripts/fb-page-read.mjs
   REEL_PROFILE=fb node fb-page-read.mjs "<ลิงก์เพจหรือ share>" <outdir> --scrolls 3     # ลองก่อน ดู top.txt ว่าเป็นเพจอะไร
   REEL_PROFILE=fb node fb-page-read.mjs "https://www.facebook.com/<page>/" <outdir> --scrolls 160
   ```
   160 ครั้งใช้ราว 8 นาที ได้ย้อนไปเกือบปีสำหรับเพจที่โพสต์วันละโพสต์ (90 วันใช้ราว 80 ครั้งก็พอ)
2. แยกโพสต์ จัดอันดับ:
   `PYTHONIOENCODING=utf-8 python <skill_dir>/scripts/parse_posts.py <outdir> "<ชื่อเพจตามที่ขึ้นบนโพสต์>" <YYYY-MM-DD วันเริ่ม>`
   ได้ `posts_since.txt` (ข้อความเต็ม) และตาราง `[reaction, (คอมเมนต์), แชร์]` เรียงจากมากไปน้อย
3. อ่านข้อความเต็มของ 8 ถึง 10 โพสต์บนสุด แล้วเขียน `<outdir>/STUDY.md`:
   - เพจคืออะไร (ผู้ติดตาม รีวิว ธุรกิจ ขายอะไร)
   - รูปแบบ (เวลาโพสต์ ความถี่ ชนิดสื่อ โครงข้อความ ซีรีส์ CTA)
   - ตาราง top posts + ข้อสังเกตว่าอะไรได้แชร์/ไม่ได้ผล (โพสต์ยอดสูงผิดปกติให้ระบุว่าน่าจะยิงโฆษณา)
   - ความรู้ที่ได้ จัดเป็นหมวด
   - ใช้กับเพจเราได้อย่างไร
4. บันทึก memory แบบ reference ชี้ไปที่ STUDY.md แล้ว `panya-sync push memory ... --go`

## C. ศึกษาทุกรีลในแท็บ Reels ของเพจ

ใช้จริง: Altair AI 25 คลิป (9 พ.ย. 2569) → `$WORK\_study\fbreels-100092880740003\STUDY.md` → `/darkui-repo-reel`

1. เก็บลิงก์รีลทั้งหมด พร้อมยอดวิวบนการ์ด (หยุดเองเมื่อเลื่อน 6 ครั้งแล้วไม่มีรีลใหม่):
   ```bash
   cd $PROJECTS/reel-bridge   # สำเนาอยู่ที่ <skill_dir>/scripts/fb-reels-list.mjs
   REEL_PROFILE=fb node fb-reels-list.mjs "https://www.facebook.com/<page>/reels/" <outdir> --scrolls 120
   ```
   ได้ `reels.json` ตัดแถว `https://www.facebook.com/reel/` ที่ไม่มีเลขทิ้ง
2. โหลดทุกคลิปด้วยวิธี A วนลูปลงใน `<outdir>/r/<reel_id>/` ใส่ `--write-info-json` เสมอ ไฟล์นี้ให้ view_count, upload_date และคำบรรยายเต็ม (รีลแนวรายการ repo ความรู้ทั้งหมดอยู่ในคำบรรยาย ไม่ได้อยู่ในเสียง)
   - รันเป็นงานพื้นหลัง 25 คลิปรวม whisper ใช้ราว 10 นาที
3. ทำตารางจาก info.json เรียงตามวันที่ แล้วดูว่ารูปแบบเปลี่ยนตอนไหน ยอดวิวกระโดดตอนไหน ต่อ contact sheet ของคลิปท็อปด้วย `vstack` แล้วเปิดดูครั้งเดียว
4. ตรวจ repo หรือตัวเลขในคลิปท็อปด้วย `gh api` แล้วเขียน STUDY.md ตามหัวข้อในวิธี B

## กับดัก

- รายการ URL ที่เขียนจาก python บน Windows ลงท้ายด้วย `\r` ต้องตัดก่อนใช้เป็นชื่อโฟลเดอร์ (`u=${u%$'\r'}`) ไม่อย่างนั้นทุกคลิปจะเขียนทับกันในโฟลเดอร์เดียว
- yt-dlp `--cookies-from-browser chrome` ใช้ไม่ได้ (DPAPI) รีลสาธารณะโหลดได้โดยไม่ต้องใช้คุกกี้
- รีลที่ไม่มีเสียงพูด whisper จะเดาข้อความมั่ว (เช่น ซับรัสเซีย "СПОКОЙНАЯ МУЗЫКА") ให้ใช้คำบรรยายกับภาพแทน

- ฟีดเพจดึงคอมเมนต์มาด้วย (`role=article` ของคอมเมนต์) parse_posts.py กรองด้วยการขึ้นต้นด้วยชื่อเพจ
- โพสต์เดียวกันถูกเก็บสองรอบ (ย่อ "... ดูเพิ่มเติม" กับเต็ม "ดูน้อยลง") ตัวแยกเลือกฉบับเต็ม
- ตัวเลขใต้โพสต์ไม่มีป้าย: 2 ตัว = reaction, แชร์ · 3 ตัว = reaction, คอมเมนต์, แชร์ (ตรวจกับหน้าจริงถ้าตัวเลขสำคัญ)
- ความรู้ของเพจแนวอินโฟกราฟิกอยู่ในภาพ carousel ข้อความโพสต์เป็นแค่สรุป ถ้าต้องการเนื้อในต้องเปิดโพสต์แล้วอ่านภาพ (ยังไม่ได้ทำ บอกผู้ใช้ทุกครั้ง)
- เลข CVE ตัวเลขสถิติ และเคลมในโพสต์ของคนอื่น จดว่า "ตามที่เพจเขียน" จนกว่าจะตรวจ
- ลิงก์ share ของ FB redirect ไปเพจจริงพร้อม `?rdid=` ใช้ URL เพจตรง ๆ ในรอบเลื่อนยาว
