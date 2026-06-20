---
name: solution-design
description: ออกแบบสถาปัตยกรรมและโซลูชัน — สร้าง C4 diagram, เลือก architecture style, ออกแบบ data model (ERD), API contract, และบันทึก ADR; ครอบคลุมทั้ง HLD และ LLD (architecture & solution design covering C4 model, architecture-style selection, ERD, API design, and Architecture Decision Records). Trigger เมื่อผู้ใช้พิมพ์ /solution-design หรือขอ "ออกแบบสถาปัตยกรรม / architecture / system design / data model / ERD / API design / ADR / HLD / LLD".
category: sdlc
phase: "04 Solution Design"
---

# /solution-design — ออกแบบสถาปัตยกรรมและโซลูชัน (Architecture & Design)

แปลง requirement (FR/NFR + business logic) ให้กลายเป็น **สถาปัตยกรรมที่ตัดสินใจได้และสร้างได้จริง** — เลือก architecture style ตาม trade-off จริง, วาด C4 (Context→Container→Component), ออกแบบ data model (ERD) และ API contract (OpenAPI), แล้วบันทึกทุกการตัดสินใจสำคัญเป็น ADR เพื่อให้ทีมหลังบ้านสืบย้อน "ทำไมถึงเลือกแบบนี้" ได้

## ใช้ตอนไหน

- หลังจาก requirement + business logic นิ่งแล้ว (ผ่าน /fr-nfr-spec และ /business-logic-spec) และพร้อมเข้าสู่การออกแบบระบบ
- เริ่มโปรเจกต์ใหม่ / เพิ่ม subsystem ใหญ่ / รื้อสถาปัตยกรรม (re-platform, monolith→services)
- ต้องตัดสินใจเชิงสถาปัตยกรรมที่ "ย้อนยาก" (เลือก DB, sync vs async, style) และต้องการบันทึกเหตุผล
- ก่อนเริ่ม coding เพื่อให้ทีมมี HLD ร่วมกัน และก่อน sprint เพื่อทำ LLD ของ module ที่จะลงมือ

อย่าใช้เมื่อ: ยังไม่มี requirement ที่ชัด (กลับไป /req-discovery, /fr-nfr-spec ก่อน) หรือเป็นการ design เรื่อง **security เชิงลึก** โดยตรง (ไปเฟส security — ดูท้ายไฟล์)

## Input ที่ต้องถามก่อนเริ่ม

ถามให้ครบก่อนลงมือ ออกแบบบนสมมติฐานลอย ๆ คือบ่อเกิดของ rework:

1. **FR/NFR ที่ผ่านแล้ว** — ขอ list FR หลัก + NFR เชิงตัวเลข (เช่น RPS เป้าหมาย, p95 latency, availability SLA 99.9%, จำนวน user, data volume/growth)
2. **Quality attributes ที่สำคัญสุด 3 อันดับ** — scalability / availability / consistency / latency / maintainability / cost ตัวไหนมาก่อน (เลือกได้ไม่หมด — บังคับ trade-off)
3. **ข้อจำกัด (constraints)** — ทีม (ขนาด/ทักษะ), งบ, deadline, cloud/on-prem, ภาษา/เฟรมเวิร์กที่บังคับใช้, ระบบเดิมที่ต้อง integrate
4. **Data characteristics** — relational vs document, transactional vs analytical, ปริมาณ, ต้อง strong consistency ไหม, มี PII/ข้อมูลตามกฎหมายไทย (PDPA) หรือไม่
5. **Integration & external systems** — payment, SSO/IdP, third-party API, legacy, message queue ที่มีอยู่
6. **Boundary** — ขอบเขตที่จะออกแบบครั้งนี้ (ทั้งระบบ หรือ subsystem ใด)

ถ้าผู้ใช้ตอบไม่ครบ ให้ตั้งสมมติฐานชัด ๆ เขียนกำกับไว้ (Assumption) แล้วเดินต่อ อย่าค้าง

## ขั้นตอน (Playbook)

