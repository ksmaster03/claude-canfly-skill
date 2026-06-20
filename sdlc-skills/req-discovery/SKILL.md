---
name: req-discovery
description: เก็บและวิเคราะห์ requirement อย่างเป็นระบบ — ระบุ stakeholder, เลือกเทคนิค elicitation, แปลงความต้องการดิบเป็น user story + acceptance criteria แล้วจัดลำดับด้วย MoSCoW เป็น product backlog (Elicit, analyze and prioritize requirements into a ready-to-build backlog). Trigger เมื่อผู้ใช้พิมพ์ /req-discovery หรือขอ "เก็บ requirement / สัมภาษณ์ผู้ใช้ / user story / backlog / requirement gathering / elicitation".
category: sdlc
phase: "01 Requirement Discovery"
---

# /req-discovery — เก็บและวิเคราะห์ความต้องการ (Requirement Elicitation)

เฟสแรกของ SDLC: ดึงความต้องการจาก stakeholder ให้ครบและถูกตัว แล้วแปลงเป็น **user story + acceptance criteria + product backlog ที่จัดลำดับแล้ว** พร้อมส่งต่อให้เฟสเขียนสเปก ไม่ใช่แค่จดสิ่งที่ลูกค้าพูด แต่หา "ปัญหาจริง" ที่อยู่ใต้ความต้องการ (อ้าง BABOK v3 — Elicitation & Collaboration, Requirements Analysis & Design Definition)

## ใช้ตอนไหน

- เริ่มโปรเจกต์/ฟีเจอร์ใหม่ ยังไม่มี requirement เป็นลายลักษณ์อักษร
- requirement กระจัดกระจาย (อยู่ในแชต อีเมล หัวคน) ต้องรวบและจัดระเบียบ
- ลูกค้าบอก "อยากได้ระบบ X" แต่ยังไม่รู้ว่าทำไม ใครใช้ และวัดความสำเร็จยังไง
- ต้องตั้ง product backlog ตั้งต้นก่อนวางแผน sprint
- **อย่าใช้เฟสนี้** เขียน FR/NFR ทางการ/SRS → ไปที่ `/fr-nfr-spec` · เขียน business rule/calculation ละเอียด → `/business-logic-spec`

## Input ที่ต้องถามก่อนเริ่ม

ถามให้ครบก่อนลงมือ ถ้าผู้ใช้ตอบไม่ได้ ให้ระบุเป็น **assumption** แล้วเดินต่อ:

1. **บริบทธุรกิจ** — ทำธุรกิจอะไร ปัญหา/โอกาสที่อยากแก้คืออะไร (pain ปัจจุบัน)
2. **เป้าหมาย & ตัววัด** — business goal คืออะไร วัดความสำเร็จด้วยอะไร (KPI/metric)
3. **Stakeholder** — ใครเกี่ยวข้องบ้าง (ผู้ใช้จริง, ผู้อนุมัติ, ผู้จ่ายเงิน, ทีม IT, regulator)
4. **ขอบเขต & เดดไลน์** — งบ/เวลา/ทีม, ระบบเดิม (as-is) มีอะไร, อะไรอยู่นอกขอบเขตแน่ ๆ
5. **ข้อจำกัด & สมมติฐาน** — เทคโนโลยีบังคับ, กฎหมาย/compliance (เช่น PDPA), การเชื่อมระบบเดิม
6. **ช่องทาง elicitation ที่ทำได้จริง** — สัมภาษณ์ได้ไหม จัด workshop ได้ไหม มีเอกสารเดิมให้อ่านไหม

## ขั้นตอน (Playbook)

