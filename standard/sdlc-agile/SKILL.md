---
name: sdlc-agile
description: ตัวขับเคลื่อนการพัฒนาซอฟต์แวร์ครบวงจรแบบ SDLC + Agile ตั้งแต่เก็บ requirement, FR/NFR, business logic, design/architecture, authentication & authorization, Segregation of Duties (SoD), threat model, dev, test, regression/non-regression, security test, pen test, deployment, ไปจนถึง monitoring & observability — จัดเป็นเฟส มี quality gate และ artifact ทุกเฟส แล้ว delegate ไปยัง sub-skill รายเฟส. Trigger เมื่อผู้ใช้พิมพ์ /sdlc-agile หรือขอ "เริ่มโปรเจกต์ซอฟต์แวร์ใหม่ / วาง process พัฒนา / ทำ SDLC / เก็บ requirement ไปจนถึง deploy / กระบวนการ Agile / software lifecycle".
category: sdlc
phase: "00 Orchestrator"
---

# /sdlc-agile — ตัวขับเคลื่อนวงจรพัฒนาซอฟต์แวร์ (SDLC + Agile Orchestrator)

สกิลนี้เป็น **ตัวกลาง (orchestrator)** ที่พาทำงานพัฒนาซอฟต์แวร์ตั้งแต่ต้นจนจบ — เก็บ requirement → ออกแบบ → พัฒนา → ทดสอบ → ปล่อย → เฝ้าระวัง — โดยทำให้ทุกเฟสมี **artifact ที่ส่งมอบได้จริง**, มี **quality gate** คั่นระหว่างเฟส, และ **traceability** ที่ลากเส้นจาก requirement → design → code → test → release ได้ครบ. รายละเอียดเชิงลึกของแต่ละเฟสอยู่ใน sub-skill ที่ระบุไว้ในตารางด้านล่าง

> ปรัชญา: **"ไม่มี artifact = เฟสนั้นยังไม่จบ"** และ **"ทุก requirement ต้องตามรอยไปถึง test ได้"**

## ใช้ตอนไหน
- เริ่มโปรเจกต์ซอฟต์แวร์ใหม่ และอยากได้กระบวนการครบตั้งแต่ต้นน้ำถึงปลายน้ำ
- ต้องการ "วาง process" ให้ทีม (โดยเฉพาะงาน enterprise / presales / ที่มี audit, compliance, security)
- มี requirement ดิบ ๆ อยากแปลงเป็นสเปก → ดีไซน์ → แผนทดสอบ → แผน deploy
- อยากรู้ว่า "ตอนนี้อยู่เฟสไหน เฟสถัดไปต้องทำอะไร ขาด artifact อะไร"

## แผนผังเฟส (Phase Map) — แต่ละเฟสมี sub-skill ของตัวเอง

| # | เฟส | sub-skill | Artifact หลักที่ได้ |
|---|-----|-----------|---------------------|
| 00 | Agile delivery framework (cross-cutting) | `/agile-delivery` | Sprint plan, backlog, ceremonies, DoR/DoD, velocity |
| 01 | Requirement discovery / elicitation | `/req-discovery` | Stakeholder map, user stories, MoSCoW backlog, acceptance criteria |
| 02 | Functional + Non-functional spec (SRS) | `/fr-nfr-spec` | FR list, NFR (perf/security/availability…), requirement IDs |
| 03 | Business logic & rules | `/business-logic-spec` | Decision tables, state machines, business rules catalog |
| 04 | Solution design / architecture | `/solution-design` | C4 diagrams, ADR, data model, API contract (HLD/LLD) |
| 05 | Authentication & Authorization | `/authn-authz-design` | AuthN flow, RBAC/ABAC model, session/token, MFA policy |
| 06 | Segregation of Duties (SoD) | `/sod-matrix` | Role × permission matrix, SoD conflict rules, least-privilege |
| 07 | Threat modeling | `/threat-model` | STRIDE/DFD, abuse cases, security requirements, mitigations |
| 08 | Development standards | `/dev-standards` | Coding standard, branching, code review, DoR/DoD |
| 09 | Test strategy & plan | `/test-strategy` | Test pyramid, test plan, coverage targets, test data |
| 10 | Regression & non-regression | `/regression-suite` | Impact analysis, regression suite, automation plan |
| 11 | Security testing | `/security-testing` | SAST/DAST/SCA/secret-scan plan, OWASP ASVS checklist |
| 12 | Penetration testing | `/pentest-plan` | Scope, Rules of Engagement, PTES/OWASP plan, report+retest |
| 13 | Deployment & release | `/release-deploy` | CI/CD pipeline, env strategy, blue-green/canary, rollback, change mgmt |
| 14 | Monitoring & observability | `/observability` | Logs/metrics/traces, SLI/SLO, alerting, incident runbook |

