---
name: vidcraft
description: วางแผน + สร้าง + ประกอบคลิปวิดีโอให้ "น่าสนใจ หยุดนิ้ว" — director's playbook (hook/retention/pacing/SFX-as-hook) + pipeline ประกอบคลิปนำเสนอ/explainer จากสไลด์ภาพ+VO (Ken Burns, xfade, Netflix subs, progress bar, intro hook, outro CTA, SFX) + ffmpeg recipe cookbook & gotchas. Trigger เมื่อผู้ใช้พิมพ์ /vidcraft หรือขอ "วางแผนคลิป / ทำคลิปให้น่าสนใจ / ทำคลิปนำเสนอ / explainer / presentation video / คลิปจากสไลด์ / hook / สคริปต์คลิป / ทำคลิปจากภาพ+เสียงพากย์". ใช้คู่กับ [[vdocut]] (ตัดฟุตเทจ) และ [[reel-factory]] (รีลข่าว 9:16).
---

# /vidcraft — วางแผน·สร้าง·ประกอบคลิป (ผู้กำกับ + คนประกอบ)

สกิลนี้คือชั้น **ความคิดสร้างสรรค์ + การประกอบคลิปจากสไลด์/ภาพ** ที่ vdocut (ตัดฟุตเทจ) กับ reel-factory (รีลข่าว) ไม่ครอบคลุม. ตกผลึกจากงานคลิปนำเสนอจริง + การ research คลิปเก่ง (SFX-as-hook, edutainment, YouTube editing studies). คุย/ยืนยันแผนเป็นภาษาไทยก่อนเรนเดอร์เสมอ; autonomous หลังเคาะแผน.

## 0. Route ก่อน — งานนี้คือแบบไหน?
- **มีฟุตเทจอยู่แล้ว ต้องตัด/เกรด/ใส่ซับ** → ไป **[[vdocut]]**.
- **รีลแนวตั้ง 9:16 เล่าข่าว/แชร์ข้อมูล จากหัวข้อเดียว** (VO+ภาพ AI+แบนเนอร์) → ไป **[[reel-factory]]**.
- **คลิปนำเสนอ/explainer/โปรดักต์ จากสไลด์ภาพ → narrated video** (16:9 หรือ 9:16, intro hook + outro CTA + progress + SFX) → **ใช้ §3 ของสกิลนี้**.
- **ไม่ว่าเส้นทางไหน → เริ่มที่ §1 วางแผนความน่าสนใจก่อนเสมอ** แล้วค่อยลงมือ.

## 1. PLAN — Engagement playbook (ทำให้ "หยุดนิ้ว")
ตกผลึกจากคลิปที่ดูมา. คุยกับผู้ใช้แล้วเลือกใช้ให้พอดีกับ tone (consumer = จัดเต็ม; B2B/enterprise = หยิบบางอัน คงความพรีเมียม).

**HOOK (0–3 วิ) = สำคัญสุด.** เลือก 1 แบบ:
- *Curiosity gap* — เปิดวงโคจรคำถามที่ต้องดูต่อ ("องค์กรคุณกำลังส่งความลับให้ AI โดยไม่รู้ตัวหรือเปล่า?")
- *Counterintuitive / contrarian* — ขัดสามัญสำนึก ("ทำไมแบงก์ไม่ชอบคนโปะหนี้" — Mr.White)
- *Bold stat / number* — ตัวเลขแรง ("92% ของ...")
- *Question / problem-agitation* — จี้ปัญหาคนดู
- **Audio-first**: ใส่ "เสียง" (riser→impact) ใน **วินาทีแรก** ก่อนภาพจะนิ่ง — คนรับเสียงก่อนภาพ (บทเรียนแมนหยุดนิ้ว,).

**โครงสร้าง**: HOOK → STAKES/บริบท → VALUE (เนื้อหลัก, **1 ไอเดียหลักต่อคลิปสั้น**) → PAYOFF → **CTA**. อย่ายัดหลายไอเดีย.