1. **ระบุ & จัดกลุ่ม stakeholder** — ทำ stakeholder map ตามแกน **อำนาจ (Power) × ความสนใจ (Interest)** เพื่อรู้ว่าใครต้อง "Manage closely", ใครแค่ "Keep informed"
2. **เลือกเทคนิค elicitation** ให้เหมาะกับแต่ละกลุ่ม (ดูตารางในขั้น Output) — ปกติผสมหลายเทคนิค ไม่ใช้อย่างเดียว
3. **เก็บความต้องการดิบ** — สัมภาษณ์/workshop/สังเกตงานจริง บันทึกคำพูดต้นฉบับ แยก "ความต้องการ (need)" ออกจาก "วิธีแก้ที่ลูกค้าเสนอ (solution)" เสมอ
4. **เขียน Problem statement & business goal** — สรุปปัญหา → เป้าหมาย → ตัววัด เป็นย่อหน้าเดียวที่ทุกคนเห็นตรงกัน
5. **As-is vs To-be** — วาด/อธิบายกระบวนการปัจจุบันเทียบกับที่อยากให้เป็น เพื่อเห็น gap ที่ระบบต้องอุด
6. **สร้าง User persona** — ผู้ใช้หลัก 2-4 แบบ (เป้าหมาย, งานที่ทำ, pain, ระดับทักษะ tech)
7. **จัดเป็น Epic → User story** — ก้อนใหญ่ (epic) แตกเป็น story รูปแบบ *As a... I want... so that...* ตรวจทุก story ด้วย **INVEST** (Independent, Negotiable, Valuable, Estimable, Small, Testable)
8. **เขียน Acceptance criteria** แบบ Gherkin (Given/When/Then) ต่อ story — ระบุเงื่อนไขที่ทำให้ "ถือว่าเสร็จ" ครอบ happy path + edge case + error
9. **จัดลำดับด้วย MoSCoW** — Must / Should / Could / Won't (this time) คุยกับผู้มีอำนาจตัดสินใจให้ commit
10. **ประกอบเป็น Product backlog** — เรียง story ตามลำดับ + แนบ assumptions / constraints / out-of-scope ให้ครบ ส่งต่อ `/fr-nfr-spec`

## Output / Artifact (เทมเพลตพร้อมใช้)

### 1) Problem statement (กรอกแทนข้อความในวงเล็บ)
> ปัจจุบัน **(ใคร)** ประสบปัญหา **(ปัญหา/pain)** ทำให้ **(ผลกระทบเชิงธุรกิจ)** เราต้องการ **(เป้าหมาย to-be)** วัดความสำเร็จด้วย **(KPI/metric)**

### 2) Stakeholder map (Power × Interest grid)

| Stakeholder | บทบาท | อำนาจ (สูง/ต่ำ) | ความสนใจ (สูง/ต่ำ) | กลยุทธ์ | เทคนิค elicitation |
|---|---|---|---|---|---|
| ผู้จัดการคลัง | ผู้ใช้หลัก + อนุมัติ | สูง | สูง | Manage closely | Interview + Observation |
| พนักงานหน้างาน | ผู้ใช้จริง | ต่ำ | สูง | Keep informed | Workshop + Observation |
| ฝ่าย IT | ผู้ดูแลระบบเดิม | สูง | ต่ำ | Keep satisfied | Document analysis |
| ฝ่ายบัญชี | ผู้รับ output | ต่ำ | ต่ำ | Monitor | Questionnaire |

### 3) เทคนิค elicitation — ใช้เมื่อไหร่

| เทคนิค | เหมาะเมื่อ | ระวัง |
|---|---|---|
| Interview (1:1) | เจาะลึกความต้องการ/ปัญหารายคน | bias ของผู้ถาม, อย่าถามนำ |
| Workshop / JAD | ต้องการ consensus จากหลายฝ่ายเร็ว | ต้องมี facilitator คุมเวลา |
| Observation (shadowing) | งานจริงต่างจากที่เล่า / หา as-is | คนถูกสังเกตอาจเปลี่ยนพฤติกรรม |
| Document analysis | มีระบบ/ฟอร์ม/SOP เดิม | เอกสารอาจล้าสมัย |
| Prototyping | requirement คลุมเครือ เห็นภาพแล้วค่อยชัด | อย่าให้เข้าใจผิดว่าเสร็จแล้ว |
| Questionnaire / survey | ผู้ใช้จำนวนมาก กระจายพื้นที่ | ออกแบบคำถามไม่ดี = ข้อมูลขยะ |

### 4) User story (ตัวอย่างเต็ม + acceptance criteria)

**Epic:** จัดการการเบิกสินค้าออกจากคลัง
**Story US-012:**
> **As a** พนักงานคลัง
> **I want** สแกนบาร์โค้ดสินค้าเพื่อบันทึกการเบิกออก
> **so that** สต็อกอัปเดตทันทีโดยไม่ต้องคีย์มือ

INVEST check: Independent ✓ · Valuable ✓ (ลดเวลา/ลด error) · Estimable ✓ · Testable ✓

**Acceptance Criteria (Gherkin):**
```gherkin
Scenario: สแกนบาร์โค้ดที่ถูกต้อง
  Given พนักงานล็อกอินและเปิดหน้า "เบิกสินค้า"
  When สแกนบาร์โค้ดของสินค้าที่มีในสต็อก
  Then ระบบแสดงชื่อสินค้าและจำนวนคงเหลือ
  And ลดจำนวนสต็อกลง 1 หน่วยทันที

Scenario: สแกนบาร์โค้ดที่ไม่มีในระบบ
  Given พนักงานเปิดหน้า "เบิกสินค้า"
  When สแกนบาร์โค้ดที่ไม่พบในฐานข้อมูล
  Then ระบบแสดงข้อความ "ไม่พบสินค้า" และไม่แก้ไขสต็อก

Scenario: สินค้าหมดสต็อก
  Given สินค้ามีจำนวนคงเหลือ = 0
  When สแกนบาร์โค้ดของสินค้านั้น
  Then ระบบเตือน "สต็อกหมด" และไม่ให้เบิก
```

