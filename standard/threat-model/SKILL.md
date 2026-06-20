---
name: threat-model
description: ทำ threat modeling ตั้งแต่ตอนออกแบบ — วาด DFD + trust boundary, ใช้ STRIDE หา threat รายองค์ประกอบ, จัดลำดับความเสี่ยง แล้วแปลงเป็น security requirement + mitigation ที่ส่งต่อให้ทีม dev/test ใช้ได้จริง. Model the system, find what can go wrong (STRIDE-per-element), rank risk, and turn it into actionable security controls. Trigger เมื่อผู้ใช้พิมพ์ /threat-model หรือขอ "threat model / STRIDE / DFD / security design / abuse case / attack surface / วิเคราะห์ภัยคุกคาม / ความเสี่ยงความปลอดภัย".
category: sdlc
phase: "07 Threat Modeling"
---

# /threat-model — สร้างแบบจำลองภัยคุกคาม (Threat Modeling)

ลงมือ threat modeling แบบ design-time: วาด data flow diagram (DFD) ระบุ trust boundary แล้วใช้ STRIDE หาภัยคุกคามรายองค์ประกอบ จัดลำดับความเสี่ยง และแปลงออกมาเป็น security requirement + mitigation ที่ระบุเจ้าของและตรวจสอบได้ ไม่ใช่รายงานภัยคุกคามลอย ๆ ที่ไม่มีใครเอาไปทำต่อ

## ใช้ตอนไหน

ทำ threat model "ก่อนเขียนโค้ด" และทำซ้ำเมื่อสถาปัตยกรรมเปลี่ยน เพราะการแก้ที่ design ถูกกว่าแก้ที่ prod หลายเท่า ทริกเกอร์ที่ควรทำ:

- ออกแบบระบบ/บริการใหม่ หรือ epic ใหม่ที่มี data flow ของตัวเอง
- **มี trust boundary เปลี่ยน** เช่น เปิด endpoint สู่ public, รับ input จาก third party, ย้าย data ข้าม network zone, เพิ่ม integration ภายนอก
- ฟีเจอร์เสี่ยงสูง: จ่ายเงิน, จัดการ credential/secret, อัปโหลดไฟล์, สิทธิ์ผู้ดูแล, export ข้อมูลส่วนบุคคล (PII/PDPA)
- ก่อน security gate ของ release ใหญ่ หรือเมื่อ audit/ลูกค้าร้องขอ

ถ้าระบบยังไม่เปลี่ยนสถาปัตยกรรมและทำ model ไว้แล้ว — รีวิวสั้น ๆ พอ ไม่ต้องเริ่มใหม่ทั้งหมด

## Input ที่ต้องถามก่อนเริ่ม

1. **ขอบเขต (scope):** กำลัง model ระบบไหน / feature ไหน / release ไหน — กันไม่ให้บานปลายทั้งองค์กร
2. **สถาปัตยกรรม:** มี solution design / sequence diagram / รายการ component และ integration ไหม (ดึงจาก /solution-design)
3. **Data ที่ไหล:** มี data ประเภทไหน (PII, credential, การเงิน, ความลับธุรกิจ) — เพื่อรู้ asset และระดับ classification
4. **Actor & trust:** ใครเรียกใช้บ้าง (anonymous, user ที่ login, admin, service-to-service, third party) แต่ละฝั่งเชื่อถือได้แค่ไหน
5. **เทคโนโลยี & deployment:** stack, cloud/on-prem, network zone, auth mechanism ที่ใช้
6. **Compliance & risk appetite:** มาตรฐานที่ต้องตาม (PDPA, ISO 27001, PCI-DSS) และระดับความเสี่ยงที่องค์กรรับได้

ถ้าข้อมูลไม่ครบ ให้สร้าง model จากสมมติฐานที่ดีที่สุด แล้ว **ทำรายการ assumption ชัด ๆ** เพื่อให้ทีมยืนยันภายหลัง อย่ารอจนข้อมูลครบ 100%

## ขั้นตอน (Playbook)

ยึด 4 คำถามของ Shostack เป็นกระดูกสันหลังตลอดทาง:

> **Q1 กำลังสร้างอะไร? · Q2 อะไรจะผิดพลาดได้? · Q3 จะทำอะไรกับมัน? · Q4 ทำได้ดีพอหรือยัง?**

