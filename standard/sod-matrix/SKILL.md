---
name: sod-matrix
description: ออกแบบ Segregation of Duties (SoD) — แยกหน้าที่ไม่ให้คนคนเดียวคุมครบทั้งธุรกรรมสำคัญ ด้วย role×permission matrix, conflict rules (maker-checker), least privilege และ access review/recertification. Design Segregation of Duties: separate sensitive transactions, build a role×permission matrix, codify toxic-combination rules, apply least privilege, and run periodic access reviews. Trigger เมื่อผู้ใช้พิมพ์ /sod-matrix หรือขอ "SoD / segregation of duties / แยกหน้าที่ / maker checker / role permission matrix / least privilege / access review / สิทธิ์ขัดแย้ง".
category: sdlc
phase: "06 Segregation of Duties"
---

# /sod-matrix — แยกหน้าที่และเมทริกซ์สิทธิ์ (Segregation of Duties)

ออกแบบให้ไม่มี "คนเดียวคุมจบ" ในธุรกรรมที่อ่อนไหว โดยกำหนด **role × permission matrix**, กฎ **SoD conflict / toxic combinations** (maker ≠ checker), หลัก **least privilege / need-to-know**, **compensating controls** สำหรับทีมเล็ก และรอบ **access review / recertification** — ส่งมอบเป็นเอกสารควบคุมที่ auditor และทีม dev เอาไปบังคับใช้ผ่าน RBAC ได้จริง

## ใช้ตอนไหน

- ระบบมีธุรกรรมที่มีมูลค่า/ความเสี่ยงสูง: จัดซื้อ (PR→PO→รับของ→จ่ายเงิน), การเงิน (ตั้งเจ้าหนี้→อนุมัติ→โอน), เปลี่ยน master data (ผู้ขาย/ราคา/บัญชีธนาคาร), การ deploy โค้ดขึ้น prod, การจัดการสิทธิ์ผู้ใช้
- ต้องผ่าน audit/compliance: ISO 27001 (A.5.3 Segregation of duties), COBIT, หรือ SOX (ICFR กรณีบริษัทมหาชน/การเงิน)
- มี role ใหม่/รวม role/ทีมเล็กที่คนหนึ่งทำหลายหน้าที่ แล้วต้องพิสูจน์ว่าความเสี่ยงถูกคุม
- ก่อน implement RBAC จริง — ใช้เป็น "ความจริงต้นทาง" (source of truth) ให้ /authn-authz-design นำไป enforce

> ขอบเขตเฟสนี้ = **ออกแบบว่าใครควร/ไม่ควรทำอะไรร่วมกัน + วิธีตรวจทาน**
> กลไกบังคับ (token, role check, policy engine) อยู่ที่ **/authn-authz-design** · การวิเคราะห์ภัยคุกคาม/abuse case อยู่ที่ **/threat-model**

## Input ที่ต้องถามก่อนเริ่ม

1. **กระบวนการอ่อนไหว (sensitive processes)** ที่ต้องคุม — list ขั้นตอนแบบ end-to-end ของแต่ละ process (เช่น procure-to-pay, user provisioning, code-to-prod)
2. **Functions / กิจกรรมย่อย** ในแต่ละ process (สร้าง / แก้ / อนุมัติ / จ่าย / รับของ / deploy / มอบสิทธิ์ / ดู report)
3. **Roles / ตำแหน่งงาน** ที่มีในองค์กรหรือระบบ (Requester, Approver, AP Clerk, Finance Manager, Developer, Release Manager, IT Admin, Auditor …)
4. **ขนาดทีมและข้อจำกัด** — ทีมเล็ก/คนทำงานทับซ้อนไหม? (ตัวกำหนดว่าต้องใช้ compensating control แค่ไหน)
5. **เกณฑ์ความเสี่ยง / threshold** — เช่น วงเงินที่ต้องอนุมัติ 2 ชั้น, การเปลี่ยน vendor bank account ที่ต้องมี dual control
6. **มาตรฐานที่ต้องอ้าง** — ISO 27001 / SOX / COBIT / ข้อกำหนดลูกค้า เพื่อ map control ให้ตรง
7. **ระบบที่บังคับใช้จริง** (ERP, IdP, CI/CD, custom app) — เพื่อรู้ว่า matrix จะไป enforce ที่ชั้นไหน