### 5) Product backlog จัดลำดับ MoSCoW

| ID | User story (สรุป) | Epic | MoSCoW | เหตุผลลำดับ |
|---|---|---|---|---|
| US-012 | สแกนบาร์โค้ดเบิกสินค้า | เบิกสินค้า | **Must** | กระบวนการหลัก ขาดไม่ได้ |
| US-013 | ดูประวัติการเบิกย้อนหลัง | เบิกสินค้า | **Should** | ช่วยตรวจสอบ แต่เลื่อนได้ |
| US-021 | แจ้งเตือนสต็อกต่ำกว่าจุดสั่งซื้อ | สต็อก | **Should** | เพิ่มคุณค่า ไม่บล็อก go-live |
| US-030 | export รายงานเป็น Excel | รายงาน | **Could** | ทำมือชั่วคราวได้ |
| US-045 | แอปมือถือ offline | mobile | **Won't (รอบนี้)** | นอกขอบเขตเฟส 1 |

### 6) Assumptions / Constraints / Out-of-scope
- **Assumptions:** มี master data สินค้าครบ · ทุกสินค้ามีบาร์โค้ด
- **Constraints:** ต้องเชื่อม ERP เดิมผ่าน REST API · เป็นไปตาม PDPA
- **Out-of-scope (รอบนี้):** ระบบจัดซื้อ · การพยากรณ์ความต้องการ

## Checklist / Definition of Done

- [ ] ระบุ stakeholder ครบทุกกลุ่ม + วาง map (Power × Interest) แล้ว
- [ ] เลือกและใช้เทคนิค elicitation อย่างน้อย 2 แบบ
- [ ] มี Problem statement + business goal + KPI ที่ stakeholder เห็นตรงกัน
- [ ] มี as-is vs to-be ชัดเจน เห็น gap
- [ ] มี persona ผู้ใช้หลักครบ
- [ ] ทุก story เขียนรูปแบบ As a/I want/so that และผ่าน INVEST
- [ ] ทุก Must-have story มี acceptance criteria แบบ Given/When/Then ครอบ happy + edge + error
- [ ] backlog จัดลำดับ MoSCoW โดยผู้มีอำนาจตัดสินใจ commit แล้ว
- [ ] บันทึก assumptions / constraints / out-of-scope ครบ

## เคล็ดลับ & ข้อควรระวัง

- **แยก need ออกจาก solution** — ลูกค้ามักบอกวิธีแก้ ("อยากได้ปุ่ม X") ถามต่อ "ทำไม / เพื่ออะไร" (เทคนิค 5 Whys) จนเจอปัญหาจริง
- **อย่าถามนำ (leading question)** — "ระบบช้าใช่ไหมครับ" → ได้คำตอบ bias; ถามเปิด "ขั้นตอนนี้ใช้เวลาเท่าไหร่"
- **เก็บ verbatim** — จดคำพูดต้นฉบับก่อนตีความ จะ trace กลับได้เมื่อมีข้อโต้แย้ง
- **Won't ≠ ทิ้ง** — "Won't this time" แปลว่าเลื่อน ไม่ใช่ยกเลิก เก็บไว้ใน backlog รอบหน้า
- **ระวัง gold-plating** — อย่าใส่ฟีเจอร์ที่ไม่มี stakeholder คนไหนร้องขอ
- **Acceptance criteria คือสัญญา** — ถ้าเขียนไม่ได้ แปลว่า story ยังไม่ชัด (ละเมิด Testable ของ INVEST)
- **ปิดด้วยการ confirm** — ส่ง summary ให้ stakeholder ยืนยันเป็นลายลักษณ์อักษร กัน scope creep

## เชื่อมกับเฟสอื่น

- **ก่อนหน้า:** `/agile-delivery` — ตั้งกรอบ Agile/Scrum, role, cadence ของทีม
- **ถัดไป:** `/fr-nfr-spec` — แปลง user story/backlog เป็น Functional & Non-Functional Requirement ทางการ (SRS)
- **เกี่ยวข้อง:** `/business-logic-spec` (business rule ละเอียด) · `/solution-design` (สถาปัตยกรรม)
- **ภาพรวมทั้งวงจร:** `/sdlc-agile`