> ครอบคลุมครบทุกหัวข้อที่ขอ: requirement, FR, NFR, design, business logic, authentication, SoD, dev, test, regression, non-regression, security test, pen test, deployment, monitoring — บวก threat modeling และ Agile framework ที่จำเป็น

## วิธีขับเคลื่อนงาน (Engagement Flow)

1. **Intake — เข้าใจบริบทก่อน** ถามให้ครบ:
   - ระบบทำอะไร / ใครใช้ / ปัญหาที่แก้ (problem statement)
   - ประเภท: greenfield ใหม่ / เพิ่มฟีเจอร์ระบบเดิม / migration / integration
   - ข้อจำกัด: timeline, ทีม, งบ, tech stack, regulation (PDPA, ISO 27001, PCI-DSS…)
   - ระดับความเสี่ยง/ความสำคัญ (มีข้อมูลส่วนบุคคล/เงิน/ความปลอดภัยไหม)
2. **Tailor — ปรับความหนักเบาให้พอดีกับงาน** (ดู "Right-sizing" ด้านล่าง) — ไม่ทำทุกเฟสเต็มสูบกับทุกโปรเจกต์
3. **Execute ทีละเฟส** เรียก sub-skill ตามแผนผัง โดยแต่ละเฟส:
   - ผลิต artifact ของเฟสนั้น
   - ผ่าน **quality gate** ก่อนไปต่อ (ดูด้านล่าง)
   - อัปเดต **traceability matrix** (req ID → design → code → test → release)
4. **Iterate แบบ Agile** ไม่ทำ waterfall ยาว ๆ — แบ่งเป็น increment/sprint ผ่าน `/agile-delivery`, ทำเฟส 01–14 แบบ "บาง ๆ แต่ครบ" ต่อ slice แล้ววนซ้ำ
5. **Track สถานะ** บอกได้เสมอว่า "อยู่เฟสไหน, artifact ครบไหม, gate ผ่านไหม, ความเสี่ยงที่ค้าง (RAID)"

## Quality Gates (ด่านคุณภาพคั่นเฟส)

| Gate | ผ่านเมื่อ |
|------|-----------|
| **G0 Requirements baseline** | FR/NFR มี ID ครบ + acceptance criteria + ผู้มีส่วนได้เสีย sign-off |
| **G1 Design approved** | สถาปัตยกรรม + data model + API contract + ADR + threat model ผ่าน review |
| **G2 Ready for dev (DoR)** | story มี AC, design ชัด, dependency เคลียร์, ประเมิน effort แล้ว |
| **G3 Dev done (DoD)** | code + unit test + code review + ผ่าน CI + เอกสารอัปเดต |
| **G4 Test passed** | test plan รัน, regression เขียว, ช่องโหว่ critical/high = 0, UAT ผ่าน |
| **G5 Release ready** | runbook + rollback plan + change approval + monitoring/alert พร้อม |
| **G6 Live & stable** | SLO เขียว, alert ทำงาน, post-release review + ไม่มี incident เปิดค้าง |

## Right-sizing (ปรับสเกลตามขนาดงาน)

