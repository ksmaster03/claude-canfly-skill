---
name: agile-delivery
description: สกิลนี้วางกรอบส่งมอบงานแบบ Agile (Scrum/Kanban/Scrumban) — กำหนด roles, artifacts, ceremonies, backlog, DoR/DoD และ metrics (velocity, cycle time, WIP) เป็นเฟส cross-cutting ที่ครอบทุกเฟสของ SDLC ไม่ใช่ขั้นตอนเดียวจบ. Trigger เมื่อผู้ใช้พิมพ์ /agile-delivery หรือขอ "วาง process Agile / Scrum / Kanban / sprint planning / backlog / retrospective / agile ceremonies".
category: sdlc
phase: "00 Agile Delivery"
---

# /agile-delivery — กรอบส่งมอบแบบ Agile (Agile Delivery Framework)

สกิลนี้ช่วยทีมซอฟต์แวร์ไทยตั้ง "วิธีส่งมอบงาน" แบบ Agile ให้เป็นระบบ — เลือกเฟรมเวิร์ก (Scrum / Kanban / Scrumban), ตั้ง roles + ceremonies + artifacts, เขียน user story ที่ดี, กำหนด DoR/DoD และวัดผลด้วย metrics ที่ใช้จริง. เป็นเฟส cross-cutting: ห่อหุ้มทุกเฟสอื่นใน SDLC ไม่ใช่แค่ขั้นตอนหนึ่ง.

## ใช้ตอนไหน
- เริ่มโปรเจกต์/ทีมใหม่ และต้องตกลง "เราจะทำงานกันยังไง" (ways of working)
- ทีมทำ Agile แบบ cargo-cult — มี standup แต่ไม่มี outcome, sprint ไม่เคยจบตาม commit, backlog รก
- ต้องเลือกระหว่าง Scrum กับ Kanban หรือผสม (Scrumban) ให้เหมาะกับลักษณะงาน
- velocity เหวี่ยง, ส่งมอบไม่ตรง, อยากตั้ง metrics + cadence ให้ predictable
- onboard คนใหม่ / vendor / ลูกค้า ให้เข้าใจ ceremonies, DoR/DoD และ role ใครทำอะไร

## Input ที่ต้องถามก่อนเริ่ม
1. **ลักษณะงาน**: feature project (scope เปลี่ยนเป็นรอบ ๆ) หรือ flow งานเข้าต่อเนื่อง (support/ops/bug)? → ชี้ Scrum vs Kanban
2. **ขนาดทีม & องค์ประกอบ**: dev กี่คน, มี QA/Design/DevOps ไหม, full-time หรือ shared? (Scrum team ที่ดี ~3–9 คน)
3. **มี PO ตัวจริงไหม**: ใครตัดสินใจ priority และรับผิดชอบ value? ถ้าไม่มี = ความเสี่ยงอันดับ 1
4. **Cadence ที่เป็นไปได้**: release ได้ถี่แค่ไหน, มี dependency กับทีมอื่น/ลูกค้าไหม
5. **Tooling**: Jira / Azure DevOps / Trello / GitHub Projects — ไว้ map สถานะ workflow และดึง metrics
6. **Definition of "เสร็จ" วันนี้คืออะไร**: มี CI/CD, automated test, code review, staging ไหม → ตั้ง DoD ตามความเป็นจริง แล้วค่อยยกระดับ
7. **ข้อจำกัด**: fixed-date/fixed-scope (TOR/สัญญา), งบ, regulatory — มีผลต่อ commitment model

## ขั้นตอน (Playbook)

**Step 1 — เลือกเฟรมเวิร์ก**

| เกณฑ์ | Scrum | Kanban | Scrumban |
|---|---|---|---|
| ลักษณะงาน | scope เป็นก้อน วางแผนเป็นรอบได้ | งานเข้าไม่แน่นอน/ต่อเนื่อง (bug, support) | mix ทั้งสอง |
| Cadence | timebox คงที่ (sprint 1–4 สัปดาห์) | flow ต่อเนื่อง ไม่มี sprint บังคับ | sprint หลวม ๆ + WIP limit |
| Commitment | commit เป็น sprint goal | pull งานเมื่อมี capacity | planning เมื่อ backlog ใกล้หมด |
| ตัวขับหลัก | velocity / sprint goal | WIP limit + cycle time | WIP limit + cadence เบา ๆ |
| เหมาะกับ | product/feature team | maintenance/ops/platform | ทีมที่โต/ผันผวน หรือกำลังเปลี่ยนผ่าน |

