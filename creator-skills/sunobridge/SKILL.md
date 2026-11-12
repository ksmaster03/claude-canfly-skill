---
name: sunobridge
description: >-
  แต่งเพลงแล้วสร้างเป็นไฟล์เพลงจริงด้วย Suno ผ่านบัญชีตัวเอง (Playwright bridge ที่ล็อกอินไว้แล้ว) —
  เขียนเนื้อ → style prompt → ซ้อมกรอกฟอร์ม → generate 2 เทค → เลือกเทค → ดึง word-level
  aligned lyrics มาทำ timeline สำหรับตัดต่อ/ทำ MV. Trigger เมื่อผู้ใช้พิมพ์ /sunobridge หรือขอ
  "แต่งเพลง / ทำเพลง / สร้างเพลง / เพลงประกอบ / jingle / ทำเพลงด้วย AI / Suno / อยากได้เพลง...",
  หรือขอทำ MV ที่ต้องมีไฟล์เพลงก่อน.
---

# /sunobridge — แต่งเพลงแล้วปั้นเป็นไฟล์เพลงจริง

`$PROJECTS/suno-bridge` ขับ suno.com ด้วย Playwright ผ่าน persistent profile `suno-data/`
บัญชี **kosin_finsure ล็อกอินค้างไว้แล้ว** (ตั้งแต่ 2026-08-13) — ไม่ต้องล็อกอินซ้ำ
ถ้า session หลุด สคริปต์จะเปิดเบราว์เซอร์แบบเห็นหน้าต่างและรอให้ล็อกอินสูงสุด 8 นาที

> ใช้ส่วนตัวเท่านั้น การ automate เว็บ Suno เป็นพื้นที่สีเทาของ ToS

> **เช็กโควตาดาวน์โหลดก่อนสั่งเพลงทุกครั้ง** `cd $PROJECTS/suno-bridge && node probe-dl.mjs <clipId เก่า>` (ไม่กินโควตา) ถ้าผลมี "Out of Downloads" ห้ามรัน `create.mjs` เพราะเสียเครดิตแต่โหลดไฟล์ไม่ได้ ให้บอกผู้ใช้วันรีเซ็ตที่หน้าเว็บแสดง แล้วเสนอเพลงจาก `$MEDIA\bgm` หรือ YouTube Audio Library แทน (11 ต.ค. 2569 โควตาเหลือ 0 รีเซ็ต 12 ต.ค.)
> เพลงบรรเลงใช้ `--instrumental` · เพลงคลอใต้เสียงพากย์ผสมที่เบากว่าเสียงพากย์ 10 ถึง 12 dB ดู `~/.claude/skills/vidcraft/references/reel-lessons.md` ข้อ 6
## ลำดับงาน

```bash
cd $PROJECTS/suno-bridge          # ต้อง cd ก่อนเสมอ ไม่งั้น MODULE_NOT_FOUND

# 1) ซ้อม — กรอกครบทุกช่องแต่ไม่กด Create ไม่เสีย credit
node create.mjs --lyrics "$PROJECTS/<งาน>/suno-lyrics.txt" \
  --styles "<style prompt ภาษาอังกฤษ>" --title "<ชื่อเพลง>" --dry

# 2) เปิด debug/filled.png ด้วย Read tool ยืนยันว่าเนื้อ/สไตล์/ชื่อ ลงถูกช่อง
#    ปุ่ม Create ต้องเปลี่ยนเป็นสีส้ม (ถ้ายังเทา = ฟอร์มไม่ครบ)

# 3) ของจริง — ได้ 2 เทค โหลด mp3 อัตโนมัติ
node create.mjs --lyrics "..." --styles "..." --title "..." --outdir "$PROJECTS/<งาน>/audio"

# 4) ดึง word-level alignment ของทั้ง 2 เทค (clipId มาจาก output ขั้น 3)
node meta.mjs <clipId-1> <clipId-2>     # -> out/aligned-<id>.json
```

**เลือกเทคด้วยข้อมูล ไม่ใช่เดา** — Suno กลืนท่อนหายได้ ให้รัน `timeline.py` ทั้งสองเทคแล้วเทียบว่า
section tag ครบทุกท่อนไหม (เคยเจอ take1 กลืน `[Verse 1]` เข้าไปในอินโทร เหลือ 10 จาก 11 ท่อน)

```bash
cp <SKILL_DIR>/references/timeline.py $PROJECTS/<งาน>/tools/
cd $PROJECTS/<งาน>
python "~/.claude/skills/vdomindset/references/downbeat.py" audio/<take>.mp3   # bpm + phase
python tools/timeline.py audio/aligned-<id>.json --bpm <bpm> --phase <phase>
```
ได้ `timeline.json` = `{bpm, bar, phase, sections:[{tag,start}], lines:[{text,start,end}]}`
นี่คือของที่ MV/ตัวตัดต่อต้องใช้ **อย่าประมาณเวลาท่อนเอง**