- **เล็ก / internal tool / prototype**: เน้น `/req-discovery` (เบา), `/fr-nfr-spec` (สั้น), `/solution-design` (1 หน้า), `/test-strategy` (smoke + critical path), deploy ง่าย ๆ — ข้าม pen test เต็มรูปแบบ
- **กลาง / มีผู้ใช้จริงภายนอก**: ครบทุกเฟส แต่ security testing แบบ automated (SAST/DAST) + pen test เฉพาะจุดเสี่ยง
- **ใหญ่ / enterprise / มีเงิน-ข้อมูลส่วนบุคคล / regulated**: เต็มทุกเฟส + `/sod-matrix` + `/threat-model` จริงจัง + `/pentest-plan` โดย third party + audit trail + compliance mapping (PDPA/ISO 27001/PCI-DSS)
- เกณฑ์ตัดสิน: ยิ่งระบบแตะ **เงิน / ข้อมูลส่วนบุคคล / ความปลอดภัย / ชื่อเสียง** มาก → ยิ่งลงเฟส security (05/06/07/11/12) หนัก

## Artifact กลางที่ใช้ข้ามเฟส (Cross-cutting)

**1) Traceability Matrix** — กระดูกสันหลังของ SDLC ลากเส้นทุก requirement ไปถึง test:

```
| Req ID | Requirement | Type(FR/NFR) | Design ref | Code/Module | Test case ID | Status |
|--------|-------------|--------------|-----------|-------------|--------------|--------|
| FR-001 | ผู้ใช้ login ด้วย email+OTP | FR | ADR-003, /authn | auth.service | TC-012, TC-013 | ✅ Pass |
| NFR-002| รองรับ 500 req/s p95<300ms | NFR | design §4.2 | api-gateway | PERF-002 | 🟡 Testing |
```

**2) RACI** — ใครรับผิดชอบอะไรในแต่ละเฟส (Responsible / Accountable / Consulted / Informed)

```
| กิจกรรม | PO | BA | Architect | Dev | QA | SecOps | DevOps |
|---------|----|----|-----------|-----|----|--------|--------|
| เก็บ requirement | A | R | C | I | C | I | I |
| ออกแบบสถาปัตยกรรม | C | C | R/A | C | I | C | C |
| Pen test | I | I | C | I | C | A/R | C |
```

**3) RAID Log** — Risks / Assumptions / Issues / Dependencies ที่ติดตามตลอดโปรเจกต์

**4) DoR / DoD** — Definition of Ready / Done (นิยามอยู่ใน `/agile-delivery` และ `/dev-standards`)

## เคล็ดลับ & ข้อควรระวัง
- **อย่าออกแบบก่อนเข้าใจปัญหา** — ทำ `/req-discovery` ให้แน่นก่อน design เสมอ มิฉะนั้น rework บาน
- **Security/Authz ออกแบบตั้งแต่ design ไม่ใช่แปะทีหลัง** — `/authn-authz-design` + `/sod-matrix` + `/threat-model` ต้องเกิดในเฟส design (shift-left)
- **Non-functional มักถูกลืม** — NFR (performance, availability, security, scalability, observability) สำคัญพอ ๆ กับ FR; บังคับให้มีใน `/fr-nfr-spec`
- **Regression ≠ การทดสอบฟีเจอร์ใหม่** — `/regression-suite` คือกันของเก่าพัง; non-regression คือยืนยันว่าการแก้ "ไม่ไปกระทบ" สิ่งที่เคยทำงาน
- **ทำแบบ Agile ไม่ใช่ waterfall** — อย่าหวังเสร็จทุก artifact ก่อนเริ่มเขียนโค้ด; ทำเป็น vertical slice บาง ๆ ที่ผ่านทุกเฟส แล้ว iterate
- **เลือกใช้เฉพาะ sub-skill ที่จำเป็น** — ดู Right-sizing; การทำเอกสารเกินจำเป็นคือ waste

## เริ่มยังไง
บอกผมว่าจะทำระบบอะไร + บริบท (ตาม Intake ข้างบน) แล้วผมจะ:
1. สรุป problem statement + เสนอ scope ของเฟสที่ควรทำ (right-sized)
2. เริ่มเฟสแรกที่เหมาะ (ปกติคือ `/req-discovery`) และไล่ทีละ gate
3. คอยอัปเดต traceability + RAID ให้

> ภาพรวมทั้งวงจรอยู่ที่สกิลนี้ — ลงรายละเอียดเฟสไหนให้พิมพ์ slug ของเฟสนั้นได้เลย (เช่น `/threat-model`)