แนวทาง: งานสร้าง product ใหม่ → **Scrum**; งาน support/ops ที่ priority เด้งตลอด → **Kanban**; ทีมที่มีทั้งสองหรือ Scrum แล้วอึดอัดกับ timebox → **Scrumban**.

**Step 2 — ตั้ง Roles (อ้าง Scrum Guide 2020)**
- **Product Owner**: เจ้าของ Product Backlog และ value — จัดลำดับ, ตัดสินใจ scope, ตัวแทน stakeholder. *คนเดียว* ไม่ใช่ committee.
- **Scrum Master**: รับผิดชอบให้ทีมทำ Scrum ได้จริง, ขจัด impediment, โค้ช process, ป้องกัน team จากการถูกแทรก. ไม่ใช่ PM สั่งงาน.
- **Developers (Development Team)**: cross-functional, self-managing, รับผิดชอบสร้าง Increment และตั้ง Sprint Backlog. ใน Scrum Guide 2020 ทั้งสามรวมเป็น **Scrum Team** เดียว ไม่มี sub-team.
- (Kanban ไม่บังคับ role แต่ในทางปฏิบัติยังต้องมีคนดูแล priority + คน facilitate flow)

**Step 3 — ตั้ง Artifacts + commitment**
- **Product Backlog** (commitment = *Product Goal*): รายการงานทั้งหมด เรียงตาม priority, refine ต่อเนื่อง
- **Sprint Backlog** (commitment = *Sprint Goal*): งานที่เลือกทำใน sprint + แผนส่งมอบ
- **Increment** (commitment = *Definition of Done*): ผลงานที่ "เสร็จ" จริงและใช้งานได้ ทุก increment ต้องผ่าน DoD

**Step 4 — ตั้ง Ceremonies + timebox** (อิง sprint 2 สัปดาห์ เป็นค่าเริ่ม)

| Ceremony | Timebox (sprint 2 wk) | จุดประสงค์ / output |
|---|---|---|
| Sprint Planning | ≤ 4 ชม. | ตั้ง Sprint Goal + เลือกงานเข้า Sprint Backlog |
| Daily Standup (Daily Scrum) | 15 นาที | sync แผนวันต่อวันสู่ Sprint Goal + ยก impediment (ไม่ใช่ status report) |
| Backlog Refinement | ~5–10% ของ capacity/sprint | ทำ story ให้พร้อม (ผ่าน DoR), estimate, แตกงาน |
| Sprint Review | ≤ 2 ชม. | demo Increment ต่อ stakeholder + เก็บ feedback ปรับ backlog |
| Sprint Retrospective | ≤ 1.5 ชม. | ปรับปรุง "วิธีทำงาน" + ตั้ง action ที่ทำได้จริง |

(timebox ของ Scrum Guide อิงต่อ sprint 1 เดือน: Planning ≤ 8 ชม., Review ≤ 4 ชม., Retro ≤ 3 ชม. — ให้ pro-rate ตามความยาว sprint จริง)

**Step 5 — มาตรฐาน User Story + Estimation**
- รูปแบบ: **As a `<ผู้ใช้>`, I want `<สิ่งที่ต้องการ>`, so that `<คุณค่า/เหตุผล>`** + Acceptance Criteria (เขียนแบบ Given/When/Then ได้)
- เช็คด้วย **INVEST**: Independent, Negotiable, Valuable, Estimable, Small, Testable
- Estimation: **Story Points** (relative, ใช้ Fibonacci 1,2,3,5,8,13) ด้วย **Planning Poker** เพื่อจับ uncertainty ไม่ใช่จับชั่วโมง; ทีม/epic ใหญ่ใช้ **T-shirt sizing** (S/M/L/XL) ตอนยังหยาบ แล้วค่อยแตกเป็น points
- story ที่ > 8–13 points หรือทำไม่จบใน 1 sprint = ใหญ่ไป ต้องแตก (split by workflow step, by data variation, happy path ก่อน edge case)

**Step 6 — กำหนด DoR / DoD** (ใช้เทมเพลตด้านล่าง) ให้ทีมตกลงร่วมกันและติดไว้ที่มองเห็น

**Step 7 — ตั้ง Metrics + WIP** เลือกที่เหมาะกับเฟรมเวิร์ก (ดูตารางในส่วนเคล็ดลับ), ตั้ง **WIP limit** สำหรับ Kanban/Scrumban, เก็บ baseline 2–3 sprint ก่อนตัดสินใจปรับ

## Output / Artifact (เทมเพลตพร้อมใช้)