**Pacing (retention)**:
- เปลี่ยนภาพทุก **~2–4 วิ** (Mr.White ตัด ~2 วิ/ช็อต). ห้ามเฟรมนิ่งเกิน ~5 วิ — อย่างน้อยต้องมี Ken Burns ขยับ.
- **Pattern interrupt** — สลับมุม/ขนาดตัวอักษร/จังหวะ.
- **Open loop** — "เดี๋ยวจะบอก..." ดึงให้ดูจนจบ; **CTA ไต่ระดับ** ตอนปิด.
- **Progress bar** บอกความคืบหน้า เพิ่ม watch-time.

**Clarity / visual**:
- **ตัวเลข/สถิติหลัก ทำใหญ่เต็มจอ + ย้ำซ้ำ** (Mr.White ย้ำ "92%" หลายเฟรม).
- **Visual metaphor 1 ตัว** แทนนามธรรม (เช่น ปราการ = โล่กั้น "data → [ปราการ] → AI").
- คอนทราสต์สูง, โลโก้/แบรนด์ติดทุกเฟรม, **ซับเสมอ** (คนดูส่วนใหญ่ปิดเสียง).

**Audio**: VO −14 LUFS, เพลงเป็น bed ที่ duck ใต้เสียงพูด, **SFX เป็นเครื่องหมายวรรคตอนที่ beat สำคัญ** (ไม่ใส่รัว) +.

**Platform/format**: 9:16 = FB/IG/TikTok/Shorts; 16:9 = YouTube/LinkedIn/นำเสนอ. เผื่อขอบปลอดภัยให้ซับ/UI ของแพลตฟอร์ม.

## 2. Pre-production checklist (ก่อนเรนเดอร์ — ยืนยันกับผู้ใช้)
ความยาว/aspect · กลุ่มเป้าหมาย+tone · **hook 1 ประโยค** · 1 ไอเดียหลัก · CTA · เสียง (Niwat/Premwadee + [[tinglish]]) · เพลง · ต้องมีซับ/progress/SFX ไหม · โลโก้. **เสนอแผน 4–8 ประโยคภาษาไทย แล้วรอ "เอาตามนี้"**.

## 3. ประกอบคลิปนำเสนอจากสไลด์ (pipeline ที่พิสูจน์แล้ว)
ภาพ slide (16:9) N รูป + โลโก้ + VO ต่อสไลด์ → narrated video พร้อม transition/เกรด/ซับ/progress/intro hook/outro CTA/SFX.
**Reference implementation** — สคริปต์ 6 ตัวที่พิสูจน์แล้ว แยกหน้าที่ชัดเจน (สร้างเองตามชื่อนี้ได้เลย): `build_video.py` คลิปต่อสไลด์, `build_video2.py` xfade+เกรด, `reburn.py` ซับ Netflix, `build_video3_final.py` intro/outro+concat, `build_sfx.py` SFX layer, `merge_images.py` รวมเป็น PPTX. ลำดับ:

1. **VO**: edge-tts ผ่าน `python -m edge_tts` (ดู §4 SAC) Niwat + Tinglish → `vo01..N.mp3`.
2. **คลิปต่อสไลด์**: **SINGLE-frame image input** + `zoompan` (Ken Burns, สลับทิศตาม index) + `eq` เกรด + overlay โลโก้ + `format=yuv420p`; `-t = lead+vo_dur+tail`. **เข้ารหัสทุกคลิปด้วยพารามิเตอร์เดียวกัน** (libx264, 30fps, yuv420p, `-video_track_timescale 30000`) เพื่อ concat ได้เนียน.
3. **Transition**: xfade chain (สลับชนิด, `D_TR~0.6`) → deck video. *(หมายเหตุ: xfade ออก timebase 1/15360 — ถ้าจะต่อ intro/outro ทีหลังต้องซ่อม PTS ก่อน, §4.)*
4. **ซับ Netflix-style** (§4): สร้าง SRT (chunker ≤40 ตัวอักษร) → burn ด้วย Leelawadee UI.
5. **เสียง**: VO ต่อ segment + BGM **L-shape** (ดังตอนเปิด 3 วิ แล้วลงเป็น bed) + `sidechaincompress` duck + loudnorm −14. ถ้ามี intro/outro ใช้ **segmented loudnorm** (loudnorm แต่ละท่อนแยก แล้วต่อ).
6. **Intro hook + Outro CTA**: คลิปแยก (single-frame zoompan + ASS kinetic text) → **concat DEMUXER `-c copy`** (พารามิเตอร์ตรงกัน, deck pixels ไม่ถูกแตะ = ภาพไม่ดำ). อย่าใช้ concat filter กับ deck ที่ timebase แปลก.
7. **Progress bar**: `drawbox=x=0:y=ih-5:w='iw*t/{T}':h=5:color=0xRRGGBB@0.9:t=fill` ในพาส burn ซับ.
8. **SFX layer** (§5): สร้าง riser/impact → วางด้วย adelay+amix เป็น track เต็มความยาว → amix ใต้เสียงสุดท้าย + loudnorm → re-mux **`-c:v copy`** (เร็ว ไม่แตะวิดีโอ).
9. **QA** (§6).

## 3.1 Tighten ฟุตเทจยาว (meeting/demo recording → คลิปกระชับ ส่งลูกค้า)
สำหรับไฟล์อัดประชุม Teams/Zoom ยาวๆ ("ตัดให้กระชับ คงเนื้อหาเต็ม"). พิสูจน์กับงาน Surapon (106→98 นาที).
1. **silencedetect** หา dead air: `ffmpeg -i SRC -af silencedetect=noise=-30dB:d=1.5 -vn -f null - 2>sil.log` (decode เสียงอย่างเดียว เร็ว). ระวังหัวคลิปมักเป็น "ห้องรอ" เงียบยาว (เคสนี้ 2.5 นาทีแรก).
2. **keep-list** = complement ของ silence gaps (เหลือ pad ~0.4s ต่อข้างให้จังหวะธรรมชาติ); ทิ้ง segment <1s. gaps ยาว (≥8s) = เดาเป็น section break.
3. **ตัดในพาสเดียว** ด้วย select/aselect (ไม่ใช่ extract+concat ทีละชิ้น): วิดีโอ `select='between(t,a,b)+between(...)+...',setpts=N/FRAME_RATE/TB,fps=30`; เสียง `aselect='<expr เดียวกัน>',asetpts=N/SR/TB` → ภาพ/เสียง sync เพราะ expr เดียวกัน. (expr ยาวหลายพันตัวอักษรได้ ffmpeg รับไหว)
4. รวมกับ §3: + grade เบา + logo overlay มุม (แบรนด์) + progress bar + BGM duck (ระวัง gotcha §4 BGM loop) + loudnorm. เสียงประชุม mono 16kHz → loudnorm ช่วยให้ฟังง่ายขึ้นมาก.
5. customer-facing: + intro/outro card แบรนด์ + ตัดช่วง sensitive (ถ้าระบุ timestamp ได้; การหา "ช่วงที่ไม่ควรให้ลูกค้าเห็น" อัตโนมัติต้องสแกนเนื้อหา = แพง — ถามผู้ใช้ก่อน).
6. **render ครั้งเดียว ~1 ชม.วิดีโอ ใช้ veryfast/CRF 23** (จอแชร์ compress ง่าย) → เร็วพอ. ทดสอบลุค 60 วิก่อนเรนเดอร์เต็มเสมอ.

## 4. ffmpeg recipe cookbook + GOTCHAS (จ่ายด้วยเลือดมาแล้ว)
**Environment**: ffmpeg/ffprobe บน PATH. `uv` ที่ `...WinGet\Packages\astral-sh.uv_...\uv.exe`. `PYTHONIOENCODING=utf-8` เสมอ.

