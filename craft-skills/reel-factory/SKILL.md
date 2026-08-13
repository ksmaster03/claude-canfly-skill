---
name: reel-factory
description: สร้างคลิปรีลแนวตั้ง 9:16 ภาษาไทยแบบ "แชร์ข้อมูล/เล่าข่าว" จากหัวข้อเดียว — research → บท → VO (edge-tts + Tinglish) → ภาพ gen (ChatGPT connector) → ประกอบ Ken Burns + แบนเนอร์ + ซับ + BGM (ดัก) + SFX ตอนขึ้นหัวข้อ + ปิดด้วย CTA. Trigger เมื่อผู้ใช้พิมพ์ /reel-factory หรือขอ "ทำคลิปรีล / ทำรีล / คลิปแชร์ข้อมูล / คลิปเล่าข่าว / info reel / short" ที่ต้องมี VO + ภาพประกอบ + เพลง.
---

# /reel-factory — โรงงานทำคลิปรีล (9:16, ไทย, VO+ภาพ+BGM+SFX)

Pipeline ที่พิสูจน์แล้ว (โปรเจกต์ ai-livestock-reel, fable5-news). ทดสอบบน Windows 11 (path/asset เป็นของเครื่องนี้). คุย/ยืนยันบทเป็นภาษาไทยก่อนเรนเดอร์เสมอ; autonomous ได้หลังเคาะบท

## ภาพรวม 6 ขั้น
1. **Research** หัวข้อด้วย WebSearch (TH+EN) → เก็บข้อเท็จจริงจริง มีแหล่งอ้างอิง (อย่าแต่งข่าว — เคยพลาดคิดว่า Fable 5 ban ปลอม แต่จริง → **เช็กก่อนเสมอ**)
2. **เขียนบท** เป็น `<PROJ>/script.json` (schema ด้านล่าง) — hook → หัวข้อ 1..N → CTA ปิดท้าย (ชวนกดไลก์/ติดตาม)
3. **VO**: `python <skill>/templates/make_vo.py <PROJ>` → edge-tts Niwat + [[tinglish]] respell (คำอังกฤษออกสำเนียงไทย) → `vo/*.wav` + `vo_durs.json`
4. **ภาพ**: `python <skill>/templates/build_prompts.py <PROJ>` แล้ว `node $CHATGPT_BRIDGE/chatgpt-batch.mjs <PROJ>/prompts.json <PROJ>/img` (เปิด browser session Plus — เปิดทิ้งไว้ ~8 นาที, ครั้งแรกอาจต้อง login/ผ่าน turnstile)
5. **ประกอบ**: `python <skill>/templates/assemble_reel.py <PROJ>` → `<PROJ>/<name>_9x16.mp4`
6. **Self-eval**: probe + แคปเฟรม (Read PNG) เช็กแบนเนอร์/ซับ/ภาพ + วัดเสียงช่วงเงียบ VO ว่าได้ยิน BGM

## script.json schema
```json
[
  {"id":"s1","sfx":"title_boom","th":"<บทพูด VO>","cap":"<ซับบนจอ สั้น>","img":"<prompt ภาพไทย>"},
  {"id":"s2","sfx":"open_whoosh","th":"หนึ่ง ...","cap":"1. ...","img":"..."},
  {"id":"sN","sfx":"ding","th":"ถ้าคลิปนี้มีประโยชน์ กดไลก์ กดติดตาม...","cap":"กดไลก์ + ติดตาม 👍","img":"..."}
]
```
- `th` = บทพูด (จะถูก respell เป็น Tinglish อัตโนมัติก่อนเข้า TTS). `cap` = ซับบนจอ (คงคำอังกฤษไว้อ่านสวย ไม่ respell). `img` = prompt ภาพ
- `sfx` (ออปชัน): `title_boom` (เปิด) / `open_whoosh` (ขึ้นหัวข้อใหม่) / `ding` (CTA) / `trans_whoosh`
- config เสริม: `<PROJ>/config.json` = `{"name":"My_Reel","banner":"หัวข้อ • แท็ก","accent":[13,148,136],"bgm":"$MEDIA/edit/assets/bgm_bed.m4a"}`

