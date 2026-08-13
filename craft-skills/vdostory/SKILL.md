---
name: vdostory
description: >-
  สร้างคลิป explainer/storyboard แบบการ์ตูนโทนสว่าง จากหัวข้อเดียว — เล่าปัญหา (pain point) →
  ทางแก้ พร้อมภาพการ์ตูนต่อเนื่อง + เสียงบรรยายไทย. ไพป์ไลน์: บท/สตอรีบอร์ด → ภาพการ์ตูนผ่าน
  chatgpt-bridge (GPT-4o) → VO ด้วย Gemini TTS (หรือ edge-tts) → text overlay ด้วย Remotion →
  ประกอบคลิปด้วย ffmpeg (Ken Burns + b-roll + L-cut + ซับไทย + SFX + BGM ดักใต้เสียง).
  แนะนำใช้ toolkit **Neramit** (config-driven ไฟล์ JSON เดียว). Trigger เมื่อผู้ใช้พิมพ์ /vdostory
  หรือขอ "ทำคลิป storyboard / explainer การ์ตูน / คลิปเล่าปัญหา-ทางแก้ + เสียงบรรยาย / อธิบายภาพรวมเป็นคลิปการ์ตูน".
---

# /vdostory — Storyboard → คลิปการ์ตูน + Voiceover

เปลี่ยน "หัวข้อ + แก่นเรื่อง" ให้เป็นคลิป explainer การ์ตูน: ภาพต่อเนื่อง + เสียงบรรยายไทย + text overlay + b-roll + BGM
ใช้คู่กับ [[vidcraft]] (ffmpeg cookbook), [[reel-factory]] (รีล 9:16), [[vdocut]] (ตัดฟุตเทจ), [[tinglish]] (ออกเสียงอังกฤษแบบไทย)

## ⭐ แนะนำ: ใช้ Neramit (config-driven — เร็วสุด)
Toolkit **Neramit (เนรมิต)** = `$NERAMIT` — รวมทุกขั้นของ /vdostory ไว้แล้ว
เขียน **config.json ไฟล์เดียว** (ฉาก + บทพากย์ + b-roll + overlay + BGM) แล้ว:
```
cd /d/Project/Neramit
export GEMINI_API_KEY=...
python neramit.py examples/devsecops/config.json   # → out/*.mp4
```
มันจัดการ: เจนภาพ (chatgpt-bridge) → VO (Gemini TTS) → overlay (Remotion) → Ken Burns/b-roll/L-cut → SFX + BGM ดัก → mp4; **resumable** (rerun ข้ามของที่ทำแล้ว)
ดู schema เต็มใน `README.md` ของ repo. ทำเองแบบ manual ก็ได้ตามขั้นด้านล่าง

## เมื่อไรใช้
อธิบายภาพรวมสินค้า/ระบบ/ไอเดีย เป็นคลิปการ์ตูนเล่าเรื่อง (pain point → solution), pitch, โฆษณาสั้น, อธิบายแอป/บริการ

## หลักคิดสำคัญ (จากงานจริง)
- **motion where it helps, stillness where it matters** — หน้าเนื้อหาที่มี**ตัวอักษรในภาพ** ให้ **นิ่ง** (ห้าม Ken Burns เพราะซูมจะตัดตัวอักษร); เฉพาะ **b-roll ที่โล้น (ไม่มีข้อความ)** ค่อยใส่ Ken Burns
- **L-cut** — ปล่อย VO เล่นต่อเนื่องคร่อมรอยตัดภาพ (panel → b-roll → panel) ให้ลื่น ไม่ใช่ตัดแข็ง
- **overlay แทนตัวอักษรในภาพ gen** — เจนภาพแบบ no-text แล้วใส่ตัวหนังสือทีหลัง (คุมง่าย + คมชัด)

## Pipeline (7 ขั้น — manual)

### 1) บท + แก่นเรื่อง
โครง **ปัญหาจริง → จุดอ่อนของเดิม → ทางแก้ใหม่ → CTA** (8–12 ฉาก, ฉากละ ~1 ประโยค). ตัวละครหลักคงที่ทุกฉาก (ชื่อ/ทรงผม/สี) เพื่อความต่อเนื่อง

### 2) storyboard → prompts.json + config/scenes
- `prompts.json` = `[{"id","prompt":"<EN image prompt>"}]` — **style block เดียวกันทุกฉาก** + คำบรรยายตัวละครซ้ำเป๊ะ + ลงท้าย `16:9`
  - ภาพ **หน้าเนื้อหา**: ให้มี title อังกฤษในภาพได้ (GPT-4o เจน text ในภาพคม) · ภาพ **b-roll**: `no text, lots of negative space` (ใส่ overlay ทีหลัง)
- บทพากย์: เขียนไทยธรรมชาติ (Gemini อ่านศัพท์อังกฤษได้ดี); ถ้าใช้ edge-tts ให้ respell ศัพท์อังกฤษเป็นไทย [[tinglish]]