**ขั้นที่ 1 — Model the system (ตอบ Q1):** ลิสต์ asset (ของมีค่าที่ผู้โจมตีอยากได้/อยากทำลาย เช่น customer PII, session token, เงิน), entry point / attack surface (ทุกจุดที่ input เข้าระบบ: API, form, file upload, queue, webhook, admin console) แล้ววาด **DFD** ด้วยองค์ประกอบ 4 ชนิด: External entity (วงรี/สี่เหลี่ยม), Process (วงกลม), Data store (เส้นคู่/กระบอก), Data flow (ลูกศร) จากนั้นลาก **trust boundary** (เส้นประ) คั่นทุกจุดที่ระดับความเชื่อถือเปลี่ยน เช่น Internet↔DMZ, app↔DB, service↔third-party

**ขั้นที่ 2 — Find threats (ตอบ Q2):** เดิน **STRIDE-per-element** ทีละองค์ประกอบของ DFD โดยจำคู่ภัย-คุณสมบัติที่ถูกละเมิด:

| ตัวอักษร | Threat | ละเมิดคุณสมบัติ | ใช้กับ element แบบไหน |
|---|---|---|---|
| **S** | Spoofing | Authentication | External entity, Process |
| **T** | Tampering | Integrity | Process, Data store, Data flow |
| **R** | Repudiation | Non-repudiation | External entity, Process |
| **I** | Information disclosure | Confidentiality | Process, Data store, Data flow |
| **D** | Denial of service | Availability | Process, Data store, Data flow |
| **E** | Elevation of privilege | Authorization | Process |

เน้น threat ที่ "ข้าม trust boundary" ก่อน เพราะนั่นคือจุดที่ assumption เรื่องความเชื่อถือพังได้ เสริมด้วย **abuse/misuse case** (เล่าจากมุมผู้โจมตี เช่น "ผู้โจมตีลอง credential stuffing บน login เพื่อ takeover บัญชี") และร่าง **attack tree** สั้น ๆ สำหรับ asset สำคัญ (root = เป้าหมาย เช่น "ขโมยเงินลูกค้า", กิ่ง = วิธีบรรลุ)

**ขั้นที่ 3 — Rank risk:** ให้คะแนนแต่ละ threat ด้วย **likelihood × impact** (เมทริกซ์ 3×3 / 5×5) หรือ DREAD (Damage, Reproducibility, Exploitability, Affected users, Discoverability) เมื่อต้องการความละเอียด สำหรับ threat ที่ผูกกับ CVE/แนว exploit รู้จัก ให้โยง **CVSS** เป็นตัวอ้างอิงความรุนแรง จัดลำดับเพื่อรู้ว่า "ทำอะไรก่อน" — อย่าพยายามแก้ทุกอย่างพร้อมกัน

**ขั้นที่ 4 — Decide & convert (ตอบ Q3):** แต่ละ threat ตัดสิน 1 ใน 4 ทาง: **Mitigate** (ใส่ control), **Eliminate** (ตัดฟีเจอร์/flow ออก), **Transfer** (ผลักให้ third party/ประกัน), **Accept** (รับความเสี่ยง โดยมีคนเซ็นรับ) แล้วแปลง mitigation ทุกตัวเป็น **security requirement** ที่ทดสอบได้ ส่งต่อ: requirement → /fr-nfr-spec, control ที่ต้อง verify → /security-testing และ /pentest-plan

**ขั้นที่ 5 — Validate (ตอบ Q4):** ทวนว่าทุก element ผ่าน STRIDE ครบ, ทุก threat มีการตัดสินใจ, ทุก mitigation มีเจ้าของ map กับ **OWASP Top 10** เพื่อกันหลุดประเด็นยอดฮิต บันทึก assumption + residual risk ที่ accept ไว้ และนัดรอบ review เมื่อสถาปัตยกรรมเปลี่ยน

## Output / Artifact (เทมเพลตพร้อมใช้)

> คัดลอกไปใช้แล้วเติมตามระบบจริงได้ทันที

### 1. DFD elements + trust boundaries