## Asset บนเครื่องนี้
- **edge-tts** `~/.local/bin/edge-tts.exe` (เสียง th-TH-NiwatNeural ชาย / PremwadeeNeural หญิง — ฟรี ธรรมชาติ; ผู้ใช้ชอบ Niwat+Tinglish)
- **ภาพ** ผ่าน `$CHATGPT_BRIDGE` (GPT-4o image gen, Plus account) — prompt ขอ "แนวตั้ง 9:16, ไม่มีข้อความ/ตัวอักษรในภาพ" (เรา overlay ซับเอง; ภาพ ~941×1672 อัปเป็น 1080×1920)
- **BGM** `$MEDIA/edit/assets/bgm_bed.m4a` (+ bgm_imf/bgm_lcut) — **เบามาก (~-38dB)!** template บูสต์ +12dB + ducking ให้แล้ว
- **SFX kit** `$MEDIA/sfx/kit/`: `title_boom.mp3 open_whoosh.mp3 trans_whoosh.mp3 ding.mp3 hit.mp3`

## Gotchas (จ่ายด้วยเลือดมาแล้ว)
1. **ซับ ASS เท่านั้น** — burn SRT ด้วย force_style ตำแหน่งเพี้ยน (libass PlayResY=288). ใช้ไฟล์ .ass ที่ฝัง `PlayResX/Y 1080/1920` + `Alignment=2` + `MarginV~190` (template ทำให้แล้ว)
2. **BGM bed เบามาก** → ต้อง `volume=4.0` (+12dB) + `sidechaincompress` (duck ใต้ VO) ไม่งั้นเงียบสนิท. เช็กด้วยการวัดช่วงเงียบ VO ควรได้ ~-20dB
3. **ภาพต้องสั่ง "ไม่มีตัวอักษร"** (GPT-4o เขียนไทยเพี้ยน) + "แนวตั้ง 9:16"
4. **SFX วางที่ `seg.start`** (จังหวะภาพตัด+VO ขึ้น) ด้วย `adelay=ms|ms`; amix `normalize=0` + `alimiter` ก่อน loudnorm กันคลิป
5. **PYTHONIOENCODING=utf-8** เสมอ; ไฟล์ .ps1/.py ที่มีไทยให้เป็น ASCII-only หรือระวัง cp1252
6. **Tinglish**: เติมคำใหม่ที่เจอลง `~/.claude/skills/tinglish/tinglish_dict.json` (เช่น แบรนด์/ศัพท์เฉพาะคลิป)
7. **อย่าแต่งข่าว** — research ยืนยันข้อเท็จจริงก่อนทำคลิปแนวข่าวเสมอ

## เสียงพากย์: edge-tts (ดีฟอลต์) vs F5 โคลนเสียงผู้ใช้
- ดีฟอลต์ = **edge-tts Niwat + Tinglish** (เนียน เร็ว) — ผู้ใช้เลือกอันนี้
- ถ้าจะใช้ **เสียงโคลนผู้ใช้ (F5)**: — ต้อง ref สะอาด 10-12 วิ (ไม่ clip) + ref_text ถอดด้วย Scribe ให้ตรงเป๊ะ + NFE 32-40; รันด้วย Python เซ็นชื่อ (Device Guard บล็อก venv ของ uv) — ช้ามากบน CPU

## โพสต์
- **FB Reel draft**: `node $FB_MCP/reel_draft.mjs <video> <captionFile>` (video_state=DRAFT, รีวิวใน Meta Business Suite มือถือ) — ต้อง FB token มี pages_manage (ปัจจุบันหมดอายุ ต้อง re-auth)
- **YouTube**: อัป Short เอง/unlisted (ยังไม่มี uploader อัตโนมัติ)
- ดูภาพรวมงานวิดีโออื่นๆ ที่สกิล [[vdocut]]

## ปรับจูนที่ผู้ใช้ขอบ่อย
BGM ดัง/เบา (แก้ `volume=` ใน assemble), เปลี่ยนเพลง (config.bgm), เพิ่ม/ลดหัวข้อ (script.json), เปลี่ยนเสียง (Niwat↔Premwadee), สี/ข้อความแบนเนอร์ (config.accent/banner)
