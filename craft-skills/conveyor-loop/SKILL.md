---
name: conveyor-loop
description: สร้าง "วิดีโอสายพานสินค้า AI แบบวนลูป" (ฉากหลังไลฟ์/คอนเทนต์ปักตะกร้า) จากภาพนิ่งโรงงาน — ภาพตั้งต้น → Google Flow (Veo) เจนคลิป 8 วิ → ffmpeg วนลูป+คมชัด+ติดแบรนด์ บน PC (แทน CapCut). ต่อยอดเทคนิคจากเพจ "ออม สายเอไอ". Trigger เมื่อผู้ใช้พิมพ์ /conveyor-loop หรือขอ "ทำวิดีโอสายพาน / คลิปโรงงานวนลูป / ฉากหลังไลฟ์โกดัง / warehouse loop / conveyor video / คลิปสินค้าบนสายพาน".
---

# /conveyor-loop — โรงงานทำวิดีโอสายพานสินค้า AI วนลูป

โปรเจกต์: **`$WORK/ai-conveyor-loop`** (path/asset ปรับตามเครื่องคุณเอง)
เทคนิคต้นแบบ: EP.253 เพจ *รวมความรู้การตลาดด้วยเอไอ (ออม สายเอไอ)* — ทำให้ workflow มือถือ+CapCut
กลายเป็น automate บน PC. คุย/ยืนยันภาพตั้งต้น + สินค้าเป็นภาษาไทยก่อนเจนเสมอ

## Pipeline 4 ขั้น
```
[0] ภาพตั้งต้น   python scripts/gen_image.py --preset vitamin assets/scene.png   (chatgpt-bridge; หรือใช้ภาพเอง)
[1] เจนวิดีโอ 8s node scripts/flow-bridge.mjs --image ../assets/scene.png \
                        --prompt-file ../prompts/master_en.txt --out ../clips/raw.mp4   (Google Flow/Veo — login ครั้งแรก)
                   ↳ ทำมือก็ได้: ดู $WORK/ai-conveyor-loop\FLOW_STEPS.md
[2] โพสต์-โปรเซส python scripts/build.py clips/raw.mp4 --seconds 60 -o output/loop.mp4   (enhance→loop, ffmpeg)
[3] ติดแบรนด์    python scripts/brand.py output/loop.mp4 output/final.mp4 --logo assets/logo.png --cta "ทักแชทสั่งเลย"
```

## หัวใจของงาน (อย่าลืม)
- **Prompt สั่ง 3 อย่างเสมอ** (อยู่ใน `prompts/master_en.txt` + `negative.txt`): กล้องนิ่งสนิท ·
  สายพานวิ่ง **ออกจากกล้อง** ความเร็วคงที่ · **loop-ready (เฟรมแรก≈สุดท้าย)** → นี่คือเหตุผลที่ต่อวนลูปแล้วเนียน
- เปลี่ยนสินค้า = แก้ `{PRODUCT}` `{SCENE}` หรือใช้ `prompts/presets/*.json` (vitamin/coffee_sachet/water_bottle)
- **Flow เจนพลาด ("Oops") เป็นปกติ** — flow-bridge retry 3 รอบ; ทำมือก็แค่กดใหม่
- โพสต์-โปรเซสแทน CapCut ครบ: `enhance.py` (720→1080×1920+sharpen) · `make_loop.py`
  (stream_loop = "duplicate ใน CapCut"; `--crossfade` ทำได้แต่ **อาจโกสต์กับสายพานเส้นตรง** — default ต่อตรงดีสุด)

## สเต็ปทำงาน
1. ถามผู้ใช้: สินค้าอะไร / มีภาพตั้งต้นแล้วหรือให้เจน / ความยาวลูป (เริ่มต้น 60s) / ติดแบรนด์+CTA ไหม
2. เตรียมภาพตั้งต้น (`gen_image.py` หรือรับไฟล์จากผู้ใช้ → `assets/`)
3. เจนวิดีโอ: ใช้ `flow-bridge.mjs` (ถ้า login แล้ว) — **ถ้ายังไม่ได้เทสต์กับ Flow จริง ให้ผู้ใช้ login ครั้งแรก
   และเตือนว่า selector อาจต้องปรับ (`node scripts/inspect.mjs` → `debug/inspect.json`)**; ไม่งั้นให้ทำมือตาม `FLOW_STEPS.md` แล้ววางไฟล์ใน `clips/`
4. `build.py` → `brand.py` (ถ้าติดแบรนด์)
5. Self-check: `ffprobe` ดู duration/ขนาดตรง 9:16, แคปเฟรมรอยต่อลูป (Read PNG) ดูว่าเนียน

## ข้อควรระวัง
- `flow-data/` = โปรไฟล์ login Google — **อยู่ใน .gitignore อย่า commit**
- automate เว็บ Google เป็น ToS gray-area + กิน free credit (~10/คลิป) — ใช้ส่วนตัว/พอประมาณ
- ยังไม่ได้ live-test flow-bridge กับ Google (เขียนจาก UI ที่เห็นในคลิป) — คาดว่าต้องจูน selector รอบแรก

## ไฟล์อ้างอิง
- `$WORK/ai-conveyor-loop\README.md` — คู่มือเต็ม + quick start
- `FLOW_STEPS.md` — ทำ Flow ด้วยมือ (fallback)
- related: skills reel-factory / vdostory / vidcraft