- ⛔ **Smart App Control บล็อก .exe**: `edge-tts.exe` → WinError 4551 → ใช้ **`python -m edge_tts`**. `yt-dlp.exe` ถูกบล็อก → **`uv tool run yt-dlp`**.
- ⛔ **Frame explosion**: `-loop 1 -t D -i img` + `zoompan d=frames` = คูณเฟรม (input×d) → ไฟล์บวมเป็นนาที + ภาพดำ. **FIX: input เป็นภาพเฟรมเดียว** (`-i img` ไม่มี -loop/-t) + `zoompan d=frames:s=WxH:fps=30` + `-t D` ที่ output.
- ⛔ **Timebase balloon**: เอาต์พุต xfade มี `tb=1/15360`; พอ re-encode ด้วย `-r 30` → duration บวม ~×12. **FIX: rebuild PTS** `-vf "setpts=N/30/TB" -fps_mode cfr -r 30 -video_track_timescale 30000`.
- ⛔ **Concat ภาพดำ/ผิด**: concat **filter** กับ source timebase แปลกทำ deck ดำได้; concat **demuxer `-c copy`** ต้องพารามิเตอร์ **เหมือนกันเป๊ะ** (fps/profile/pix_fmt/timescale). **FIX: เข้ารหัสทุกท่อนเหมือนกัน → demuxer -c copy** (ภาพไม่ถูกแตะ → สว่างชัวร์) → แล้วค่อย subs/progress/audio ในพาส single-input.
- ⛔ **A/V drift**: ทุก audio segment ต้องยาวเท่า video segment ของมัน — pad ด้วย `apad -t <len>` ไม่งั้นท่อนหลังเลื่อน.
- ⛔ **BGM loop overruns video**: `-stream_loop -1` BGM + `amix` (default `duration=longest`) → เสียงยาวเกินวิดีโอ (เพลงเล่นต่อหลังภาพจบ → ไฟล์ยาวผิด). **FIX: `amix=inputs=2:duration=first:normalize=0`** (ใส่ speech/content เป็น input แรก) หรือถ้าเรนเดอร์ไปแล้ว trim เสียงให้เท่าวิดีโอ + re-mux `-c:v copy` (เช็ค `ffprobe -select_streams v/a stream=duration` ว่า v==a). เจอจากงาน Surapon meeting cut.
- **ซับ Netflix-style (ไทยไม่หนา + วรรณยุกต์ไม่ซ้อน)**: `subtitles=subs.srt:force_style='FontName=Leelawadee UI,FontSize=23,Bold=0,Outline=1.3,Shadow=1,MarginV=50,PrimaryColour=&H00FFFFFF,OutlineColour=&H00000000'`. (Leelawadee UI = sans ไทยน้ำหนักปกติ; เลี่ยง Tahoma+Bold+outline หนา ที่ทำตัวหนา/วรรณยุกต์ซ้อน). 9:16 ต้องใช้ **.ass** ฝัง PlayResX/Y (ดู [[reel-factory]] §gotcha1).
- **BGM L-shape + duck**: เพลงดัง ~0.5 ช่วงเปิด → ลงเหลือ ~0.14 เป็น bed (`volume='if(lt(t,1.2),0.5,...)':eval=frame`) + `sidechaincompress=threshold=0.04:ratio=8:attack=5:release=350` (key = VO).
- **Loudnorm**: `-14 LUFS / -1 dBTP / LRA 11` บนเสียงสุดท้ายเสมอ (social-ready).
- **Path/encoding**: OneDrive paths มีช่องว่าง/ไทย → เรียก ffmpeg ผ่าน Python (`subprocess` list args) เลี่ยง bash globbing; ไฟล์มี # → hardlink ASCII (vdocut §4).