1. **ทวน driver** — สรุป FR หลัก + NFR เชิงตัวเลข + 3 quality attribute ที่สำคัญสุด ให้ผู้ใช้ยืนยัน เพราะทั้งหมดนี้คือเกณฑ์ตัดสินใจ design
2. **เลือก architecture style** — เทียบ style ที่เข้าข่าย (ดูตาราง trade-off ด้านล่าง) แล้วเลือกโดยอิงจาก quality attribute + constraint ที่ได้มา → ผลลัพธ์ต้องกลายเป็น **ADR ฉบับแรก**
3. **C4 Level 1 — Context** — ใครใช้ระบบ (actor), ระบบเราเป็นกล่องเดียว, เชื่อมกับ external system ใดบ้าง (มองจากนอก)
4. **C4 Level 2 — Container** — แตกระบบเป็น deployable/runnable units: web app, API, DB, cache, queue, worker, ระบุ tech + protocol ระหว่างกัน (นี่คือหัวใจของ HLD)
5. **C4 Level 3 — Component** — เจาะ container สำคัญ (เช่น API) เป็น component ภายใน (controller/service/repository/gateway) — เป็นส่วนของ LLD ทำเฉพาะ container ที่กำลังจะลงมือ
6. **Data model (ERD)** — ระบุ key entities, attributes, relationship, cardinality, PK/FK; ตัดสินใจ normalization (ปกติ 3NF แล้ว denormalize เฉพาะจุดที่มีเหตุผลด้าน read-performance)
7. **API contract** — เลือก REST/GraphQL/gRPC, ออกแบบ resource/operation, versioning, error format มาตรฐาน, แล้วร่าง **OpenAPI** สำหรับ endpoint หลัก
8. **Map NFR → design** — เปลี่ยน NFR แต่ละข้อเป็นกลไกออกแบบที่จับต้องได้ (ดูหัวข้อ "เชื่อม NFR" ในเคล็ดลับ) และเขียน ADR เพิ่มสำหรับทุกการตัดสินใจที่ย้อนยาก
9. **รวมเป็น HLD แล้วเจาะ LLD** — เอกสาร HLD (context+container+ADR+ERD+API ภาพรวม) สำหรับทุกคน; LLD (component+sequence+schema+ลายละเอียด field/validation) สำหรับ module ที่จะ code
10. **ส่งต่อ security** — ระบุจุดที่ต้อง authn/authz, trust boundary, ข้อมูล sensitive แล้ว **ส่งต่อให้เฟส security** ออกแบบต่อ (อย่าออกแบบเอง)

### เลือก architecture style — เกณฑ์ + trade-off

| Style | เหมาะเมื่อ | ข้อดี | ข้อเสีย / trade-off |
|---|---|---|---|
| **Monolith** | ทีมเล็ก, domain ยังไม่นิ่ง, MVP/เริ่มต้น | deploy/dev/test ง่าย, refactor ข้าม module ง่าย, ไม่มี network overhead, transaction เดียวจบ | scale ได้แค่ทั้งก้อน, deploy ทั้งหมดทุกครั้ง, codebase โตแล้วเปราะ, ผูกกับ stack เดียว |
| **Modular monolith** | ต้องการขอบเขต domain ชัดแต่ยังไม่อยากแบก distributed | boundary ชัดเหมือน services แต่ยัง deploy ก้อนเดียว, transaction ยังง่าย, แตกเป็น service ภายหลังได้ | ยังต้อง deploy รวม, ต้องมีวินัยรักษา module boundary ไม่ให้รั่ว |
| **Microservices** | domain นิ่ง+ใหญ่, หลายทีม, ต้อง scale/deploy อิสระต่อ service | scale เฉพาะส่วน, deploy อิสระ, เลือก stack ต่อ service, fault isolation | distributed complexity (network, eventual consistency, saga), ops หนัก (observability/CI-CD), latency เพิ่ม, debug ข้าม service ยาก |
| **Serverless (FaaS)** | โหลดไม่สม่ำเสมอ/เป็น spike, event-driven, อยากจ่ายตามใช้ | ไม่ต้องดูแล server, auto-scale ถึงศูนย์, จ่ายตามจริง | cold start, vendor lock-in, จำกัด runtime/timeout, debug/test local ยาก, แพงเมื่อ throughput สูงคงที่ |
| **Event-driven** | decouple producer/consumer, async workflow, audit/replay, สูง throughput | decoupling สูง, ทนต่อ load spike (buffer), ขยาย consumer ง่าย, รองรับ event sourcing | eventual consistency, debug/trace flow ยาก, ต้องจัดการ ordering/idempotency/duplicate, infra (broker) เพิ่ม |

