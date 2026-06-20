---
name: fr-nfr-spec
description: เขียนสเปก requirement เป็นทางการระดับ SRS — Functional Requirements (FR) ที่มี ID ไม่ซ้ำ อะตอมมิก ทดสอบได้ + Non-functional Requirements (NFR) ทุกหมวด (performance, security, availability) ที่ "วัดผลได้" มี metric + target ชัดเจน. Write a formal Software Requirements Specification with uniquely-IDed FRs and measurable NFRs (p95 latency, uptime %, RTO/RPO). Trigger เมื่อผู้ใช้พิมพ์ /fr-nfr-spec หรือขอ "เขียน FR / NFR / SRS / functional spec / non-functional / requirement spec / สเปกระบบ".
category: sdlc
phase: "02 FR & NFR Spec"
---

# /fr-nfr-spec — สเปก Functional & Non-functional (SRS)

แปลงความต้องการดิบให้เป็น **SRS** ที่เป็นทางการ: Functional Requirements (FR) มี ID ไม่ซ้ำ อะตอมมิก ทดสอบได้ และ Non-functional Requirements (NFR) ทุกหมวดที่ "วัดผลได้จริง" (มี metric + target + วิธีวัด) — เขียนตามมาตรฐาน ISO/IEC/IEEE 29148:2018 (แทน IEEE 830 เดิม) เพื่อให้ส่งต่อ design / test ได้โดยไม่ต้องเดา

## ใช้ตอนไหน

- ผ่านเฟส discovery แล้ว (มี stakeholder, scope, raw requirement) และต้องการ "ตัวเอกสารทางการ" ที่ทีม dev/QA/architect อ้างอิงได้
- ลูกค้า/ผู้ตรวจรับ ขอ SRS / spec ที่ผูกกับสัญญา หรือต้องใช้ในการประมูล (TOR)
- ก่อนเริ่ม solution-design — design ต้องมี requirement ที่ "freeze + วัดผลได้" เป็น input
- จะตั้ง SLA/SLO หรือต้องตอบ compliance (PDPA/ISO 27001) — NFR ที่วัดได้คือหลักฐาน
- **ไม่ใช่** สำหรับ business rule/decision logic (→ `/business-logic-spec`) หรือการเก็บความต้องการดิบ/สัมภาษณ์ (→ `/req-discovery`)

## Input ที่ต้องถามก่อนเริ่ม