## ขั้นตอน (Playbook)

1. **แตก process เป็น functions** — เขียน sensitive transaction แต่ละตัวเป็นลำดับขั้น แล้วระบุว่าขั้นไหนเป็น "จุดควบคุม" (control point) เช่น "อนุมัติ PO", "ปล่อยจ่ายเงิน", "deploy prod"
2. **ระบุ toxic combinations** — คู่ function ที่ถ้าคนเดียวทำได้ทั้งคู่จะเกิดความเสี่ยง (ฉ้อโกง/error/abuse) เช่น *สร้าง PO + อนุมัติ PO*, *แก้ vendor bank account + อนุมัติจ่าย*, *เขียนโค้ด + deploy prod เอง*
3. **กำหนด least privilege ของแต่ละ role** — แต่ละ role ได้สิทธิ์เท่าที่จำเป็นต่อหน้าที่ (need-to-know) ไม่ผูก permission ที่ไม่ได้ใช้
4. **สร้าง role × permission matrix** — ตาราง ✓/✗ ว่า role ไหนทำ function ไหนได้
5. **ตรวจ matrix ทับกับ conflict rules** — ไล่ทุก role: มี role ใดถือ permission คู่ที่เป็น toxic combination พร้อมกันไหม? ถ้ามี → ต้องแยก role หรือใส่ compensating control
6. **ออกแบบ maker-checker / dual control** ที่จุดควบคุม — กำหนดชัดว่า maker ≠ checker, ใครอนุมัติชั้นไหน, วงเงินไหนต้องสองลายเซ็น
7. **ออกแบบ compensating controls** สำหรับกรณีแยกไม่ได้ (ทีมเล็ก) — เช่น mandatory logging + independent review รายเดือน, dual approval, alert เมื่อ self-approve, จำกัดด้วย threshold
8. **กำหนด access review / recertification** — ความถี่ (รายไตรมาส/ครึ่งปี), ใครเป็นผู้รับรอง (data/process owner ไม่ใช่ IT), วิธีจัดการสิทธิ์ที่ไม่ผ่าน
9. **Map ไปมาตรฐาน** — ผูกแต่ละ control เข้ากับ ISO 27001 A.5.3 / SOX ICFR / COBIT เพื่อใช้เป็นหลักฐาน audit
10. **ส่งต่อให้ enforcement** — ส่ง matrix + rules ให้ /authn-authz-design implement เป็น RBAC/ABAC จริง

## Output / Artifact (เทมเพลตพร้อมใช้)

### A) Role × Permission Matrix (ตัวอย่าง: Procure-to-Pay)

| Permission / Function          | Requester | Approver (Mgr) | AP Clerk | Finance Mgr | IT Admin | Auditor |
|--------------------------------|:---------:|:--------------:|:--------:|:-----------:|:--------:|:-------:|
| สร้าง PR (purchase request)     | ✓         | ✗              | ✗        | ✗           | ✗        | ✗       |
| อนุมัติ PR / แปลงเป็น PO         | ✗         | ✓              | ✗        | ✗           | ✗        | ✗       |
| แก้ master data ผู้ขาย/บัญชีธนาคาร | ✗       | ✗              | ✓        | ✗           | ✗        | ✗       |
| อนุมัติ master data ผู้ขาย        | ✗         | ✗              | ✗        | ✓           | ✗        | ✗       |
| บันทึกใบแจ้งหนี้ (AP invoice)    | ✗         | ✗              | ✓        | ✗           | ✗        | ✗       |
| อนุมัติ/ปล่อยจ่ายเงิน (payment run) | ✗      | ✗              | ✗        | ✓           | ✗        | ✗       |
| จัดการสิทธิ์ผู้ใช้ (provision role) | ✗      | ✗              | ✗        | ✗           | ✓        | ✗       |
| ดู audit log / report (read-only) | ✗      | ✗              | ✗        | ✗           | ✗        | ✓       |