### A) Sprint Plan
```
Sprint:        #__   |  ระยะ: dd/mm – dd/mm (2 สัปดาห์)
Sprint Goal:   <ประโยคเดียวที่บอกคุณค่าที่จะส่งมอบ>
Capacity:      __ คน × __ วันทำงาน − ลา/ประชุม = __ คน-วัน  |  Committed points: __
```
| Story ID | User Story (สรุป) | Owner | Points | DoR ✓ | Status |
|---|---|---|---|---|---|
| PROJ-101 | ผู้ใช้ login ด้วย email/OTP | A | 5 | ✓ | In Progress |
| PROJ-102 | ดูประวัติคำสั่งซื้อ | B | 3 | ✓ | To Do |
| PROJ-103 | export รายงาน PDF | C | 8 | ✗ | (รอ refine) |

### B) Product Backlog
| ID | Story / Item | Priority | Type | Points | Status | หมายเหตุ |
|---|---|---|---|---|---|---|
| PROJ-201 | ค้นหาสินค้าด้วยคีย์เวิร์ด | High | Story | 5 | Ready | — |
| PROJ-202 | แจ้งเตือนสต็อกใกล้หมด | Med | Story | 8 | Refining | รอ NFR จาก /fr-nfr-spec |
| PROJ-203 | bug: ยอดรวม VAT ผิด | High | Bug | 3 | Ready | reproduce ได้แล้ว |
| PROJ-204 | migrate auth → OAuth2 | Low | Tech/Spike | 13 | New | ต้องแตกก่อน |
> Priority: High / Med / Low (หรือ MoSCoW: Must / Should / Could / Won't) · Status: New → Refining → Ready → In Sprint → Done

### C) Checklist — Definition of Ready (DoR) — เกณฑ์ "พร้อมเข้า sprint"
- [ ] เขียนรูปแบบ user story ครบ (As a / I want / so that) และเข้าใจตรงกัน
- [ ] มี Acceptance Criteria ที่ทดสอบได้ (Given/When/Then)
- [ ] ผ่าน INVEST — โดยเฉพาะ Small (จบใน 1 sprint) และ Testable
- [ ] dependency / external API / data ที่ต้องใช้ระบุชัด และพร้อม (ไม่ block)
- [ ] design / mockup ที่จำเป็นพร้อม (อ้าง /solution-design ถ้ามี)
- [ ] ทีม estimate เป็น points ได้แล้ว (ไม่ใหญ่เกิน 8–13)
- [ ] NFR / security ที่เกี่ยวข้องระบุไว้ (อ้าง /fr-nfr-spec, /threat-model)

### D) Checklist — Definition of Done (DoD) — เกณฑ์ "เสร็จจริง" (ตั้งตามความพร้อมทีม แล้วยกระดับ)
- [ ] code เขียนเสร็จ + ผ่าน code review (อย่างน้อย 1 reviewer)
- [ ] unit / integration test เขียนแล้วและ pass (อ้าง /test-strategy)
- [ ] ผ่าน Acceptance Criteria ครบทุกข้อ
- [ ] merge เข้า main, CI เขียว, ไม่ทำ build/test อื่นพัง
- [ ] security/lint/SAST ผ่านเกณฑ์ (อ้าง /security-testing)
- [ ] เอกสาร/release note/i18n อัปเดต (ถ้ามีผล)
- [ ] deploy ขึ้น staging และ verify โดยคนที่ไม่ใช่คนเขียน
- [ ] PO ยอมรับ (accept) story แล้ว

### E) Retrospective (โครง Start / Stop / Continue)
```
Sprint #__ Retro — ผู้เข้าร่วม: ____  | facilitator: ____
🟢 START (เริ่มทำ)    : สิ่งที่อยากลองทำใหม่
🔴 STOP (หยุดทำ)      : สิ่งที่ฉุดทีม / เสียเวลา
🔵 CONTINUE (ทำต่อ)   : สิ่งที่ได้ผล อยากรักษาไว้
─────────────────────────────────────────────
Action items (ทำได้จริง, มีเจ้าของ, มี due):
1. [ ] <action> — owner: ___ — due: sprint หน้า
2. [ ] <action> — owner: ___ — due: ___
```
> (ตัวแปร: 4Ls = Liked/Learned/Lacked/Longed-for, หรือ Mad/Sad/Glad — เลือกสลับกันได้กันเบื่อ)

## Checklist / Definition of Done (ของตัวสกิลนี้)
- [ ] เลือกเฟรมเวิร์ก (Scrum/Kanban/Scrumban) พร้อมเหตุผลอิงลักษณะงาน
- [ ] ระบุ roles ครบ + มีคนรับ PO และ Scrum Master จริง
- [ ] กำหนด artifacts 3 ตัว + commitment ของแต่ละตัว
- [ ] ตั้ง ceremonies พร้อม timebox และความถี่
- [ ] มี DoR + DoD ที่ทีมตกลงร่วมและติดให้เห็น
- [ ] มี estimation method + cadence/sprint length
- [ ] เลือก metrics + ตั้ง WIP limit (ถ้า Kanban/Scrumban)
- [ ] backlog seed เริ่มต้น + sprint plan แรกพร้อม

## เคล็ดลับ & ข้อควรระวัง
- **Metrics ใช้ให้ถูกตัว** — อย่าใช้ velocity เปรียบเทียบข้ามทีม (points เป็น relative ของแต่ละทีม) และอย่าตั้ง velocity เป็น KPI กดดัน เพราะทีมจะ inflate points.

| Metric | วัดอะไร | เหมาะกับ |
|---|---|---|
| Velocity | points ที่ทำเสร็จต่อ sprint (เฉลี่ย 3–5 sprint) | Scrum — วางแผน capacity |
| Burndown / Burnup | งานเหลือ / งานสะสมเทียบเวลา | Scrum — ดู progress ใน sprint/release |
| Cycle Time | เวลาตั้งแต่ "เริ่มทำ" ถึง "เสร็จ" ของ 1 item | Kanban — ความเร็ว flow |
| Lead Time | เวลาตั้งแต่ "ขอ" ถึง "ส่งมอบ" | Kanban — มุมลูกค้า |
| Throughput | จำนวน item เสร็จต่อช่วงเวลา | Kanban — กำลังการผลิต |
| WIP limit | งานพร้อมกันสูงสุดต่อ column | Kanban/Scrumban — ลด context switch |

- **Daily standup ≠ status report ให้หัวหน้า** — เป็นการ re-plan สู่ Sprint Goal; ถ้ากลายเป็นรายงานเจ้านาย ให้ Scrum Master ดึงกลับ
- **WIP สูง = ฆาตกรเงียบ** — งานค้างเยอะทำให้ cycle time พุ่ง; จำกัด WIP บังคับให้ "ปิดงานก่อนเปิดใหม่"
- **อย่า inflate DoD เกินความพร้อม** — ตั้ง DoD ตามที่ทีมทำได้จริงวันนี้ (เช่น ยังไม่มี automated test ก็ใส่ manual test ก่อน) แล้ว *ยกระดับทุก retro* ค่อยเป็นค่อยไป
- **Sprint Goal มีค่ามากกว่ารายการ story** — ถ้าทำ story ไม่ครบแต่บรรลุ goal = สำเร็จ; ใช้ goal เป็นเข็มทิศเวลา scope สั่น
- **Refinement ต้องสม่ำเสมอ** — backlog ที่ไม่ refine = planning ช้าและ commit พลาด; กัน 5–10% capacity ทุก sprint
- **Retro ที่ไม่มี action = เสียเวลา** — ทุก retro ต้องได้ action ที่มีเจ้าของ + due และตามผลใน retro ถัดไป
- **fixed-date/fixed-scope (TOR ไทย)** — ถ้าสัญญา fix ทั้งวันและ scope ให้ใช้ Agile บริหาร *ภายใน* (ส่งมอบเป็นรอบ ลด risk เร็ว) แต่เปิดเผย scope-vs-time ผ่าน burnup + change log ให้ stakeholder เห็นแต่เนิ่น ๆ

## เชื่อมกับเฟสอื่น
- **ก่อนหน้า**: — (เป็นเฟส cross-cutting เฟสแรก — ห่อหุ้มทุกเฟสที่ตามมา)
- **ถัดไป**: `/req-discovery` — เก็บความต้องการมาเติม Product Backlog
- **ภาพรวมทั้งวงจร**: `/sdlc-agile` — เห็นทุกเฟส (req → design → dev → test → release → observe) ทำงานในจังหวะ Agile ที่สกิลนี้วางไว้
- **ป้อนงานเข้า ceremonies จากเฟสอื่น**: `/fr-nfr-spec`, `/business-logic-spec` (เนื้อ story + AC), `/solution-design`, `/authn-authz-design`, `/sod-matrix`, `/threat-model` (ใส่เป็น input/constraint ของ DoR), `/test-strategy`, `/regression-suite`, `/security-testing`, `/pentest-plan` (อ้างใน DoD), `/dev-standards` (เกณฑ์ code review ใน DoD), `/release-deploy` + `/observability` (นิยาม "deploy แล้ว verify" ใน DoD และ feedback กลับเข้า backlog)