1. **Scope & boundary** — ระบบ/โมดูลไหน in-scope, out-of-scope อะไร, มี actor/role อะไรบ้าง
2. **แหล่ง requirement ดิบ** — output จาก `/req-discovery`, user stories, TOR, สัมภาษณ์ (ใช้เป็น `source` ของแต่ละ FR เพื่อ traceability)
3. **ภาระงาน/สเกลคาดหมาย** — concurrent users, requests/sec, ขนาดข้อมูล, peak vs avg (จำเป็นต่อ NFR performance/scalability — ถ้าไม่มีต้องสมมติแล้วระบุเป็น assumption)
4. **ข้อผูกพันธุรกิจ** — SLA ที่สัญญา, business hours, ต้นทุน downtime/นาที (ป้อน availability + RTO/RPO)
5. **บริบท compliance/security** — PII/PDPA, มาตรฐานที่ต้อง comply (ISO 27001, PCI-DSS), การ audit
6. **สภาพแวดล้อม/ข้อจำกัด** — on-prem/cloud, browser/OS ที่รองรับ, ระบบที่ต้อง integrate (ป้อน portability/compatibility)
7. **Priority scheme** — ใช้ MoSCoW (Must/Should/Could/Won't) หรือ Critical/High/Med/Low

> ถ้าข้อมูลไม่ครบ — อย่าหยุด. เขียน FR/NFR ตามที่มี แล้วทำเครื่องหมาย `[ASSUMPTION]` หรือ `[TBD]` ให้เห็นชัด พร้อมคำถามที่ต้องตามเก็บ

## ขั้นตอน (Playbook)

1. **กำหนด ID scheme + ลงทะเบียน** — FR ใช้ `FR-NNN` (เช่น FR-001), NFR ใช้ `NFR-<หมวด>-NN` (เช่น `NFR-PERF-01`). ID **ห้ามนำกลับมาใช้ซ้ำ** แม้ลบ requirement ทิ้ง (deprecate ไม่ลบเลข) เพื่อรักษา traceability
2. **สกัด Functional Requirements** — แตกความต้องการดิบเป็นข้อ **อะตอมมิก** (1 ข้อ = 1 ความสามารถที่ทดสอบได้). เขียนรูปแบบ "The system shall <action> <object> <condition>" / "ระบบต้อง<ทำอะไร><กับอะไร><เมื่อใด>". หลีกเลี่ยงคำกำกวม: ห้ามใช้ "เร็ว / ง่าย / รองรับเยอะ / ตามเหมาะสม / etc." โดยไม่มีเกณฑ์
3. **ตรวจคุณภาพ FR แต่ละข้อ (ตาม ISO/IEC/IEEE 29148 §5.2)** — ต้องผ่าน: *atomic* (แตกย่อยไม่ได้), *unambiguous* (ตีความได้ทางเดียว), *testable/verifiable* (มี acceptance criteria), *feasible*, *necessary*, *traceable* (ผูก source + AC). ถ้าข้อใดมี "และ/หรือ" ที่ทำให้ทดสอบแยกไม่ได้ → แตกเป็นหลายข้อ
4. **ดึง NFR ออกจาก FR และบริบท** — เดินทุกหมวด NFR (ตารางด้านล่าง) แล้วถามว่า "ระบบนี้มีข้อกำหนดด้านนี้ไหม วัดยังไง เป้าหมายเท่าไร". **ทุก NFR ต้องมี metric + target + วิธีวัด** มิฉะนั้นถือว่ายังไม่ใช่ requirement (เป็นแค่ความปรารถนา)
5. **ใส่ตัวเลขเป้าหมายที่อ้างอิงได้** — performance ผูกกับ workload, availability ผูกกับ business hours/ต้นทุน downtime. ถ้าตัวเลขมาจากการสมมติ ให้ระบุ basis (เช่น "อิงจาก peak 500 req/s ใน discovery")
6. **ทำ traceability** — แต่ละ FR/NFR ผูก `source` (ที่มา) ขึ้นข้างบน และ `AC ref / test ref` ลงข้างล่าง เตรียมส่ง `/test-strategy`
7. **ประกอบเป็น SRS + review** — รวมเป็นเอกสารตามโครงสารบัญด้านล่าง, ทำ requirement review กับ stakeholder, lock baseline + version

## NFR หมวดที่ต้องไล่ให้ครบ (แต่ละหมวดต้องมีตัวเลข)

| หมวด NFR | metric ที่ใช้บ่อย | ตัวอย่าง target จริง |
|---|---|---|
| Performance | latency p95/p99, throughput | API ตอบ p95 ≤ 300 ms, p99 ≤ 800 ms @ 500 req/s; รายงานสร้างเสร็จ ≤ 5 s |
| Scalability | concurrent users, scale-out | รองรับ 5,000 concurrent users; auto-scale ถึง 2× peak ภายใน 3 นาที |
| Availability/Reliability | uptime %, RTO, RPO, MTBF | uptime ≥ 99.9%/เดือน (≤ 43 นาที down); RTO ≤ 30 นาที, RPO ≤ 5 นาที |
| Security | auth, encryption, OWASP | TLS 1.2+ ทุก endpoint; PII เข้ารหัส AES-256 at rest; ผ่าน OWASP ASVS L2 |
| Usability | task success, เวลาเรียนรู้ | ผู้ใช้ใหม่ทำงานหลักสำเร็จ ≥ 90% ภายใน 5 นาทีโดยไม่ต้องอบรม; WCAG 2.1 AA |
| Maintainability | coverage, MTTR, complexity | unit test coverage ≥ 80%; MTTR ≤ 4 ชม.; cyclomatic ≤ 15/ฟังก์ชัน |
| Portability | OS/cloud/browser | รันได้ทั้ง AWS/on-prem (containerized); รองรับ Chrome/Edge/Safari 2 เวอร์ชันล่าสุด |
| Compatibility | integration, รูปแบบข้อมูล | integrate SAP ผ่าน REST/JSON; export CSV/XLSX ตาม schema ที่กำหนด |
| Compliance | มาตรฐาน, audit | สอดคล้อง PDPA (consent + สิทธิเจ้าของข้อมูล); audit log เก็บ ≥ 1 ปี; ISO 27001 controls |
| Observability | logging, metric, trace | structured log ทุก request (correlation-id); metric scrape ทุก 15 s; alert ภายใน ≤ 1 นาที |

## Output / Artifact (เทมเพลตพร้อมใช้)

### ตาราง Functional Requirements

| FR ID | ชื่อ | รายละเอียด (The system shall…) | Priority | Source | AC ref |
|---|---|---|---|---|---|
| FR-001 | ลงทะเบียนผู้ใช้ | ระบบต้องให้ผู้ใช้สมัครบัญชีด้วยอีเมล + รหัสผ่าน และส่งอีเมลยืนยันภายใน 60 วินาที | Must | US-12 | AC-001 |
| FR-002 | เข้าสู่ระบบ | ระบบต้องตรวจสอบ credential และล็อกบัญชีหลังกรอกผิด 5 ครั้งติดต่อกัน | Must | US-12 / PDPA | AC-002 |
| FR-003 | ค้นหาคำสั่งซื้อ | ระบบต้องค้นหาคำสั่งซื้อจากเลขที่ออเดอร์ ชื่อลูกค้า หรือช่วงวันที่ และคืนผลภายใน 2 วินาที | Should | TOR §4.2 | AC-007 |

*หมายเหตุ:* 1 แถว = 1 requirement อะตอมมิก. คอลัมน์ Source คือ traceability ขึ้น (ดิบ→FR), AC ref คือ traceability ลง (FR→test)

### ตาราง Non-functional Requirements

| NFR ID | หมวด | Requirement | Metric | Target | วิธีวัด/verify |
|---|---|---|---|---|---|
| NFR-PERF-01 | Performance | API หลักต้องตอบสนองเร็วภายใต้ภาระ peak | p95 / p99 latency | p95 ≤ 300 ms, p99 ≤ 800 ms @ 500 req/s | load test (k6) ที่ peak workload |
| NFR-AVL-01 | Availability | ระบบ production ต้องพร้อมใช้งานต่อเนื่อง | uptime / เดือน | ≥ 99.9% (≤ 43 นาที/เดือน) | uptime monitor + SLA report รายเดือน |
| NFR-AVL-02 | Reliability | กู้คืนจาก disaster ได้ตามเป้า | RTO / RPO | RTO ≤ 30 นาที, RPO ≤ 5 นาที | DR drill ทุกไตรมาส |
| NFR-SEC-01 | Security | ข้อมูล PII ต้องถูกเข้ารหัส | encryption | AES-256 at rest, TLS 1.2+ in transit | config audit + pentest |
| NFR-CMP-01 | Compliance | ระบบต้องสอดคล้อง PDPA | สิทธิเจ้าของข้อมูล | รองรับ consent + ขอลบ/เข้าถึงภายใน 30 วัน | compliance checklist + audit log |
| NFR-OBS-01 | Observability | ทุก request ต้อง trace ได้ | log coverage | 100% request มี correlation-id, alert ≤ 1 นาที | ตรวจ log + ทดสอบ alert |

### โครง SRS (สารบัญ — ISO/IEC/IEEE 29148)

```
1. บทนำ (Introduction)
   1.1 วัตถุประสงค์และขอบเขต (Purpose & Scope)
   1.2 นิยามศัพท์ ตัวย่อ (Definitions, Acronyms)
   1.3 เอกสารอ้างอิง (References)
   1.4 ภาพรวมระบบ (System Overview)
2. คำอธิบายโดยรวม (Overall Description)
   2.1 บริบทระบบ / context diagram
   2.2 Actors & roles
   2.3 ข้อสมมติและข้อจำกัด (Assumptions & Constraints)
3. Functional Requirements        ← ตาราง FR
4. Non-functional Requirements     ← ตาราง NFR (ทุกหมวด)
5. External Interfaces (UI / API / hardware / integration)
6. Data Requirements (entity, retention, ปริมาณ)
7. Traceability Matrix (source → FR/NFR → AC/test)
8. ภาคผนวก: open issues / TBD / glossary
```

## Checklist / Definition of Done

- [ ] ทุก FR มี ID ไม่ซ้ำ, อะตอมมิก, ทดสอบได้, ไม่กำกวม (ไม่มี "เร็ว/ง่าย/เยอะ" ลอย ๆ)
- [ ] ทุก FR มี Source (ขึ้น) และ AC ref (ลง) ครบ — traceable สองทาง
- [ ] เดิน NFR ครบทุกหมวดในตาราง (performance, scalability, availability, security, usability, maintainability, portability, compatibility, compliance, observability) — ที่ไม่ applicable ระบุ N/A พร้อมเหตุผล
- [ ] **ทุก NFR มี metric + target ที่เป็นตัวเลข + วิธีวัด** — ไม่มีข้อใดเป็นความปรารถนาลอย ๆ
- [ ] ตัวเลข performance/availability ผูกกับ workload และ business context จริง (ไม่ใช่ค่ามั่ว)
- [ ] Priority ครบทุกข้อ (scheme เดียวกันทั้งเอกสาร)
- [ ] business rule/decision logic ไม่หลุดมาปนใน FR (ส่งต่อ `/business-logic-spec`)
- [ ] มี baseline version + วันที่ + ผู้อนุมัติ; รายการ TBD/assumption แยกชัด

## เคล็ดลับ & ข้อควรระวัง

- **กับดักคำกำกวม:** "ระบบต้องเร็ว" ทดสอบไม่ได้ → "p95 ≤ 300 ms @ 500 req/s". "รองรับผู้ใช้จำนวนมาก" → "5,000 concurrent users". ทุกคำคุณศัพท์ต้องแปลงเป็นตัวเลข
- **อย่ายัด design ลง requirement:** FR บอก "อะไร" (what) ไม่ใช่ "อย่างไร" (how). "ใช้ Redis cache" เป็น design → เก็บไว้ที่ `/solution-design`. เขียนแค่เป้า latency
- **NFR latency ต้องระบุ percentile:** average หลอกตา — เขียน p95/p99 เสมอ และผูกกับ load level (ไม่งั้น target ไม่มีความหมาย)
- **availability ต้องมาคู่ RTO/RPO:** uptime % ตอบ "ล่มบ่อยแค่ไหน", RTO/RPO ตอบ "ล่มแล้วกู้เร็วแค่ไหน / เสียข้อมูลแค่ไหน" — คนละเรื่อง ต้องมีทั้งคู่
- **ID เป็นสัญญา:** เมื่อ publish แล้วห้ามเปลี่ยนความหมายของ ID เดิม. requirement ที่เลิกใช้ให้ mark *Deprecated* ไม่ลบเลข
- **แยก FR atomic จริง ๆ:** "ระบบต้อง login และส่งอีเมลแจ้งเตือน" = 2 FR. ถ้าทดสอบ 2 อย่างแยกกัน → แยกข้อ
- **Compliance ไม่ใช่แค่ติ๊ก:** PDPA/ISO ต้องแปลงเป็น NFR ที่วัดได้ (เก็บ log กี่ปี, ลบข้อมูลภายในกี่วัน) ไม่ใช่เขียนว่า "ต้อง comply PDPA" เฉย ๆ
- อ้างมาตรฐานในเอกสาร (ISO/IEC/IEEE 29148:2018 หรือ IEEE 830 รุ่นเก่า) เพื่อให้ผู้ตรวจรับเชื่อถือ

## เชื่อมกับเฟสอื่น

- **ก่อนหน้า:** `/req-discovery` — เก็บความต้องการดิบ/สัมภาษณ์/scope (เป็น `source` ของ FR/NFR ที่นี่)
- **ถัดไป:** `/business-logic-spec` — แปลง business rule/decision logic ที่อ้างใน FR เป็นกฎเชิงตรรกะละเอียด
- **ป้อนต่อ:** `/solution-design` (NFR เป็น input ของสถาปัตยกรรม), `/test-strategy` + `/regression-suite` (FR/NFR → test case ผ่าน AC ref), `/observability` (รับ NFR-OBS ไปทำจริง), `/authn-authz-design` (รับ NFR-SEC)
- **ภาพรวมทั้งวงจร:** `/sdlc-agile`
