---
name: test-strategy
description: วางกลยุทธ์และแผนการทดสอบ — test pyramid (unit/integration/e2e), test type/level, coverage target, test data, entry/exit criteria, และเทคนิคออกแบบ test case (boundary value, decision table) ระดับ test lead / QA strategy & test planning aligned to ISO/IEC/IEEE 29119. Trigger เมื่อผู้ใช้พิมพ์ /test-strategy หรือขอ "test plan / test strategy / unit test / integration test / e2e / UAT / test case / แผนทดสอบ / coverage".
category: sdlc
phase: "09 Test Strategy"
---

# /test-strategy — กลยุทธ์และแผนการทดสอบ (Test Strategy & Plan)

ออกแบบ "ทดสอบอะไร ที่ระดับไหน ด้วยเทคนิคใด แค่ไหนถึงพอ" ให้เป็นเอกสารที่ทีมใช้จริง — แยก **Test Strategy** (หลักการระดับองค์กร/โปรเจกต์ คงทน) ออกจาก **Test Plan** (รายละเอียดเฉพาะ release/feature) ตามแนว ISO/IEC/IEEE 29119 และวางโครง test case ที่ออกแบบจากเทคนิคจริง ไม่ใช่เดาเคสตามอารมณ์

## ใช้ตอนไหน
- เริ่ม feature/epic/release ใหม่ แล้วต้องตอบ "จะทดสอบยังไงให้ปล่อยได้อย่างมั่นใจ"
- ทีมเขียนเทสมั่ว — e2e เยอะเกิน (ช้า/เปราะ), unit น้อย, ไม่มี contract test ระหว่าง service
- ต้องตกลง coverage target / entry-exit criteria / DoD กับ stakeholder หรือ audit
- เตรียม UAT กับ business user หรือต้องวาง test data/environment ให้ทำซ้ำได้
- **ไม่ใช่ตอนนี้:** regression suite ที่รันต่อเนื่อง → `/regression-suite`; security testing → `/security-testing`; pen test → `/pentest-plan`; ตัวเลข NFR (เช่น p95 latency, throughput) กำหนดที่ `/fr-nfr-spec` แล้ว performance test แยกเฟส

## Input ที่ต้องถามก่อนเริ่ม
1. **ขอบเขต & ความเสี่ยง** — feature/release ไหน, ส่วนไหน critical (payment, auth, data integrity) ต้องเทสหนัก? ใช้ risk-based testing จัดลำดับ
2. **สถาปัตยกรรม** — monolith / microservices / มี external API? (กำหนดว่าต้องมี contract test ไหม)
3. **Spec อ้างอิง** — FR/NFR (`/fr-nfr-spec`), business logic (`/business-logic-spec`), acceptance criteria
4. **Stack & เครื่องมือ** — ภาษา/framework เทส (Jest/Vitest/JUnit/pytest, Playwright/Cypress), CI ที่มี
5. **Test data & environment** — มี staging ไหม, ข้อมูล PII ใช้ได้แค่ไหน, seed/mask อย่างไร
6. **Constraint** — timeline, regulatory (PDPA/ISO), ใครเป็นคน sign-off UAT
7. **Definition of Done เดิม** ของทีม (ถ้ามี) เพื่อไม่ขัดกัน

## ขั้นตอน (Playbook)
1. **Risk assessment** — list feature × (impact ถ้าพัง × โอกาสพัง) → จัดเป็น High/Med/Low กำหนดความเข้มของเทสตามความเสี่ยง ไม่เทสทุกอย่างเท่ากัน
2. **เลือก test level ตาม pyramid** — แมปแต่ละความเสี่ยงไปยังระดับที่ "ถูกและเร็วที่สุดที่ครอบได้": logic → unit; ขอบเขต module/DB → integration; สัญญา API ระหว่างทีม → contract; flow ผู้ใช้สำคัญ → e2e
3. **เลือกเทคนิคออกแบบ test case** ต่อจุดทดสอบ — equivalence partitioning + boundary value (input ที่มีช่วง), decision table (กฎหลายเงื่อนไข AND/OR), state transition (workflow/สถานะ เช่น order: draft→paid→shipped)
4. **กำหนด coverage target** — line/branch ต่อ layer (เช่น domain logic ≥80% branch, glue code ต่ำกว่าได้) + ระบุข้อจำกัด coverage (สูง ≠ ถูกต้อง — วัด "รันถึง" ไม่ใช่ "assert ถูก")
5. **วาง test data & environment** — แหล่งข้อมูล (factory/fixture/masked prod), การ reset state, environment matrix (browser/OS/device ถ้าจำเป็น)
6. **นิยาม entry/exit criteria + defect workflow** — เมื่อไรเริ่มเทสได้, เมื่อไรปิด phase ได้, severity vs priority, เกณฑ์ block release
7. **เขียน test case จริง** จากเทคนิคในข้อ 3 ลงเทมเพลตด้านล่าง พร้อม trace กลับไป requirement (req ref)
8. **วางแผน UAT** — business scenario ภาษาธุรกิจ, ผู้ sign-off, environment, เกณฑ์ผ่าน
9. **ผูกเข้า CI & ส่งต่อ** — ระบุว่าชุดไหนรันทุก commit / ทุก PR / nightly, แล้วส่งของ regression ต่อ `/regression-suite`