## เขียนเนื้อเพลงให้ Suno

- ไฟล์ `.txt` ล้วน ใช้แท็ก `[Intro] [Verse 1] [Pre-Chorus] [Chorus] [Rap] [Bridge] [Outro]`
- **อย่าเขียนคำอธิบายในวงเล็บเหลี่ยม** เช่น `[Bridge — clean guitar, half-time]` เพราะมันจะร้องออกมา
  ให้เก็บคำอธิบายไว้ในไฟล์ `lyrics.md` ของเราแทน แล้วส่ง `.txt` ที่สะอาดเข้า Suno
- วงเล็บโค้ง `(...)` ก็ถูกร้องเหมือนกัน ระวัง
- ท่อนฮุกให้มีคำซ้ำสั้น ๆ ที่ร้องตามได้ · เพลงที่โม้อย่างเดียวฟังแล้วไม่เชื่อ ควรมี bridge ที่ "ลดความมันลงแล้วพูดความจริง"
- ความยาว ~2,200 ตัวอักษร ออกมาได้เพลงราว 3:45

## Style prompt

ภาษาอังกฤษ คั่นด้วยจุลภาค ใส่ให้ครบ 5 อย่าง: **แนว · เพศ/ลักษณะเสียงร้อง · BPM · เครื่องดนตรีเด่น · อารมณ์**

```
thai pop punk rock, energetic male vocalist, 168 bpm, driving distorted electric guitar,
punchy live drums, gang vocal chorus, half-time rap verse, anthemic singalong, live band, no autotune
```
BPM ที่ขอไปเป็นแค่คำใบ้ — **ต้องวัดจากไฟล์จริงด้วย `downbeat.py` เสมอ** (ขอ 168 ได้จริง 169.4)

## กับดัก (เจอมาแล้วทุกข้อ)

- **ปุ่ม Simple/Advanced เป็น `role="tab"` ไม่ใช่ `button`** → `getByRole('button')` จะ timeout 30 วิ
  และ `el.click()` ผ่าน DOM ก็ไม่ทำให้ React สลับโหมด ต้องคลิกด้วยเมาส์จริงหรือ `getByRole('tab')`
- **ช่อง Styles มีตัวปลอม** — `textarea[placeholder="Describe the sound you want"]` คือ autosize clone
  ที่ `visibility:hidden` ตัวจริงอยู่ใน `[data-testid="create-form-styles-wrapper"]` และ placeholder
  หมุนเปลี่ยนไปเรื่อย ๆ จึงต้อง filter `visible=true` ไม่ใช่ match placeholder
- ช่องเนื้อเพลงเป็น contenteditable `[aria-label="Lyrics editor"]` ไม่ใช่ textarea
- **aligned lyrics ต้องมี Clerk JWT** — `await window.Clerk.session.getToken()` แล้วยิง
  `https://studio-api.prod.suno.com/api/gen/<id>/aligned_lyrics/` พร้อม `Authorization: Bearer`
  (ไม่มี token = 401) · payload อยู่ที่ `data[0]` เป็น list `{word,start_s,end_s}` และ
  **มี section tag `[Chorus]` ติดมาในคำด้วย** จึงใช้หาขอบท่อนได้ตรง ๆ
- `https://suno.com/api/...` ตอบ 404 ทั้งหมด ต้องยิง `studio-api.prod.suno.com`
- ไฟล์เสียงอยู่ที่ `https://cdn1.suno.ai/<clipId>.mp3`
- **เพลงจาก Suno ถูกบีบไดนามิกจนแบน** (ดังสุด−เบาสุดต่างกันราว 7 dB) → หาโครงเพลงด้วย RMS
  ไม่ได้เลย (`references/sections.py` มีไว้พิสูจน์ข้อนี้) ต้องใช้ aligned lyrics เท่านั้น
- Suno master มาให้แล้ว **อย่า loudnorm ซ้ำ** ตอน mux เข้าวิดีโอ
- อย่ารัน bridge ซ้อนสองโปรเซส profile ล็อกได้ตัวเดียว

## ต่อยอด

ได้ `timeline.json` แล้วส่งต่อให้ [[vdomindset]] ทำ MV แนวตั้ง 9:16 ได้เลย —
ตัดฉากที่ `sections[].start` (snap เข้าบาร์) และขึ้นคำร้องจาก `lines[]`
ถ้าท่อนไหนร้องถี่ (แร็ป) ให้ตัดที่ **ครึ่งบาร์** เพราะ snap เต็มบาร์จะเหวี่ยงได้ถึง 0.7 วิ
ซึ่งกินคำร้องบรรทัดก่อนหน้า

## งานที่ทำเสร็จแล้ว

- `$PROJECTS/claude-song` — "พิมพ์มาสิ" ร็อคไทย 3:44 169.4 BPM + MV 9:16 (ดู [[project_claude_song_mv]])