```
ระบบ: <ชื่อระบบ/ฟีเจอร์>   เวอร์ชัน: <vX.Y>   วันที่: <yyyy-mm-dd>   ผู้จัดทำ: <ชื่อ>

External entities : E1 ผู้ใช้ (browser/anonymous) · E2 Admin · E3 Payment Gateway (3rd party)
Processes         : P1 Web/API Gateway · P2 Auth Service · P3 Order Service
Data stores       : DS1 User DB (PII) · DS2 Session Store · DS3 Audit Log
Data flows        : DF1 E1→P1 HTTPS request · DF2 P2→DS1 query · DF3 P3→E3 charge API

Trust boundaries  :
  TB1  Internet  ↔  DMZ (E1/E3  ↔  P1)        — input ภายนอก ไม่เชื่อถือ
  TB2  DMZ       ↔  App tier (P1  ↔  P2/P3)
  TB3  App tier  ↔  Data tier (P*  ↔  DS*)
  TB4  ระบบเรา   ↔  3rd party (P3  ↔  E3)

Assets: A1 customer PII (DS1) · A2 session token (DS2) · A3 payment credential (DF3)
Assumptions: <เช่น TLS 1.2+ ทุก flow, WAF หน้า P1, secret อยู่ใน vault>
```

### 2. STRIDE-per-element table

| ID | Element | STRIDE | ภัย (threat scenario) | Likelihood×Impact | Mitigation (control) | Security requirement | OWASP | เจ้าของ |
|----|---------|--------|----------------------|-------------------|----------------------|----------------------|-------|---------|
| T-01 | DF1 (E1→P1) | **S** | ผู้โจมตีปลอม session/JWT เพื่อสวมรอยผู้ใช้ | สูง×สูง | ออก JWT พร้อม signature ตรวจ + หมดอายุสั้น + rotate key | "ทุก request ต้องผ่านการตรวจ token ที่ลายเซ็นถูกต้องและยังไม่หมดอายุ" | A07 Auth Failures | Backend |
| T-02 | P1 (Gateway) | **D** | flood request ทำให้ API ล่ม (DoS) | กลาง×สูง | rate limit + WAF + autoscale + circuit breaker | "API ต้อง rate-limit ต่อ IP/บัญชี และคืน 429 เมื่อเกิน" | A04 Insecure Design | Platform |
| T-03 | DS1 (User DB) | **I** | ดึง PII ผ่าน SQL injection ที่ P3 | กลาง×สูง | parameterized query + least-privilege DB user + encryption at rest | "ทุก query ต้อง parameterized; ห้าม string-concat input" | A03 Injection | Backend |
| T-04 | P3 (Order) | **E** | ผู้ใช้ปกติเรียก endpoint admin ได้ (broken access control) | สูง×สูง | enforce authz ราย`resource+action` ฝั่ง server, deny-by-default | "ทุก endpoint ตรวจสิทธิ์ฝั่ง server ก่อนทำงานทุกครั้ง" | A01 Broken Access Control | Backend |
| T-05 | DF3 (P3→E3) | **T** | แก้ยอดเงิน/ผู้รับระหว่างทางไป payment gateway | ต่ำ×สูง | mTLS + ลงลายเซ็น payload + ตรวจ webhook signature | "การเรียก gateway ต้องลงลายเซ็นและ verify ฝั่งรับ" | A08 Integrity Failures | Backend |
| T-06 | DS3 (Audit) | **R** | ผู้ใช้ปฏิเสธว่าไม่ได้ทำธุรกรรม เพราะ log ไม่พอ/แก้ได้ | กลาง×กลาง | audit log แบบ append-only + เก็บ actor/time/action + timestamp ที่เชื่อถือได้ | "ทุก action สำคัญต้องบันทึก audit ที่แก้ไม่ได้" | A09 Logging Failures | Backend |

### 3. ตารางจัดลำดับความเสี่ยง

| ID | Threat (ย่อ) | Likelihood (1–3) | Impact (1–3) | คะแนน (L×I) | ระดับ | การตัดสินใจ | สถานะ |
|----|-------------|:---:|:---:|:---:|---|---|---|
| T-04 | Broken access control | 3 | 3 | 9 | **Critical** | Mitigate | Open |
| T-01 | Token spoofing | 3 | 3 | 9 | **Critical** | Mitigate | Open |
| T-03 | SQLi → PII leak | 2 | 3 | 6 | High | Mitigate | In progress |
| T-02 | API DoS | 2 | 3 | 6 | High | Mitigate | Open |
| T-05 | Payment tampering | 1 | 3 | 3 | Medium | Mitigate | Open |
| T-06 | Repudiation | 2 | 2 | 4 | Medium | Mitigate | Open |