## Output / Artifact (เทมเพลตพร้อมใช้)

### A. โครง Test Plan (สารบัญ — อิง IEEE 829 / ISO 29119 test plan)
```
1. บทนำ & ขอบเขต (in-scope / out-of-scope)
2. เอกสารอ้างอิง (FR/NFR, business spec, design)
3. กลยุทธ์ทดสอบ (test pyramid + เหตุผลสัดส่วน)
4. Test items & features to be tested / not tested
5. Test levels & types (ตารางในข้อ B)
6. เทคนิคออกแบบ test case ที่ใช้
7. Coverage target ต่อ layer + ข้อจำกัด
8. Test data & test environment (matrix)
9. Entry / Exit criteria (ตารางในข้อ E)
10. Defect lifecycle, severity & priority
11. Roles, schedule, sign-off (รวม UAT)
12. ความเสี่ยง & แผนสำรอง (risk-based prioritization)
```

### B. Test Pyramid & สัดส่วนเป้าหมาย (ปรับตามความเสี่ยง)
```
        ╱ e2e ╲          ~10%  flow ผู้ใช้ critical, ข้ามระบบจริง  (ช้า/เปราะ — ใช้น้อยแต่คุ้ม)
      ╱ contract ╲       ~10%  สัญญา API ระหว่าง service/ทีม (consumer-driven)
    ╱ integration ╲      ~20%  module + DB/queue/external (mock ขอบนอก)
  ╱      unit       ╲    ~60%  logic ล้วน เร็ว deterministic รันทุก save
```
เหตุผล: ยิ่งสูง ยิ่งช้า/แพง/เปราะ/ debug ยาก → ดันการตรวจ logic ลงล่างสุด เก็บ e2e ไว้พิสูจน์ "ระบบจริงต่อกันได้" เท่านั้น (anti-pattern: ice-cream cone = e2e เยอะ unit น้อย)

### C. Test level & type (ทำเครื่องหมายที่ใช้)
| Type | ระดับ | ทดสอบอะไร | เครื่องมือตัวอย่าง |
|------|-------|-----------|-------------------|
| Unit | component | function/class logic, branch | Jest/Vitest/JUnit/pytest |
| Integration | module | module↔DB/queue/3rd-party | Testcontainers, supertest |
| Contract | interface | schema/สัญญา API ระหว่างทีม | Pact, OpenAPI validation |
| System / E2E | system | user flow ข้ามระบบจริง | Playwright, Cypress |
| Smoke | system | build ใช้งานได้ขั้นต่ำไหม (เร็ว) | subset e2e |
| Sanity | system | จุดที่เพิ่งแก้ทำงานหรือไม่ | targeted manual/auto |
| UAT | acceptance | ตรงความต้องการธุรกิจจริง | business user + scenario |
| Exploratory | system | หาเคสที่ test case ตายตัวไม่เจอ | session-based, charter |
| Accessibility | system/UI | WCAG, keyboard, screen reader | axe-core, Lighthouse |
> Performance/load, security, pen test → ดู `/fr-nfr-spec`, `/security-testing`, `/pentest-plan`

### D. เทมเพลต Test Case (ลงตารางหรือ tool)
| Field | ตัวอย่าง |
|-------|----------|
| Test Case ID | TC-LOGIN-007 |
| Requirement Ref | FR-AUTH-03 |
| Title | ล็อกอินด้วยรหัสผ่านผิดเกิน 5 ครั้งต้องถูกล็อก |
| Priority | High |
| Precondition | มี user active; ระบบ lockout threshold = 5 |
| Test Data | user=test@x.com, wrong_pw ×5 |
| Steps | 1) กรอกรหัสผิด 5 ครั้งติด 2) กรอกครั้งที่ 6 |
| Expected Result | ครั้งที่ 6 ขึ้น "บัญชีถูกล็อก" + ไม่ออก token |
| Type / Level | Functional / Integration |
| Status | Pass / Fail / Blocked |

### E. Entry / Exit Criteria
| | Entry (เริ่ม phase ได้เมื่อ) | Exit (ปิด phase ได้เมื่อ) |
|--|------------------------------|---------------------------|
| System/Integration | build deploy ลง test env ได้, smoke ผ่าน, test data พร้อม | test case วางแผนรัน ≥95%, ไม่มี Critical/High เปิดค้าง, coverage ถึง target |
| UAT | system test exit ผ่าน, ข้อมูล UAT พร้อม, user มี | acceptance scenario ผ่านครบ, business sign-off เป็นลายลักษณ์ |

