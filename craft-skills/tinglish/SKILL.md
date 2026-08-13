---
name: tinglish
description: ออกเสียงคำภาษาอังกฤษแบบสำเนียงไทย (Tinglish) สำหรับงาน TTS/พากย์/voiceover — แปลงคำอังกฤษเป็น "คำอ่านไทย" ก่อนป้อนเข้า engine ใดๆ (edge-tts, F5-TTS, ElevenLabs) เพื่อให้เสียงออกแบบคนไทยพูดอังกฤษ ไม่ใช่สำเนียงฝรั่ง. ใช้ทุกครั้งที่เขียนสคริปต์/บทพูดที่จะให้ TTS อ่าน แล้วมีคำอังกฤษปนอยู่. Trigger เมื่อผู้ใช้พิมพ์ /tinglish, ขอ "สำเนียงไทย / ออกเสียงอังกฤษแบบไทย / Tinglish / respell / คำอ่านไทย", หรือกำลังเตรียมบทพูดให้ TTS/พากย์/dub/voiceover ที่มีคำอังกฤษ.
---

# /tinglish — ออกเสียงอังกฤษสำเนียงไทย

**หลักการเดียวที่ต้องจำ:** TTS ทุกตัว (edge-tts, F5-TTS, ElevenLabs) จะออกเสียงอังกฤษ "สำเนียงไทย" ได้ก็ต่อเมื่อ **เขียนคำอังกฤษเป็นคำอ่านภาษาไทยก่อนป้อนเข้า engine** เช่น `software` → `ซอฟต์แวร์`, `Claude` → `คล้อด`, `agent` → `เอเจ้นท์`. ถ้าปล่อยเป็นตัวอักษรอังกฤษ engine จะสลับไปออกสำเนียงเจ้าของภาษาทันที

## เมื่อไหร่ใช้
ทุกครั้งที่เตรียม **บทพูด/สคริปต์สำหรับ TTS หรือพากย์** แล้วมีคำอังกฤษปน — แปลงคำอังกฤษเป็นคำอ่านไทยด้วย dictionary + กฎด้านล่าง ก่อนส่งเข้า engine **อย่าแปลงข้อความที่เป็นซับไตเติล/ข้อความบนจอ** (ตรงนั้นคงคำอังกฤษไว้ให้อ่านสวย — Tinglish ใช้กับ "เสียง" เท่านั้น)

## วิธีใช้เร็วสุด (helper)
```
python <skill_dir>/respell.py "ใช้ model ของ Anthropic สร้าง agent"
# -> ใช้ โมเดล ของ แอนโทรปิก สร้าง เอเจ้นท์
```
หรือใน Python:
```python
import sys; sys.path.insert(0, r"~/.claude/skills/tinglish")
from respell import make_respeller
respell = make_respeller()           # โหลด tinglish_dict.json อัตโนมัติ
gen_text = respell(thai_text_with_english)   # ป้อนเข้า edge-tts / F5 / ฯลฯ
```
`respell.py` เทียบคีย์ case-insensitive, ตัดที่ขอบคำอังกฤษ, จับวลียาวก่อนคำเดี่ยว (`software engineering` ก่อน `software`)

## ลำดับการทำงาน
1. คำที่อยู่ใน `tinglish_dict.json` → ใช้คำอ่านในนั้น (คุมแบรนด์/ศัพท์เทคให้เป๊ะ)
2. คำที่ไม่อยู่ใน dict → respell เองด้วย **กฎ Tinglish (§กฎ)** แล้ว **เพิ่มเข้า dict** เพื่อใช้ซ้ำ
3. ตรวจเสียงจริงด้วยตัวอย่างสั้นก่อนเรนเดอร์ทั้งงาน (เสียงเพี้ยน = แก้คำอ่านใน dict)

## §กฎ Tinglish (สำหรับ respell คำที่ไม่อยู่ใน dict)
ดัดแปลงตามสัทศาสตร์ที่คนไทยออกจริง:

**พยัญชนะท้าย (final)**
- `-l` → เสียง "ว"/"น" : school→สคูน, grill→กริว, level→เลเวิ่ล/เลเวว
- คลัสเตอร์ท้ายตัดเหลือตัวเดียว : act→แอ๊ก, next→เน็กซ์→เน็ก, product→โปรดักท์
- `-s/-es` ท้ายมักหาย : agents→เอเจ้นท์, models→โมเดล
- `-v` ท้าย → "พ" ; `-g/-z/-j` ท้าย → ก/ส/ช (devoice)

**พยัญชนะต้น/แทนเสียงที่ไทยไม่มี**
- `th` (θ/ð) → ท/ด : think→ติ้งก์, the→เดอะ
- `v-` → "ว" : video→วิดีโอ, value→แวลู
- `r` → "ร/ล" หรือหายท้ายคำ
- `sh` → "ช" : show→โชว์ ; `z` → "ส/ซ" : zip→ซิป
- `g` → "ก" : google→กูเกิ้ล

**คลัสเตอร์ต้น s+stop → แทรกสระ "ะ/เออะ"**
- start→สตาร์ท, school→สคูน, sport→สปอร์ต

**สระประสม → สระยาว** (ยกเว้นลงท้าย i/u ที่กลายเป็นสระประสมไทย)
- tie→ไท, view→วิว

**วรรณยุกต์/เสียงสูงต่ำ** : ใส่ให้เป็นธรรมชาติแบบที่คนไทยพูด (มักลงเสียงตรี/จัตวาในพยางค์เน้น) เช่น AI→เอไอ, OK→โอเค

## รวมกับ TTS
- **edge-tts** : `edge-tts --voice th-TH-NiwatNeural --text "<respelled>" ...`
- **F5-TTS (โคลนเสียง)** : ใส่ respelled text เป็น `gen_text` (ดูตัวอย่าง make_dub_f5.py ในโปรเจกต์ Problem Solvers)
- **ElevenLabs multilingual** : ก็ใช้ respelled text เช่นกัน

## Anti-patterns
- ❌ ส่งคำอังกฤษดิบเข้า TTS แล้วหวังสำเนียงไทย (จะได้สำเนียงฝรั่ง)
- ❌ respell ข้อความที่เป็นซับ/ข้อความบนจอ (ใช้กับเสียงเท่านั้น)
- ❌ แปลงชื่อแบรนด์มั่วโดยไม่เช็ก dict (Claude=คล้อด ไม่ใช่ คลอดี)
- ❌ ลืมเรียงคีย์ยาว→สั้น เวลา match (วลีต้องชนะคำเดี่ยว)

อ้างอิงสัทศาสตร์: [Tinglish (Wikipedia)](https://en.wikipedia.org/wiki/Tinglish) · [A Systemic Review of Thai-Accented English Phonology](https://files.eric.ed.gov/fulltext/EJ1348382.pdf)