```
เกณฑ์ระดับ: 1–2 Low · 3–4 Medium · 6 High · 9 Critical
Residual risk ที่ Accept: <รายการ + ใครเซ็นรับ + วันที่ทบทวน>
```

## Checklist / Definition of Done

- [ ] ระบุ asset, entry point/attack surface และ actor พร้อมระดับ trust ครบ
- [ ] DFD มีองค์ประกอบครบ 4 ชนิด และลาก trust boundary ทุกจุดที่ trust เปลี่ยน
- [ ] เดิน STRIDE ครบ **ทุก element** (โดยเฉพาะ element ที่ข้าม boundary)
- [ ] มี abuse/misuse case อย่างน้อยต่อ asset สำคัญ
- [ ] ทุก threat มีคะแนนความเสี่ยง (L×I หรือ DREAD) และจัดลำดับแล้ว
- [ ] ทุก threat มี **การตัดสินใจ** (mitigate/eliminate/transfer/accept) — ไม่มี threat ที่ค้างไร้คำตอบ
- [ ] ทุก mitigation แปลงเป็น security requirement ที่ทดสอบได้ + ระบุเจ้าของ
- [ ] map OWASP Top 10 และ assumption/residual risk ที่ accept ถูกบันทึกพร้อมผู้เซ็นรับ
- [ ] ส่ง requirement ต่อ /fr-nfr-spec และ control ต่อ /security-testing, /pentest-plan แล้ว

## เคล็ดลับ & ข้อควรระวัง

- **เริ่มจาก trust boundary ก่อน:** threat ที่อันตรายสุดมักเกิดตรงที่ข้อมูลข้ามจาก "ไม่เชื่อถือ" ไป "เชื่อถือ" — โฟกัสตรงนั้นจะได้ของจริงเร็ว
- **อย่าทำ model สมบูรณ์แบบ:** DFD ที่ดีพอและ map เสร็จ มีค่ากว่า DFD สวยที่ทำไม่จบ ทำเป็น iteration
- **STRIDE-per-element ป้องกันการลืม:** ถ้านั่งนึกลอย ๆ จะมองข้าม จงไล่ตารางบังคับทุก element × ทุกตัวอักษร
- **threat ต้องสมจริง:** เขียนเป็น scenario ที่ผู้โจมตีทำได้จริงในระบบนี้ ไม่ใช่ทฤษฎี — ระบุ element, ขั้นตอน, ผลลัพธ์
- **ระวัง analysis paralysis กับ DREAD:** ถ้าทีมเถียงกันเรื่องคะแนนนาน ใช้ L×I แบบหยาบก่อน แล้วค่อยลงรายละเอียดเฉพาะ Critical/High
- **mitigation ที่ไม่มีเจ้าของ = ไม่เกิด:** ทุกแถวต้องมีคนรับผิดชอบและสถานะ ไม่งั้น threat model จะกลายเป็นเอกสารตาย
- **ทบทวนเมื่อ design เปลี่ยน:** เพิ่ม integration ใหม่ = trust boundary ใหม่ = ต้อง re-model ส่วนนั้น

## เชื่อมกับเฟสอื่น

- **ก่อนหน้า:** [/sod-matrix](#) — เมทริกซ์แยกหน้าที่ (separation of duties) ป้อนข้อมูล actor/role เข้ามาช่วยหา threat ฝั่ง authorization
- **ถัดไป:** [/dev-standards](#) — มาตรฐานการเขียนโค้ดที่ฝัง secure coding control จาก mitigation ที่ตัดสินใจไว้
- **ภาพรวมทั้งวงจร:** [/sdlc-agile](#) — ดูว่า threat modeling วางตรงไหนของ SDLC
- **ส่งงานต่อ:** security requirement → `/fr-nfr-spec` · control ที่ต้อง verify → `/security-testing` และ `/pentest-plan` · บริบทสถาปัตยกรรม ← `/solution-design`
- **ขอบเขตที่ไม่ทำในเฟสนี้:** การออกแบบ authentication/authorization ละเอียดอยู่ที่ `/authn-authz-design` และ `/sod-matrix`; การทดสอบเจาะจริงอยู่ที่ `/security-testing`, `/pentest-plan` — เฟสนี้แค่ "ระบุภัย + กำหนด requirement" ไม่ลงมือทดสอบ