> หลัก least privilege: ทุก cell ที่ไม่จำเป็นต่อหน้าที่ = ✗ · Auditor เป็น read-only เท่านั้น (ไม่มีสิทธิ์แก้ใด ๆ)

### B) SoD Conflict Rules (Toxic Combinations)

| #   | Function A           | ขัดกับ Function B        | เหตุผล (risk)                                              | Required Control                              | มาตรฐาน        |
|-----|----------------------|-------------------------|-----------------------------------------------------------|-----------------------------------------------|----------------|
| SOD-1 | สร้าง PR/PO          | อนุมัติ PR/PO            | สั่งซื้อให้ตัวเอง/พวกพ้องโดยไม่มีคนตรวจ → ฉ้อโกงจัดซื้อ      | maker ≠ checker; แยก role Requester/Approver   | ISO A.5.3, SOX |
| SOD-2 | แก้ vendor bank account | อนุมัติ/ปล่อยจ่ายเงิน   | เปลี่ยนเลขบัญชีปลายทางแล้วโอนเข้าบัญชีตัวเอง               | dual control + alert เมื่อแก้ bank แล้วจ่ายภายใน N วัน | SOX, COBIT     |
| SOD-3 | บันทึก AP invoice    | อนุมัติ payment run      | สร้างหนี้ปลอมแล้วอนุมัติจ่ายเอง                              | แยก AP Clerk / Finance Mgr; 4-eyes ที่จุดจ่าย   | SOX ICFR       |
| SOD-4 | เขียน/merge โค้ด     | deploy ขึ้น prod         | ฝัง backdoor/แก้แล้ว push ขึ้น prod โดยไม่มี review/gate     | dev ≠ deployer; CI gate + approval ก่อน prod   | ISO A.8.31     |
| SOD-5 | จัดการสิทธิ์ผู้ใช้ (IT Admin) | อนุมัติธุรกรรมธุรกิจ | มอบสิทธิ์ให้ตัวเองแล้วทำธุรกรรม → privilege escalation     | IT Admin = สิทธิ์เทคนิคเท่านั้น, ห้ามถือ business role | ISO A.5.3      |

### C) Compensating Controls (กรณีทีมเล็ก / แยก role ไม่ได้)

| ความเสี่ยงที่แยกไม่ได้           | Compensating Control                                                        | ผู้ตรวจ/รับรอง          | ความถี่    |
|--------------------------------|----------------------------------------------------------------------------|------------------------|-----------|
| คนเดียวทั้งสร้างและอนุมัติ PO    | log ทุกการ self-approve + ผู้บริหารอิสระ review รายการ + จำกัด threshold วงเงิน | Finance Director       | รายเดือน   |
| dev เดียว deploy prod เอง        | บังคับ peer review (PR approval) + immutable deploy log + post-deploy review | Tech Lead (คนอื่น)      | ทุก release |
| admin คนเดียวจัดการสิทธิ์ทั้งระบบ | break-glass account แยก + log ทุก privilege change + แจ้งเตือนทันที          | Security/External audit | รายเดือน   |

### D) Access Review / Recertification Checklist

- [ ] กำหนดรอบ recertification ชัดเจน (เช่น **รายไตรมาส** สำหรับ privileged role, **รายครึ่งปี** สำหรับทั่วไป)
- [ ] **ผู้รับรอง = data/process owner** (เจ้าของกระบวนการธุรกิจ) ไม่ใช่ IT หรือเจ้าตัว
- [ ] รายการ review ครบ: user × role × permission ที่ถืออยู่จริง (ดึงจากระบบ ไม่ใช่จากเอกสาร)
- [ ] ตรวจ **orphan/stale accounts** (พนักงานลาออก/ย้ายแผนกแต่สิทธิ์ค้าง)
- [ ] ตรวจ **SoD violation** อัตโนมัติ: มี user ใดถือ permission คู่ toxic combination จาก §B ไหม
- [ ] ทุกสิทธิ์ที่ "ไม่รับรอง" ต้องถูก **revoke ภายใน SLA** (เช่น 7 วัน) และบันทึกหลักฐาน
- [ ] เก็บหลักฐานการรับรอง (ใคร/เมื่อไหร่/รายการ) ไว้สำหรับ audit
- [ ] privileged/admin access ใช้ **time-bound / JIT** ถ้าทำได้ (ลดสิทธิ์ค้าง)

