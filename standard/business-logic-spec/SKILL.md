---
name: business-logic-spec
description: ระบุ business logic/business rules ให้ชัดและทดสอบได้ — decision table, state machine, กฎคำนวณ/ตรวจสอบ, edge case — เพื่อให้ dev เขียนตรรกะถูกต้องและตรงเจตนาธุรกิจ (turn fuzzy domain rules into precise, testable specs). Trigger เมื่อผู้ใช้พิมพ์ /business-logic-spec หรือขอ "business logic / business rule / decision table / state machine / กฎทางธุรกิจ / ตรรกะระบบ / workflow rule".
category: sdlc
phase: "03 Business Logic"
---

# /business-logic-spec — ระบุตรรกะและกฎทางธุรกิจ (Business Logic & Rules)

แปลง "กฎทางธุรกิจที่อยู่ในหัวคน" ให้เป็น spec ที่ชัด ทดสอบได้ และไม่กำกวม — ผ่าน business rules catalog, decision table, state machine และกฎคำนวณ/ตรวจสอบ — เพื่อให้ dev เขียนตรรกะถูกต้องตั้งแต่รอบแรก และ tester เขียน test case ได้ตรงกฎ

## ใช้ตอนไหน

- หลังจากมี FR/NFR แล้ว (`/fr-nfr-spec`) แต่ FR บอกแค่ "ระบบต้องคิดส่วนลด" โดยไม่บอก "คิดยังไง กี่ขั้น เงื่อนไขไหนชนะ"
- เมื่อตรรกะมีหลายเงื่อนไขซ้อนกัน (if-else ลึกหลายชั้น) จนอธิบายเป็นร้อยแก้วแล้วเริ่มขัดแย้งกันเอง → ใช้ **decision table**
- เมื่อ entity มี "สถานะ" และเปลี่ยนสถานะตาม event (เช่น คำสั่งซื้อ, คำขอลา, ใบกำกับภาษี) → ใช้ **state machine**
- เมื่อมีกฎคำนวณเงิน/ภาษี/ดอกเบี้ย/ส่วนลด ที่การปัดเศษหรือลำดับการคำนวณมีผลต่อผลลัพธ์
- ใช้ก่อนเข้า `/solution-design` เพื่อให้สถาปนิกออกแบบโครงสร้างจากตรรกะที่นิ่งแล้ว ไม่ใช่เดาเอง

> ขอบเขตเฉพาะเฟสนี้ = "ตรรกะและกฎ" เท่านั้น
> - สถาปัตยกรรม / data model / API design → `/solution-design`
> - สิทธิ์ตามบทบาท / การแยกหน้าที่ (maker-checker เชิงสิทธิ์) → `/sod-matrix`
> - การยืนยันตัวตน / authorization เชิงเทคนิค → `/authn-authz-design`
> เฟสนี้พูดถึง maker-checker ได้แค่ "ระดับ logic ของ flow" (ใครทำสเต็ปไหน สถานะเปลี่ยนยังไง) ไม่ลงลึกว่า role ไหนมีสิทธิ์อะไร

## Input ที่ต้องถามก่อนเริ่ม

