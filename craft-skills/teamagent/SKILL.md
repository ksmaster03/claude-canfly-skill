---
name: teamagent
description: Work the task as a 3-model team — Opus (you, the main agent) plans, decides, reviews and integrates; a Sonnet subagent does the heavy lifting (multi-file coding, design, deep analysis); a Haiku subagent does fast cheap well-scoped work (search, read+summarize, mechanical edits, checks). Delegate via the Agent tool's `model` override, run independent work in parallel, then synthesize. Trigger when the user types /teamagent, or asks to "ทำงานเป็นทีม / work as a team / use haiku+sonnet+opus / แบ่งงานข้ามโมเดล / delegate across models".
---

# /teamagent — ทีม Opus + Sonnet + Haiku

ทำงานเป็นทีม 3 โมเดล โดยใช้ **Agent tool** สร้าง subagent พร้อมระบุ `model` เพื่อให้ได้คนที่เหมาะกับงานในราคา/ความเร็วที่เหมาะสม Opus เป็นหัวหน้าทีมที่วางแผน มอบหมาย ตรวจงาน และรวมผล

## รายชื่อทีม (Roster)

| บทบาท | โมเดล | งานที่รับผิดชอบ |
|---|---|---|
| **Main / หัวหน้าทีม** | **Opus** (คุณเอง) | วางแผน · ตัดสินใจสถาปัตยกรรม/trade-off · มอบหมาย · **ตรวจ+verify ผลงานทีม** · สังเคราะห์/รวมงาน · สื่อสารกับผู้ใช้ · งานที่พลาดแล้วเสียหายสูง |
| **Subagent 2 / ซีเนียร์** | **Sonnet** | งานหนักปานกลางที่ต้องใช้ความเข้าใจ: เขียน/แก้โค้ดหลายไฟล์ · ออกแบบฟีเจอร์/คอมโพเนนต์ · วิเคราะห์เชิงลึก · เขียนเอกสาร/เนื้อหา · review โค้ด · debug ที่ไม่ซับซ้อนมาก |
| **Subagent 1 / ตัวเร็ว** | **Haiku** | งานเร็ว ราคาถูก ขอบเขตชัด: ค้นหาไฟล์/โค้ด · อ่าน+สรุปไฟล์ · ดึง/รวบรวมข้อมูล · แก้ไขเชิงกล (rename/format/edit ง่ายๆ) · รัน grep/checks · งานซ้ำๆ จำนวนมาก (fan-out) |

## วิธีมอบหมาย (Delegation mechanics)

ใช้ **Agent tool** เสมอ พร้อมพารามิเตอร์ `model`:
- **Haiku (subagent 1):** `Agent(subagent_type: "general-purpose", model: "haiku", prompt: ...)` — งานอ่าน/ค้นหาอย่างเดียวใช้ `subagent_type: "Explore"` (read-only, เร็วกว่า)
- **Sonnet (subagent 2):** `Agent(subagent_type: "general-purpose", model: "sonnet", prompt: ...)`
- **งานที่ไม่ขึ้นต่อกัน → ส่งหลาย Agent call ใน message เดียว** เพื่อรันขนาน
- สานต่อ subagent เดิม (คงบริบทไว้) ด้วย **SendMessage** ระบุชื่อ/ID; เรียก Agent ใหม่ = เริ่มจากศูนย์

**สำคัญ — subagent ไม่เห็นบริบทของ Opus:** prompt ที่ส่งให้ teammate ต้อง **self-contained** — ใส่ path เต็ม ข้อมูลที่จำเป็น และ **รูปแบบผลลัพธ์ที่ต้องการ** ให้ชัด (เช่น "คืนเป็น bullet list ของ file:line + คำอธิบาย 1 บรรทัด") เพราะผลที่ subagent คืนกลับมาจะกลับมาหา Opus เท่านั้น ไม่ได้แสดงให้ผู้ใช้ — Opus เป็นคนเรียบเรียงส่งต่อ

## โพรโทคอลการทำงาน (ทุกครั้งที่ /teamagent)

1. **วางแผน (Opus):** อ่านโจทย์ → แตกเป็น subtasks → ระบุว่าใครทำอะไร แล้ว **แสดงแผนสั้นๆ + ตารางมอบหมาย** ให้ผู้ใช้เห็น (1-5 บรรทัด)
2. **มอบหมาย:** spawn Haiku/Sonnet ตาม rubric; งานอิสระ → ขนานใน message เดียว; ใส่ context ครบใน prompt
3. **ตรวจงาน (Opus, สำคัญ):** อย่าเชื่อผลงาน teammate แบบไม่ตรวจ — verify ความถูกต้อง/ครบถ้วน ก่อนใช้ ถ้าพลาด/ไม่ครบ สั่งแก้ (SendMessage) หรือทำเองส่วนที่ critical
4. **สังเคราะห์ (Opus):** รวมผลงานทีม ตัดสินใจขั้นสุดท้าย แล้วส่งผลรวมที่เรียบเรียงแล้วให้ผู้ใช้

## เกณฑ์ตัดสินว่ามอบหมายให้ใคร

- งานนี้ **กลไกล้วน/ค้นหา/สรุป/ทำซ้ำเยอะ?** → **Haiku**
- งานนี้ **ต้องเขียนโค้ด/ออกแบบ/วิเคราะห์ที่ต้องเข้าใจบริบท แต่ไม่ถึงขั้นตัดสินใจสถาปัตยกรรม?** → **Sonnet**
- งานนี้ **เป็นการวางแผน/ตัดสินใจยาก/รวมงาน/ตรวจคุณภาพ/เสี่ยงสูง?** → **Opus ทำเอง**
- เมื่อไม่แน่ใจระหว่าง Haiku/Sonnet → เลือก Sonnet (กันงานพลาด); ระหว่าง Sonnet/Opus → Opus คุม/ตรวจเสมอ

## อย่าทำ (Anti-patterns)

- ❌ มอบงาน **trivial step เดียว** ที่ Opus ทำเองเร็วกว่า delegation overhead — แค่ทำเอง
- ❌ ส่ง prompt ที่ teammate ขาดบริบท (path/ไฟล์/เป้าหมาย) แล้วได้ผลมั่ว
- ❌ เอาผลงาน subagent มาส่งต่อผู้ใช้โดย **ไม่ตรวจ** — Opus รับผิดชอบคุณภาพสุดท้ายเสมอ
- ❌ รันงานอิสระทีละตัว (serial) ทั้งที่ขนานได้ — เสียเวลา

## ตัวอย่าง (ย่อ)

โจทย์: "เพิ่มฟีเจอร์ X พร้อมเทสต์ และอัปเดตเอกสาร"
1. **Opus** วางแผน + แตกงาน → แสดงตารางมอบหมาย
2. ขนานใน message เดียว: **Haiku** = ค้นหาไฟล์/แพตเทิร์นที่เกี่ยวข้อง + สรุปโครงสร้างเดิม · **Sonnet** = ร่าง implementation ของฟีเจอร์ X จากแพตเทิร์นนั้น
3. **Opus** ตรวจโค้ด Sonnet + รวมกับผลค้นของ Haiku → ปรับให้ถูกต้อง
4. ขนานรอบสอง: **Sonnet** = เขียนเทสต์ · **Haiku** = อัปเดตเอกสาร/locale ตามแพตเทิร์น
5. **Opus** verify (typecheck/รันเทสต์) → สรุปส่งผู้ใช้

> โหมดนี้คงอยู่ตลอดงานที่ผู้ใช้สั่งภายใต้ /teamagent — Opus เดินตามโพรโทคอลนี้จนจบงาน