### 3) ภาพการ์ตูน — chatgpt-bridge (GPT-4o)
`$CHATGPT_BRIDGE`:
```
cd /d/Project/chatgpt-bridge
node chatgpt-batch.mjs "$WORK/<PROJ>/prompts.json" "$WORK/<PROJ>/images"
```
- gotcha: ต้องมี `node_modules` (playwright) — `npm install` ก่อน; path forward-slash Windows
- headed browser; session หมด/Turnstile = login เอง · fallback ถ้า cap รูป: Cloudflare FLUX ()

### 4) Voiceover — **Gemini TTS (แนะนำ)** หรือ edge-tts
- **Gemini 2.5 TTS** (ธรรมชาติสุด): REST `gemini-2.5-flash-preview-tts`, `GEMINI_API_KEY`, voice `Charon`(ชาย)/อื่น ๆ, prefix **style prompt** (เช่น "Read in a warm professional Thai narrator voice: ") → PCM 24kHz → WAV
  - ⚠️ **preview tier RPM ต่ำ** → ต้อง **throttle ~22s/คำขอ + backoff 429** + **resume** (ข้ามไฟล์ที่มีแล้ว); คีย์ต้องเปิด **billing** (free tier quota=0 → 403/429)
  - โค้ดพร้อมใช้: `neramit/tts.py`
- **edge-tts** (ฟรี ไม่ต้องคีย์, fallback): `edge-tts --voice th-TH-NiwatNeural --text "<respelled>" --write-media vo/<id>.mp3`

### 5) Text overlay — **Remotion** (สำหรับหน้าโล้น/b-roll)
ตัวหนังสือใหญ่ คมชัด เงาบาง (browser-quality + Thai shaping ดีกว่า drawtext/ASS):
- composition `Overlay.tsx` (โหลดฟอนต์ไทยผ่าน `delayRender`/`FontFace`, text-shadow บาง + emerald accent bar) → `npx remotion still ... Overlay out.png --props='{"text":"..."}'` → **PNG โปร่งใส**
- ซ้อนบน b-roll ตอน ffmpeg: b-roll ซูม (zoompan) อยู่หลัง, overlay นิ่งคมชัดอยู่หน้า (`[bg][1:v]overlay=0:0`)
- โค้ดพร้อมใช้: `Neramit/remotion/` + `neramit/overlays.py`

### 6) ประกอบคลิป — ffmpeg (Ken Burns + b-roll + L-cut + ซับ + SFX + BGM)
- ต่อฉาก: VO → วัด duration (wave/ffprobe) → หน้าเนื้อหา **static** (scale 1920x1080 + fade dip ที่ขอบฉาก), b-roll **zoompan** (Ken Burns) + overlay
- **b-roll/L-cut:** ในฉากยาว แบ่งเวลาเป็น [panel static] + [b-roll motion×N] hard-cut ใต้ VO ต่อเนื่อง; ต่อฉากด้วย concat demuxer (sync ตรง) + dip ที่ขอบ
- ซับไทย (ถ้าต้องการ): ASS + Sarabun (`subtitles=...:fontsdir=`); **ถ้าภาพมีข้อความ/overlay แล้ว ไม่ต้องใส่ซับ** (จะทับกัน)
- **SFX:** synth whoosh (`anoisesrc`+bandpass+fade) ตอนเปลี่ยนฉาก + ding (`sine`) จุดเน้น → วางด้วย `adelay`+`amix`
- **BGM ดักใต้เสียง:** `yt-dlp` โหลดเพลง → `sidechaincompress` (BGM เป็น main, VO เป็น sidechain) → `amix` + `loudnorm=I=-15`
- โค้ดพร้อมใช้: `neramit/media.py` + `neramit/build.py`

### 7) ส่งออก
`out/final.mp4` (1920x1080, H.264+AAC, loudnorm). 9:16 สำหรับรีล → [[reel-factory]]/[[vdocut]]

## เช็คลิสต์คุณภาพ
- [ ] ตัวละคร/สไตล์ต่อเนื่องทุกฉาก
- [ ] หน้าเนื้อหา **นิ่ง** (ไม่ Ken Burns) — ตัวอักษรในภาพไม่โดนตัด; เฉพาะ b-roll ที่ซูม
- [ ] overlay (Remotion) บนหน้าโล้น: ใหญ่ คมชัด เงาบาง อ่านง่ายบนพื้นสว่าง (ใช้สีเข้ม)
- [ ] VO ธรรมชาติ (Gemini) / respell แล้ว (edge-tts); **ไม่ใส่ซับทับ overlay**
- [ ] L-cut ลื่น (VO คร่อมรอยตัด b-roll)
- [ ] เสียง loudnorm, BGM ดักใต้ VO (sidechain)

## ตัวอย่างจริง
- **Neramit** `$NERAMIT\examples\devsecops\` — DevSecOps explainer ไทย (8 ฉาก, intro/outro การ์ตูน, 4 b-roll + Remotion overlay, Gemini VO, BGM ดัก) → `github.com/<your-github-user>/neramit`
- `$WORK/thai-consular-next\vdostory\` — explainer แอป Thai Consular (edge-tts เวอร์ชันเก่า)