หลักตัดสิน: **อย่าเลือก microservices เพราะมันเท่** — เริ่มที่ modular monolith เป็น default ถ้าไม่มีแรงผลัก (organizational scaling, independent deploy, scale ไม่เท่ากันรุนแรง) ที่ชัดเจน Style ผสมได้ (เช่น modular monolith + event-driven บางส่วน + serverless สำหรับงาน batch)

## Output / Artifact (เทมเพลตพร้อมใช้)

### 1) ADR — Architecture Decision Record (ลอกไปใช้ได้เลย)

```markdown
# ADR-001: <ชื่อการตัดสินใจ เช่น เลือก Modular Monolith เป็น architecture style>

- Status: Proposed | Accepted | Superseded by ADR-XXX | Deprecated
- Date: 2026-06-20
- Deciders: <ชื่อผู้ตัดสินใจ / ทีม>

## Context
<บริบทและแรงผลักของปัญหา: requirement/NFR ที่เกี่ยวข้อง, constraint (ทีม/งบ/เวลา),
สมมติฐาน, และ "ทำไมต้องตัดสินใจตอนนี้". เขียนกลาง ๆ ยังไม่บอกคำตอบ>

## Options Considered
1. <ทางเลือก A> — ข้อดี / ข้อเสีย
2. <ทางเลือก B> — ข้อดี / ข้อเสีย
3. <ทางเลือก C> — ข้อดี / ข้อเสีย

## Decision
<เราเลือก ... เพราะ ... (อ้าง quality attribute/constraint จาก Context อย่างชัดเจน)>

## Consequences
- เชิงบวก: <ได้อะไร>
- เชิงลบ / ราคาที่ต้องจ่าย: <trade-off, หนี้ที่ก่อ, สิ่งที่จะยากขึ้น>
- Follow-up: <งานที่ตามมา / เงื่อนไขที่จะทำให้ต้อง revisit>
```

> เก็บ ADR เป็นไฟล์ลำดับเลข `docs/adr/NNNN-title.md` หนึ่งการตัดสินใจ = หนึ่งไฟล์ ห้ามแก้ ADR ที่ Accepted แล้ว — ถ้าเปลี่ยนใจให้สร้างฉบับใหม่แล้วตั้ง Status เดิมเป็น `Superseded`

### 2) C4 Level 1 — System Context (โครงรายการ)

```markdown
## C4 Context: <ชื่อระบบ>
ระบบหลัก (system in scope): <ชื่อ> — <หน้าที่ 1 ประโยค>

Actors (ผู้ใช้/บทบาท):
- <Customer>        — <ทำอะไรกับระบบ>
- <Back-office>     — <ทำอะไร>
- <Admin>           — <ทำอะไร>

External systems (ระบบภายนอกที่เชื่อมด้วย):
- <Payment Gateway> — <ทิศทาง + จุดประสงค์ เช่น "ระบบ → ส่งคำขอชำระเงิน (HTTPS/REST)">
- <SSO / IdP>       — <"ระบบ → ตรวจ token (OIDC)">
- <Notification>    — <"ระบบ → ส่ง email/SMS">
```

> ขยายเป็น C4 Container ต่อโดยแตก "ระบบหลัก" ออกเป็น web/API/DB/cache/queue/worker พร้อม tech และ protocol ระหว่างกล่อง วาดจริงด้วย Mermaid `C4Context`/`C4Container` หรือ Structurizr DSL