## Checklist / Definition of Done

- [ ] ทุก sensitive process ถูกแตกเป็น functions และระบุ control point แล้ว
- [ ] มี role × permission matrix ครบทุก role × function (✓/✗ ชัดเจน, default = ✗ ตาม least privilege)
- [ ] มีตาราง SoD conflict rules ครบ พร้อมเหตุผล + required control + อ้างมาตรฐาน
- [ ] ตรวจแล้วว่า **ไม่มี role ใดถือ toxic combination** — ถ้ามี ต้องมี compensating control กำกับชัด
- [ ] maker-checker / dual control ถูกกำหนดที่ทุกจุดควบคุม (maker ≠ checker)
- [ ] กรณีทีมเล็กมี compensating controls + ผู้ตรวจอิสระ + ความถี่
- [ ] มีแผน access review/recertification (รอบ, ผู้รับรอง, SLA revoke)
- [ ] map control → ISO 27001 A.5.3 (+ SOX/COBIT ถ้าเกี่ยว) ครบ
- [ ] ส่ง matrix + rules ต่อให้ /authn-authz-design เพื่อ enforce ผ่าน RBAC/ABAC

## เคล็ดลับ & ข้อควรระวัง

- **อย่ายัด permission ที่ role ใช้ "นาน ๆ ที"** — สิทธิ์ที่ไม่ค่อยใช้คือช่องโหว่ ใช้ JIT/elevation ชั่วคราวแทนการถือถาวร
- **ระวัง role creep / role explosion** — คนสะสมสิทธิ์ตอนย้ายงานแต่ของเก่าไม่ถูกถอน; recertification คือยาแก้ ไม่ใช่ matrix สวย ๆ ครั้งเดียว
- **toxic combination อันตรายข้ามระบบ** — บางทีคนถือสิทธิ์ A ใน ERP และ B ใน CI/CD; ต้อง review สิทธิ์รวมข้ามระบบ ไม่ใช่แยกระบบ
- **maker-checker ต้องเป็นคน "คนละคน" จริง** — ไม่ใช่บัญชีเดียวกันที่มี 2 role; ระวัง shared/service account ที่ทำลายการแยกหน้าที่
- **compensating control ต้อง detective + อิสระ** — log อย่างเดียวไม่พอ ต้องมีคนอื่น review จริงและมีหลักฐานว่าได้ review
- **อย่าให้ admin/superuser ถือ business role** — แยกสิทธิ์เทคนิค (จัดการระบบ) ออกจากสิทธิ์ธุรกรรม (อนุมัติ/จ่าย) เด็ดขาด
- **break-glass ต้องมี แต่ต้องดัง** — บัญชีฉุกเฉินใช้ได้ แต่ต้อง trigger alert + review ทุกครั้งที่ใช้
- เริ่มจาก process ที่เสี่ยงสุด (เงิน/prod) ก่อน อย่าพยายามทำ matrix ครบทั้งองค์กรในรอบเดียว

## เชื่อมกับเฟสอื่น

- **ก่อนหน้า:** `/authn-authz-design` — ออกแบบกลไก authn และ role enforcement (matrix นี้คือ input ให้มัน implement)
- **ถัดไป:** `/threat-model` — เอา conflict rules/abuse case ไปวิเคราะห์ภัยคุกคามและ attacker scenario ต่อ
- **ภาพรวมทั้งวงจร:** `/sdlc-agile` — ตำแหน่งเฟส SoD ในวงจร SDLC ทั้งหมด
- เกี่ยวข้อง: `/business-logic-spec` (จุดควบคุมในกฎธุรกิจ), `/observability` (logging/alert สำหรับ compensating & detective control)