### F. ตัวอย่าง Boundary Value Analysis
อายุที่รับสมัคร: ถูกต้อง **18–60** (รวมปลายทั้งสอง)
```
Partition:  | invalid |   valid    | invalid |
            17 |  18  ...  60  | 61
ทดสอบ BVA:  17, 18, 19   ...   59, 60, 61   (+ค่า off เช่น 0, -1, 999, ไม่ใช่ตัวเลข)
```
จับ off-by-one (`<` vs `<=`) ซึ่งเป็นบั๊กขอบที่พบบ่อยสุด — ทดสอบ "ค่าตรงขอบ" ไม่ใช่แค่กลางช่วง

### G. ตัวอย่าง Decision Table (ส่วนลด)
| เงื่อนไข | R1 | R2 | R3 | R4 |
|----------|----|----|----|----|
| เป็นสมาชิก | Y | Y | N | N |
| ยอดซื้อ ≥ 1,000 | Y | N | Y | N |
| **ผลลัพธ์: ส่วนลด** | 15% | 5% | 10% | 0% |

> ทุก rule = 1 test case อย่างน้อย → ครบทุก combination เงื่อนไข ไม่ตกเคสที่เกิดจากการ AND/OR หลายตัว

## Checklist / Definition of Done
- [ ] แยก Test Strategy (คงทน) ออกจาก Test Plan (เฉพาะ release) ชัดเจน
- [ ] ทุก requirement สำคัญมี test case map กลับได้ (traceability)
- [ ] สัดส่วน pyramid สมเหตุผล — ไม่ใช่ ice-cream cone
- [ ] เลือกเทคนิคออกแบบเคส (EP/BVA/decision/state) ตรงกับชนิด input ไม่ใช่เดา
- [ ] coverage target ต่อ layer ระบุชัด + เขียนข้อจำกัด coverage กำกับ
- [ ] test data & environment ทำซ้ำได้ (reset/seed/mask), PII ปลอดภัย
- [ ] entry/exit criteria + severity/priority + เกณฑ์ block release ตกลงกับ stakeholder
- [ ] มีแผน UAT พร้อมผู้ sign-off
- [ ] ระบุชุดที่รัน per-commit / per-PR / nightly และส่งต่อ `/regression-suite`

## เคล็ดลับ & ข้อควรระวัง
- **Coverage เป็น proxy ไม่ใช่เป้า** — 100% line cov ที่ไม่มี assert จริง = หลอกตัวเอง; วัด mutation testing ถ้าจริงจังเรื่องคุณภาพเทส
- **อย่าเทสซ้ำชั้น** — ถ้า unit ครอบ logic แล้ว ไม่ต้องดัน e2e ไปไล่ทุกสาขา (แพง+ช้า); e2e ตรวจ "ต่อกันได้" พอ
- **Contract test คือยาแก้ integration เปราะ** ใน microservices — consumer-driven (Pact) จับ breaking change ก่อน deploy โดยไม่ต้อง spin ทั้งระบบ
- **Severity ≠ Priority** — UI typo บนหน้า landing อาจ severity ต่ำแต่ priority สูง (CEO เห็น); แยกสองแกนเสมอ
- **Flaky test แย่กว่าไม่มีเทส** — ทำให้ทีมเลิกเชื่อ CI; quarantine + fix แทนปล่อย retry
- **Exploratory ไม่ใช่ "เทสมั่ว"** — ใช้ charter + session-based test management จับเคสที่ scripted ตกหล่น
- **อ้างมาตรฐานเท่าที่ใช้จริง** — ISO/IEC/IEEE 29119 (กระบวนการ/เอกสารทดสอบ ยุคใหม่ แทน IEEE 829 เดิม) เป็นโครงอ้างอิง ไม่ต้องทำครบทุก template ถ้า overkill กับขนาดทีม

## เชื่อมกับเฟสอื่น
- **ก่อนหน้า:** `/dev-standards` — มาตรฐานโค้ด/รีวิว (กำหนดว่าเทสต้องผ่านก่อน merge)
- **ถัดไป:** `/regression-suite` — เปลี่ยน test case เป็นชุด regression ที่รันต่อเนื่อง
- **ภาพรวมทั้งวงจร:** `/sdlc-agile`
- **เกี่ยวข้อง:** `/fr-nfr-spec` (ที่มาของ acceptance/NFR targets), `/business-logic-spec` (กฎที่ต้องเทส), `/security-testing` & `/pentest-plan` (มิติความปลอดภัย), `/solution-design` (จุดต่อระหว่าง service → contract test)