### 3) API endpoint — ตารางสัญญา (เริ่มจากตารางนี้แล้วค่อยขยายเป็น OpenAPI)

| Method | Path | Auth | Request (body/params) | Response (200) | Error |
|---|---|---|---|---|---|
| GET | `/v1/orders` | Bearer | `?status=&page=&size=` | `{ data:[Order], page }` | 401, 403 |
| GET | `/v1/orders/{id}` | Bearer | path `id` | `Order` | 401, 404 |
| POST | `/v1/orders` | Bearer | `{ items:[{sku,qty}] }` | `Order` (201) | 400, 401, 422 |
| PATCH | `/v1/orders/{id}` | Bearer | `{ status }` | `Order` | 400, 401, 404, 409 |

**Error format มาตรฐาน (ใช้ทุก endpoint):**

```json
{ "error": { "code": "VALIDATION_ERROR", "message": "human readable", "details": [ { "field": "items[0].qty", "issue": "must be >= 1" } ], "traceId": "..." } }
```

**ร่าง OpenAPI (ตัวอย่าง endpoint เดียวให้ต่อยอด):**

```yaml
openapi: 3.0.3
info: { title: Orders API, version: "1.0.0" }
paths:
  /v1/orders/{id}:
    get:
      summary: Get order by id
      security: [ { bearerAuth: [] } ]
      parameters:
        - { name: id, in: path, required: true, schema: { type: string, format: uuid } }
      responses:
        "200": { description: OK, content: { application/json: { schema: { $ref: "#/components/schemas/Order" } } } }
        "404": { description: Not found }
components:
  securitySchemes:
    bearerAuth: { type: http, scheme: bearer, bearerFormat: JWT }
  schemas:
    Order:
      type: object
      required: [id, status, total]
      properties:
        id: { type: string, format: uuid }
        status: { type: string, enum: [pending, paid, shipped, cancelled] }
        total: { type: number }
```

> Versioning: เริ่มที่ URL path (`/v1/`) — ตรงไปตรงมาและ cache/route ง่าย; พิจารณา header-based เมื่อต้องการความยืดหยุ่นสูง ห้าม breaking change ใน v เดิม

### 4) ERD — Entity Relationship (โครง)

```markdown
## ERD: <ชื่อ domain>
Entity: Customer
  - id (PK, uuid)
  - email (unique, not null)
  - name
  - created_at
Entity: Order
  - id (PK, uuid)
  - customer_id (FK → Customer.id, not null)
  - status (enum: pending|paid|shipped|cancelled)
  - total (decimal)
  - created_at
Entity: OrderItem
  - id (PK, uuid)
  - order_id (FK → Order.id, not null)
  - sku
  - qty (int, > 0)
  - unit_price (decimal)

Relationships:
  - Customer 1 ──< Order        (one customer has many orders)
  - Order    1 ──< OrderItem    (one order has many items)
```

> วาดจริงด้วย Mermaid `erDiagram` ระบุ cardinality ให้ครบ (1:1, 1:N, M:N → ต้องมี join table) และระบุ index ที่จำเป็น (FK, คอลัมน์ที่ค้นบ่อย) ใน LLD

## Checklist / Definition of Done

- [ ] driver ชัด: FR หลัก + NFR เชิงตัวเลข + 3 quality attribute ที่สำคัญสุด ได้รับการยืนยัน
- [ ] เลือก architecture style แล้ว และมี **ADR** อธิบายเหตุผล + ทางเลือกที่ปัดตก + trade-off
- [ ] C4 Context ครบ (actor + external system ทุกตัว) และ C4 Container ครบ (ทุก deployable + protocol)
- [ ] C4 Component สำหรับ container ที่จะลงมือ (LLD)
- [ ] ERD: key entity + relationship + cardinality + PK/FK + เหตุผล normalization/denormalization
- [ ] API contract: resource, versioning, error format มาตรฐาน, ร่าง OpenAPI สำหรับ endpoint หลัก
- [ ] ทุก NFR สำคัญ map ไปยังกลไก design ที่จับต้องได้ (ไม่ลอย)
- [ ] ทุกการตัดสินใจ "ย้อนยาก" มี ADR กำกับ
- [ ] HLD (ภาพรวมสำหรับทุกคน) และ LLD (รายละเอียดสำหรับ module ที่จะ code) แยกชัด
- [ ] ระบุ trust boundary + จุด authn/authz + ข้อมูล sensitive ส่งต่อให้เฟส security แล้ว