1. **FR อ้างอิง** — เฟสนี้ขยายความ FR ตัวไหน (ขอ FR-ID จาก `/fr-nfr-spec`)
2. **โดเมน/กฎดิบ** — กฎทางธุรกิจในรูปแบบที่ลูกค้าพูด (นโยบายส่วนลด, เกณฑ์อนุมัติ, เงื่อนไขคิดเงิน) พร้อม "ใครเป็นเจ้าของกฎ" (rule owner)
3. **entity ที่มีวงจรชีวิต** — มี object ไหนที่มีสถานะและเปลี่ยนได้บ้าง (order, ticket, loan, invoice)
4. **หน่วย/ความแม่นยำ** — สกุลเงิน, จำนวนทศนิยม, วิธีปัดเศษ (ปัดขึ้น/ลง/banker's), เขตเวลาอ้างอิง, ปฏิทิน (วันทำการ?)
5. **ลำดับความสำคัญของกฎ** — ถ้ากฎหลายตัวชนกัน อันไหนชนะ (precedence / specificity)
6. **แหล่งความจริง** — ค่าคงที่/เกณฑ์ (threshold) มาจาก config, ตารางในระบบ หรือ hardcode

## ขั้นตอน (Playbook)

1. **รวบรวมกฎดิบ → จัดหมวด** — ดึงทุกกฎจากเอกสาร/สัมภาษณ์ แล้วระบุประเภทแต่ละกฎ:
   - `constraint` — ข้อจำกัดที่ต้องเป็นจริงเสมอ (เช่น ยอดสั่งซื้อ > 0)
   - `validation` — กฎตรวจความถูกต้องของ input (รูปแบบ, ช่วงค่า)
   - `computation` — สูตรคำนวณ (ส่วนลด, ภาษี, ค่าธรรมเนียม)
   - `derivation` — ค่าที่อนุมานจากค่าอื่น (เกรดลูกค้าจากยอดสะสม)
   - `process` — กฎควบคุม flow/ลำดับขั้น (ต้องอนุมัติก่อนจ่าย)
2. **ให้ ID และเขียนลง catalog** — ทุกกฎได้ `BR-xxx` พร้อมผูกกลับ FR-ID (traceability)
3. **ตรรกะหลายเงื่อนไข → decision table** — แตกเป็น condition × action, ใส่ทุก combination แล้วตรวจ completeness (ครบทุกกรณี) และ consistency (ไม่มี 2 แถวขัดกัน)
4. **entity มีสถานะ → state machine** — วาดตาราง transition (state/event/next/guard/action) และระบุ state เริ่มต้น/สิ้นสุด + transition ที่ "ห้ามเกิด"
5. **กฎคำนวณ → ระบุสูตร + ลำดับ + การปัดเศษ** ให้ครบจน reproduce ได้ พร้อมตัวอย่างตัวเลขจริง (worked example)
6. **ล่า edge case** — ค่า null/ว่าง, ขอบเขต (0, ค่าติดลบ, ค่าสูงสุด), การหารด้วยศูนย์, วันคาบเกี่ยว, สกุลเงินหลายตัว, การทำซ้ำ (idempotency), การยกเลิก/ย้อนกลับ
7. **ตรวจ traceability ย้อนกลับ** — ทุก BR ต้องโยงไป FR; ทุก FR ที่มีตรรกะต้องมี BR รองรับ
8. **ส่งต่อ** — สรุป assumption ที่ตั้งไว้ + คำถามค้างให้ rule owner ยืนยัน ก่อนส่งเข้า `/solution-design`

## Output / Artifact (เทมเพลตพร้อมใช้)

### 1) Business Rule Catalog (รูปแบบ entry แต่ละกฎ)

```
BR-012  ส่วนลดตามยอดสั่งซื้อ (Volume discount)
ประเภท (type)   : computation
เจ้าของกฎ        : ฝ่ายขาย (Sales policy 2026)
อ้างอิง FR        : FR-031 (คำนวณราคาสุทธิตะกร้าสินค้า)
เงื่อนไข (when)   : ลูกค้ายืนยันตะกร้า และ subtotal ≥ 1,000 THB
ผลลัพธ์ (then)    : ใช้ส่วนลดตาม decision table DT-01 (ดูด้านล่าง)
                  ส่วนลดสูงสุดไม่เกิน 20% ของ subtotal
หน่วย/ปัดเศษ      : THB, ปัดเศษทศนิยม 2 ตำแหน่งแบบ half-up หลังคำนวณส่วนลด
ความสำคัญ (prec.) : ใช้คู่กับ BR-013 (คูปอง) — ส่วนลดยอดคิดก่อน แล้วจึงหักคูปอง
ตัวอย่าง          : subtotal 1,500 → tier 5% → ส่วนลด 75.00 → net 1,425.00
```

### 2) Decision Table — DT-01: ส่วนลดตามยอดสั่งซื้อ + ประเภทสมาชิก

อ่านแบบ "เงื่อนไขด้านบน, การกระทำด้านล่าง"; แต่ละคอลัมน์ R1..R5 คือ 1 กฎ (rule). `-` = ไม่สนใจ (don't care)

| เงื่อนไข (Condition)        | R1     | R2        | R3        | R4        | R5      |
|----------------------------|--------|-----------|-----------|-----------|---------|
| subtotal (THB)             | < 1000 | 1000–4999 | 1000–4999 | ≥ 5000    | ≥ 5000  |
| ระดับสมาชิก (tier)         | -      | ทั่วไป     | VIP       | ทั่วไป     | VIP     |
| **การกระทำ (Action)**      |        |           |           |           |         |
| % ส่วนลด                    | 0%     | 5%        | 8%        | 10%       | 15%     |
| ส่งฟรี (free shipping)      | ไม่     | ไม่        | ใช่        | ใช่        | ใช่     |
| ต้องอนุมัติเพิ่ม            | ไม่     | ไม่        | ไม่        | ไม่        | ใช่*    |

\* R5: ถ้า %ส่วนลดรวมทั้งบิล > 20% หลังรวมคูปอง ต้องให้หัวหน้าฝ่ายขายอนุมัติ (ดู state machine ด้านล่าง)

ตรวจคุณภาพตาราง: **completeness** = ทุกช่วง subtotin × tier มีกฎรองรับ (รวม < 1000); **consistency** = ไม่มีแถวซ้อนทับให้ผลต่างกัน; **edge** = subtotal = 1000 และ = 5000 ตกอยู่กฎใด (ระบุชัดว่าใช้ ≥)

### 3) State Machine / Lifecycle — ตัวอย่าง: คำขออนุมัติเครดิตลูกค้า (Credit approval)

สถานะเริ่มต้น: `DRAFT` · สถานะสิ้นสุด: `ACTIVE`, `REJECTED`, `CANCELLED`

| State (สถานะ)   | Event (เหตุการณ์) | Next state (ถัดไป) | Guard (เงื่อนไขผ่าน)                       | Action (การกระทำ)                 |
|-----------------|-------------------|--------------------|--------------------------------------------|------------------------------------|
| DRAFT           | submit            | UNDER_REVIEW       | ข้อมูลครบตาม BR-020..023                    | สร้างเลขคำขอ, แจ้งผู้ตรวจ           |
| DRAFT           | cancel            | CANCELLED          | —                                          | บันทึกเหตุผลยกเลิก                   |
| UNDER_REVIEW    | approve           | ACTIVE             | วงเงิน ≤ อำนาจอนุมัติผู้ตรวจ (BR-030)        | เปิดวงเงิน, แจ้งลูกค้า               |
| UNDER_REVIEW    | escalate          | PENDING_MANAGER    | วงเงิน > อำนาจผู้ตรวจ                        | ส่งต่อผู้จัดการ                      |
| UNDER_REVIEW    | reject            | REJECTED           | —                                          | บันทึกเหตุผล, แจ้งลูกค้า             |
| PENDING_MANAGER | approve           | ACTIVE             | ผู้จัดการอนุมัติ และวงเงิน ≤ เพดานบริษัท     | เปิดวงเงิน                          |
| PENDING_MANAGER | reject            | REJECTED           | —                                          | บันทึกเหตุผล                        |

Transition ที่ห้ามเกิด (ระบุชัดเพื่อกัน bug): `REJECTED → ACTIVE`, `ACTIVE → DRAFT`, `CANCELLED → *` (terminal). การ approve ตัวเอง (maker = checker) ห้าม — *กฎสิทธิ์เชิงบทบาทอยู่ที่ `/sod-matrix`*

### 4) กฎคำนวณ/ตรวจสอบ (Computation & Validation rules)

```
BR-021 validation : tax_id ต้องเป็นตัวเลข 13 หลัก และผ่าน checksum; ว่าง = reject
BR-030 computation: ลำดับคำนวณราคาสุทธิ
  1. subtotal = Σ(qty × unit_price)            // ก่อนส่วนลด
  2. volume_discount = subtotal × tier% (DT-01) // ปัด half-up 2 ตำแหน่ง
  3. after_discount = subtotal − volume_discount
  4. coupon = min(coupon_value, after_discount) // คูปองไม่ทำให้ติดลบ
  5. vat = (after_discount − coupon) × 7%        // VAT คิดหลังหักทุกส่วนลด
  6. grand_total = after_discount − coupon + vat // ปัด half-up 2 ตำแหน่ง
  เขตเวลา: ใช้ Asia/Bangkok สำหรับวันมีผลของโปรโมชัน
```

### 5) Edge cases & exception handling (ตาราง)

| กรณีขอบ (Edge case)              | กฎที่ใช้จัดการ          | ผลลัพธ์ที่คาด                         |
|----------------------------------|------------------------|---------------------------------------|
| subtotal = 0 / ตะกร้าว่าง         | BR-012 guard           | ไม่คิดส่วนลด, บล็อกการชำระเงิน          |
| คูปอง > ยอดหลังส่วนลด             | BR-030 ขั้น 4          | หักได้ไม่เกินยอด, ไม่ติดลบ              |
| วงเงินเกินเพดานบริษัท             | state guard            | คงสถานะ PENDING_MANAGER, ไม่อนุมัติเอง |
| ส่งคำขอซ้ำ (double submit)        | idempotency key        | คืนผลเดิม ไม่สร้างคำขอใหม่              |

## Checklist / Definition of Done

- [ ] ทุก business rule มี `BR-ID`, ประเภท (constraint/validation/computation/derivation/process) และเจ้าของกฎ
- [ ] ทุก BR ผูกกลับ `FR-ID` (traceability สองทาง — ไม่มี BR ลอย, ไม่มี FR ตรรกะที่ขาด BR)
- [ ] ตรรกะหลายเงื่อนไขทุกชุดมี decision table ที่ผ่าน completeness + consistency
- [ ] ทุก entity ที่มีสถานะมี state machine ครบ: state เริ่ม/จบ, guard, action, และ transition ต้องห้าม
- [ ] กฎคำนวณระบุสูตร + ลำดับ + การปัดเศษ + หน่วย/สกุลเงิน/เขตเวลา และมี worked example ตัวเลขจริง
- [ ] edge case สำคัญถูกระบุพร้อมพฤติกรรมที่คาด (null, ขอบเขต, หารศูนย์, ซ้ำ, ยกเลิก/ย้อน)
- [ ] precedence ของกฎที่ชนกันถูกระบุชัด
- [ ] assumption และคำถามค้างถูกบันทึก และ rule owner ยืนยันแล้ว

## เคล็ดลับ & ข้อควรระวัง

- **อย่าฝังกฎเป็นร้อยแก้ว** — ถ้าเขียนเกิน 2-3 if ในประโยคเดียว ให้ย้ายเป็น decision table ทันที จะเห็นช่องโหว่เอง
- **completeness > ความสวย** — เติมทุก combination แม้กรณี "เป็นไปไม่ได้" แล้ว mark ว่า impossible/error ดีกว่าปล่อยช่องว่างให้ dev เดา
- **แยก "ค่าคงที่" ออกจากตรรกะ** — threshold/เปอร์เซ็นต์ควรชี้ไป config/ตาราง ไม่ hardcode ใน spec; ระบุแหล่งความจริง
- **การปัดเศษคือ bug ยอดฮิต** — ระบุ "ปัดเมื่อไหร่ (แต่ละขั้นหรือขั้นสุดท้าย)" และ "วิธีปัด" ให้ตรงกับฝ่ายบัญชี/กฎหมาย
- **state machine ต้องมี transition ต้องห้าม** — การไม่ระบุ "ห้ามจาก X ไป Y" คือต้นเหตุของ state corruption
- **เขตเวลา/วันทำการ** — โปรโมชัน, ดอกเบี้ย, SLA มักผิดเพราะ timezone หรือไม่นับวันหยุด ระบุปฏิทินอ้างอิงเสมอ
- **อย่าปนเรื่องสิทธิ์** — "ใครได้รับอนุญาตให้อนุมัติ" ไม่ใช่ business logic เฟสนี้ ส่งไป `/sod-matrix` / `/authn-authz-design`

## เชื่อมกับเฟสอื่น

- **ก่อนหน้า:** `/fr-nfr-spec` — FR บอก "ระบบต้องทำอะไร" เฟสนี้ลงลึก "ทำตามตรรกะ/กฎอะไรเป๊ะ ๆ"
- **ถัดไป:** `/solution-design` — สถาปนิกรับ rule catalog + decision table + state machine ไปออกแบบโครงสร้าง/data model/API
- **เกี่ยวข้อง:** `/sod-matrix` และ `/authn-authz-design` (สิทธิ์/อนุมัติเชิงบทบาท), `/test-strategy` (แปลง decision table/state machine เป็น test case), `/threat-model` (ตรวจ business-logic abuse)
- **ภาพรวมทั้งวงจร:** `/sdlc-agile`