## 5. Engagement add-ons — "make it pop" toolkit (ffmpeg ล้วน, ไม่ต้องมีไฟล์ SFX)
- **riser** (ไต่ตึง): `anoisesrc=d=0.85:c=pink:a=0.5 -af "highpass=f=400,lowpass=f=7000,volume='pow(t/0.85,2)':eval=frame,afade=t=out:st=0.75:d=0.1"`
- **impact** (boom+click): boom `aevalsrc='0.8*exp(-t*9)*sin(2*PI*62*t)':d=0.6` + click `anoisesrc=d=0.10:c=white,highpass=f=1800` → amix → lowpass 9000 → fade.
- **whoosh** (เปลี่ยนฉาก): `anoisesrc=d=0.6:c=pink` + bandpass sweep + fade.
- **วาง SFX แบบไม่ re-render วิดีโอ**: สร้าง track เต็มความยาว (`adelay=ms|ms` + `volume` ต่อ hit → `amix=normalize=0` → `apad`), แล้ว `amix` ใต้เสียงสุดท้าย + `loudnorm` (กันคลิป), re-mux `-c:v copy`. วาง hit ที่: วินาทีแรก (audio-first), เผยแบรนด์, เปลี่ยน section, outro. ~5–6 จุด/4 นาที = พอดี.
- **Animated stat callout**: ASS `\fad()` + `\t(\fscx\fscy)` เด้งตัวเลขใหญ่ตอน VO พูดถึง; หรือ drawtext fade-in.
- **Ken Burns**: `zoompan z='min(zoom+0.0006,1.10)'` สลับ x/y ตาม index ให้ไม่ซ้ำทิศ.

## 6. QA / self-eval (บน output ที่เรนเดอร์จริง)
- **ความสว่าง**: แคปเฟรม (Read PNG) — deck/เนื้อหาควรสว่าง (~13–25/255). **ถ้าดำ (<8) = bug** (สงสัย frame-explosion/timebase, §4 — ไม่ใช่ที่ source).
- **เสียงไม่คลิป**: `volumedetect` → `max_volume ≤ -1 dB`. SFX beat ควรเห็น transient เด้งที่จุดที่วาง.
- **A/V sync + duration**: ตรวจ `ffprobe duration` ตรงแผน; เฟรม intro/deck/outro ขึ้นถูกที่.
- **ซับ**: แคปเฟรมจริง ยืนยันว่า burn แล้ว + ไม่หนา/ไม่ซ้อน.
- เก็บไฟล์สำรองเวอร์ชันดีไว้เสมอ ก่อนทับด้วยเวอร์ชันใหม่ (เช่น เก็บ -v2/-v3 ไว้).

## 7. Anti-patterns
- ❌ ลงมือเรนเดอร์ก่อนเคาะ hook + 1 ไอเดียหลัก + CTA (§1–2).
- ❌ ยัดหลายไอเดียในคลิปสั้นเดียว.
- ❌ `-loop 1` + `zoompan d=` (frame explosion) — ใช้ single-frame input.
- ❌ concat filter กับ deck timebase แปลก / concat demuxer ที่พารามิเตอร์ไม่ตรง → ภาพดำ.
- ❌ `edge-tts.exe` / `yt-dlp.exe` ตรงๆ (SAC บล็อก) — ใช้ `python -m edge_tts` / `uv tool run yt-dlp`.
- ❌ ซับไทยด้วย Tahoma+Bold+outline หนา (ตัวหนา/วรรณยุกต์ซ้อน) — ใช้ Leelawadee UI regular.
- ❌ ลืม loudnorm / ลืม duck BGM / ใส่ SFX รัวจนล้น.
- ❌ ขนเทคนิค consumer-meme (มาสคอตการ์ตูน, สีจัดจ้าน) ลงงาน B2B โดยไม่ปรับ tone.
- ❌ เฟรมนิ่งเกิน 5 วิ ไม่มี motion.
- ❌ ทับไฟล์เวอร์ชันดีโดยไม่สำรอง.

## 8. Cold start
ถามงาน → §0 route → §1 วางแผน hook/โครงสร้าง → §2 ยืนยันแผนภาษาไทย → ลงมือ (§3 หรือส่งต่อ vdocut/reel-factory) → §6 QA → ส่งมอบ + เสนอปรับจูน. งานนำเสนอ/สไลด์ ให้สร้างสคริปต์ 6 ตัวตาม §3 เป็นจุดตั้งต้น.