## เคล็ดลับ & ข้อควรระวัง

- **HLD vs LLD**: HLD = "ภาพรวมระบบ" — style, container, ความสัมพันธ์ระหว่างระบบ, ADR, ERD/API ภาพรวม (audience: ทุกคน รวม non-dev); LLD = "ออกแบบภายใน module" — component, class/interface, sequence diagram, schema เต็ม, validation, algorithm (audience: dev ที่จะลงมือ) ทำ HLD ทั้งระบบก่อน แล้วทำ LLD เฉพาะ slice ที่กำลังจะ build (ไม่ต้อง LLD ล่วงหน้าทั้งระบบ — เปลือง และจะ outdated)
- **เชื่อม NFR → quality attribute → กลไก design** (อย่าให้ NFR ลอย): *scalability* → stateless service + horizontal scaling + cache + แตก write/read (CQRS เมื่อจำเป็น); *availability* → redundancy หลาย AZ + health check + retry/timeout + circuit breaker + graceful degradation; *latency* → cache layer, read replica, denormalize จุดร้อน, CDN; *consistency* → เลือก strong (ACID/transaction) เทียบ eventual (event-driven) อย่างจงใจต่อ use case; *maintainability* → boundary ชัด + dependency ทางเดียว
- **อย่า over-engineer**: เลือก style ตาม load จริง ไม่ใช่ตามแฟชั่น microservices/event-driven จ่าย "ภาษีความซับซ้อนแบบ distributed" (network failure, eventual consistency, debugging ข้ามระบบ) — จ่ายต่อเมื่อได้ประโยชน์คุ้ม
- **DB ตามรูปข้อมูล**: relational + ต้อง transaction/consistency → PostgreSQL; document/schema ยืดหยุ่น → MongoDB; key-value/cache → Redis; เลือกตาม access pattern อย่ายึด default เดียว
- **ออกแบบ failure ตั้งแต่ต้น**: ทุกการเรียกข้ามระบบต้องมี timeout/retry/idempotency; async ต้องคิด ordering + duplicate + dead-letter
- **บันทึก ADR ทันทีที่ตัดสินใจ** ไม่ใช่ย้อนเขียนทีหลัง — คุณค่าอยู่ที่ "บริบทตอนตัดสินใจ" ซึ่งจะลืม
- **ระวัง premature ERD lock**: ออกแบบ schema ให้รองรับ requirement ปัจจุบัน + ทิศที่ชัดเจน อย่าใส่ field/ตารางเผื่ออนาคตที่ยังไม่มีจริง

## เชื่อมกับเฟสอื่น

- **ก่อนหน้า**: `/business-logic-spec` — business rule + workflow ที่เป็น input ของ design (และต้นน้ำ: `/req-discovery`, `/fr-nfr-spec`)
- **ถัดไป**: `/authn-authz-design` — ออกแบบ authentication/authorization บน trust boundary ที่เฟสนี้ชี้ไว้
- **Security (อย่าออกแบบเองในเฟสนี้ ให้ส่งต่อ)**:
  - `/authn-authz-design` — identity, login, token, RBAC/ABAC
  - `/sod-matrix` — Segregation of Duties / แยกหน้าที่เชิงสิทธิ์
  - `/threat-model` — STRIDE/threat modeling บนสถาปัตยกรรมที่ออกแบบไว้
- **ปลายน้ำ**: `/dev-standards` (มาตรฐานโค้ดให้ตรง design), `/test-strategy` (กลยุทธ์ทดสอบตาม architecture), `/release-deploy`, `/observability` (ทำให้ NFR ที่ออกแบบไว้วัดได้จริง)
- **ภาพรวมทั้งวงจร**: `/sdlc-agile`
