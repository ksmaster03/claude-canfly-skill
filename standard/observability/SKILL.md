---
name: observability
description: วาง monitoring & observability หลัง deploy — สามเสา logs/metrics/traces, นิยาม SLI/SLO + error budget, golden signals, alerting และ incident management + runbook ให้ระบบ "บอกได้ว่าตอนนี้สุขภาพเป็นยังไง" และ "เมื่อพังจะรู้ก่อนลูกค้า". Trigger เมื่อผู้ใช้พิมพ์ /observability หรือขอ "monitoring / observability / logging / metrics / tracing / SLI / SLO / alerting / on-call / incident / runbook / เฝ้าระวังระบบ".
category: sdlc
phase: "14 Monitoring & Observability"
---

# /observability — Monitoring & Observability

วางระบบ "มองเห็นสุขภาพระบบ" หลัง deploy ขึ้น prod: สามเสา logs/metrics/traces นิยาม SLI/SLO + error budget, golden signals, alerting แบบ symptom-based, dashboard และ incident management + runbook ที่ on-call เปิดมาแล้วแก้ได้จริงตอนตี 3 เป้าหมายคือ **รู้ก่อนลูกค้า (detect) และซ่อมเร็ว (MTTR ต่ำ)** ไม่ใช่แค่ติดกราฟสวย ๆ

## ใช้ตอนไหน

- หลัง `/release-deploy` ส่งระบบขึ้น prod แล้ว ต้องการเฝ้าระวัง — เฟสนี้ **ไม่ deploy เอง** การ deploy อยู่ที่ `/release-deploy`
- ระบบมี dashboard แต่ alert เด้งมั่ว / alert fatigue / on-call ไม่รู้จะทำอะไรต่อ
- ต้องการนิยาม SLO กับลูกค้า/ผู้บริหาร แล้วผูกกลับไป NFR ที่ตั้งใน `/fr-nfr-spec`
- เกิด incident แล้วไม่มี runbook / postmortem เป็นการหาคนผิด ไม่ใช่หาสาเหตุ
- เพิ่ม service/endpoint ใหม่ ต้องเติม instrumentation + alert ก่อนถือว่า "เสร็จ"

## Input ที่ต้องถามก่อนเริ่ม

1. **Stack & scale** — ภาษา/เฟรมเวิร์ก, มี service กี่ตัว, sync/async, มี message queue/cron ไหม, traffic ระดับไหน (req/s)
2. **เครื่องมือที่มี/จะใช้** — metrics (Prometheus/CloudWatch/Datadog), logs (Loki/CloudWatch Logs/ELK), traces (OTel/Jaeger/Tempo/X-Ray), alerting (Alertmanager/PagerDuty/OpsGenie), dashboard (Grafana)
3. **NFR ที่ตกลงไว้** — availability เป้าเท่าไร, latency budget (p95/p99), throughput, จาก `/fr-nfr-spec`
4. **User journey วิกฤต** — flow ไหนคือ "เงินเข้า" / กระทบลูกค้ามากสุด (login, checkout, ค้นหา) → ใช้ตั้ง SLI
5. **ทีม on-call** — มีกี่คน, มี rotation ไหม, ช่องทางแจ้ง (Slack/LINE/โทร), เวลา response ที่รับได้
6. **ข้อจำกัด** — งบ, data retention, PDPA/ข้อมูลส่วนบุคคลใน logs (ห้าม log PII ดิบ)

## ขั้นตอน (Playbook)

1. **เลือก SLI จาก user journey ไม่ใช่จากเครื่อง** — เริ่มที่ "ลูกค้าเจ็บตรงไหน" แล้วแปลงเป็น SLI ที่วัดได้: availability (สัดส่วน request สำเร็จ), latency (p95/p99 ของ request ดี ๆ), error rate, freshness (สำหรับ data pipeline) — 1 journey ≈ 1-3 SLI พอ อย่าตั้งทุกอย่าง
2. **ตั้ง SLO + error budget** — SLO = เป้าของ SLI ในหน้าต่างเวลา (เช่น 99.9% ใน 30 วัน rolling) → error budget = 100% − SLO (99.9% = ดาวน์ได้ ~43 นาที/30 วัน) ใช้ budget เป็น "งบความเสี่ยง": budget เหลือ → ปล่อย feature ได้, budget หมด → freeze แล้วโฟกัสเสถียรภาพ
3. **วาง three pillars (instrumentation)**
   - **Logs** — structured (JSON) ทุกบรรทัด, log level ชัด (DEBUG/INFO/WARN/ERROR), ใส่ `trace_id`/`request_id`/`tenant` ทุก log เพื่อ correlate; ห้าม log PII/secret ดิบ
   - **Metrics** — time-series รวมเป็นตัวเลข ราคาถูก เก็บนาน เหมาะทำ alert/SLO; ตั้งชื่อ + label ให้สม่ำเสมอ (`http_request_duration_seconds{route,method,status}`)
   - **Traces** — distributed tracing (OpenTelemetry) ร้อย request เดียวข้ามหลาย service ด้วย trace context; ใช้หา "ช้าตรง hop ไหน"
   - ต่างจาก "monitoring" เดิม: monitoring ตอบ *known-unknowns* (ตั้ง dashboard/alert ของสิ่งที่รู้ล่วงหน้าว่าจะพัง); **observability** ให้ "ถามคำถามใหม่กับระบบได้โดยไม่ต้อง deploy โค้ดเพิ่ม" — ตอบ *unknown-unknowns* ด้วย high-cardinality data + ความสามารถ slice/dice ตามมิติใด ๆ (events ที่มี context ครบ)
4. **เลือก golden signals / RED / USE** — ดู §อ้างอิงด้านล่าง แล้ว instrument ให้ครบ 4 สัญญาณต่อ service
5. **ออกแบบ dashboard** — เรียงจากบนลงล่าง: SLO/error-budget สรุป → golden signals → dependency (DB/cache/queue) → resource; ทุกกราฟตอบ "คำถามเดียว" และมี threshold เส้น; แยก dashboard ระดับ service (debug) กับระดับ journey (สุขภาพธุรกิจ)
6. **เขียน alert แบบ symptom-based** — alert ที่ "ปลุกคน" ต้องผูกกับ SLO ที่ลูกค้ารู้สึก (เช่น error budget burn rate สูง, p99 latency เกิน) **ไม่ใช่ cause-based** (CPU 90% เฉย ๆ ที่ลูกค้าไม่เจ็บ → ทำเป็น ticket/warning ไม่ใช่ page); ทุก page ต้อง actionable + มี runbook link
7. **ตั้ง severity + on-call rotation + escalation** — ดูตาราง §Output; กำหนดว่าใครรับ, รับไม่ทันใน X นาที escalate ไปใคร
8. **เขียน runbook ต่อ alert** — อาการ → ตรวจอะไร (query/dashboard/log filter) → แก้อย่างไร → ถ้าแก้ไม่ได้ escalate ใคร; เก็บไว้ที่เดียว ลิงก์จาก alert
9. **วาง health check** — liveness (process ตายไหม → restart) แยกจาก readiness (พร้อมรับ traffic ไหม เช่น DB ต่อติด → ถอดออกจาก LB); อย่าให้ readiness fail ลามเป็น cascading restart
10. **ซ้อม incident loop** — detect → triage → mitigate → resolve → postmortem (blameless); วัด MTTD/MTTR แล้วเอา action item จาก postmortem กลับเข้า backlog (`/agile-delivery`)

## Output / Artifact (เทมเพลตพร้อมใช้)

### 1. ตาราง SLI / SLO + error budget

| Service / Journey | SLI (นิยามวัด) | เป้า SLO | หน้าต่างวัด | Error budget | แหล่งข้อมูล |
|---|---|---|---|---|---|
| Checkout API | availability = 2xx/3xx ÷ total req | 99.9% | 30 วัน rolling | ~43 นาที | metric `http_requests_total{status}` |
| Checkout API | latency = % req ที่ p95 < 300ms | 99% | 30 วัน rolling | 1% req ช้าได้ | histogram `http_request_duration_seconds` |
| Search | availability = สำเร็จ ÷ total | 99.5% | 30 วัน rolling | ~3.6 ชม. | metric |
| Order pipeline | freshness = order ถูก process < 5 นาที | 99% | 7 วัน rolling | 1% ของ order | queue lag metric |

> error budget ที่เหลือ = (SLO − SLI ปัจจุบัน) × ปริมาณ; budget หมด = freeze feature, โฟกัส reliability

### 2. เทมเพลต Alert definition

```yaml
alert: CheckoutHighErrorRate            # ชื่อสื่ออาการ ไม่ใช่ชื่อ metric
expr: |                                  # เงื่อนไข — symptom-based ผูก SLO
  ( sum(rate(http_requests_total{job="checkout",status=~"5.."}[5m]))
    / sum(rate(http_requests_total{job="checkout"}[5m])) ) > 0.02
for: 5m                                  # กันสัญญาณรบกวน ต้องค้างจริง
labels:
  severity: SEV2                         # อ้างตาราง severity
  team: payments
annotations:
  summary: "Checkout error rate > 2% (กิน error budget เร็ว)"
  impact: "ลูกค้าจ่ายเงินไม่ผ่าน — กระทบรายได้โดยตรง"
  runbook: "https://wiki/runbooks/checkout-high-error-rate"   # ต้องมีเสมอ
  dashboard: "https://grafana/d/checkout"
```

### 3. Incident runbook (ต่อ 1 alert)

```markdown
# Runbook: CheckoutHighErrorRate
**อาการ (Symptom):** error rate ของ /checkout > 2% นานเกิน 5 นาที; ลูกค้าจ่ายไม่ผ่าน

**ตรวจอะไร (Diagnose) — ไล่ตามลำดับ:**
1. เปิด dashboard checkout → ดู error แตกตาม `route`/`status`/`tenant`
2. trace: ค้น `trace_id` ของ req ที่ 5xx → ดูว่าพังที่ hop ไหน (DB? payment gateway?)
3. logs: filter `level=ERROR job=checkout` ช่วง 15 นาทีหลัง → หา exception ซ้ำ
4. เช็ค dependency: payment gateway health, DB connection pool, deploy ล่าสุด (rollback candidate?)

**แก้อย่างไร (Mitigate) — เอาเลือดหยุดก่อน หาสาเหตุทีหลัง:**
- ถ้าตรงกับ deploy ล่าสุด → rollback ผ่าน /release-deploy
- ถ้า gateway ล่ม → เปิด feature flag fallback / คิวไว้ retry
- ถ้า DB pool หมด → scale / เพิ่ม pool / ตัด query หนัก

**Escalate เมื่อ:** mitigate แล้ว 15 นาทีไม่ดีขึ้น หรือกระทบ > 5% ของ traffic → ปลุก secondary on-call + payments lead (ดูตาราง escalation)
```

### 4. ตาราง Severity / On-call / Escalation

| Severity | นิยาม (ผลกระทบลูกค้า) | ตอบสนอง | ใครรับ | Escalate ถ้าค้าง |
|---|---|---|---|---|
| SEV1 | ระบบล่มทั้งระบบ / ข้อมูลเสียหาย / รายได้หยุด | ทันที 24/7 page | Primary on-call | 15 นาที → Secondary + Eng lead + เปิด war room |
| SEV2 | feature หลักใช้ไม่ได้บางส่วน กระทบลูกค้าชัด | < 15 นาที | Primary on-call | 30 นาที → Secondary + team lead |
| SEV3 | กระทบเล็กน้อย มี workaround | ในเวลาทำงาน | ทีมเจ้าของ (ticket) | next business day |
| SEV4 | cosmetic / ไม่กระทบลูกค้า | backlog | ทีมเจ้าของ | — |

> **On-call:** rotation รายสัปดาห์, primary + secondary, ส่งมอบ handoff พร้อมสถานะ incident ค้าง; เฉพาะ SEV1/SEV2 เท่านั้นที่ "ปลุกคน" (page) — ที่เหลือเป็น ticket เพื่อกัน **alert fatigue**

## Checklist / Definition of Done

- [ ] ทุก critical journey มี SLI + SLO + error budget ที่ผูกกลับ NFR ใน `/fr-nfr-spec`
- [ ] ครบสามเสา: logs structured + correlation id, metrics มี label สม่ำเสมอ, traces ร้อยข้าม service
- [ ] ทุก service มี golden signals (หรือ RED/USE) ครบ 4 สัญญาณ
- [ ] dashboard มีชั้น SLO → golden signals → dependency → resource
- [ ] alert ทุกตัว symptom-based, actionable, มี severity + runbook link; ไม่มี cause-based alert ที่ "ปลุกคน" โดยลูกค้าไม่เจ็บ
- [ ] มี severity table + on-call rotation + escalation path ชัดเจน
- [ ] health check liveness/readiness แยกกัน ไม่ทำให้เกิด cascading restart
- [ ] ไม่มี PII/secret ดิบใน logs (PDPA)
- [ ] มี incident process (detect→triage→mitigate→resolve→postmortem blameless) + วัด MTTD/MTTR
- [ ] postmortem template พร้อม และ action item ไหลกลับ backlog

## เคล็ดลับ & ข้อควรระวัง

- **Golden signals (Google SRE):** latency, traffic, errors, saturation — ถ้าวัดได้แค่ 4 อย่างให้เลือก 4 อันนี้ (จาก *Site Reliability Engineering*, Google, บท Monitoring Distributed Systems) สำคัญ: แยก latency ของ request ที่ **สำเร็จ** ออกจากที่ **error** เพราะ error ที่ตอบเร็วทำให้ p95 ดูดีปลอม ๆ
- **RED** (สำหรับ request-driven service): Rate, Errors, Duration — มุมฝั่งผู้เรียก/บริการ
- **USE** (สำหรับ resource: CPU/disk/queue): Utilization, Saturation, Errors — มุมฝั่งทรัพยากร
- **Alert บน symptom ไม่ใช่ cause:** ปลุกคนเมื่อ "ลูกค้าเจ็บ" (SLO burn) ทุก page ที่ไม่ actionable คือหนี้ — ลบหรือลดเป็น ticket
- **Error budget เป็นเครื่องมือคุยกับธุรกิจ** ไม่ใช่ KPI ลงโทษ: budget เหลือ = กล้าปล่อยของ, budget หมด = หยุดเสี่ยง — เปลี่ยน "เสถียร vs เร็ว" จากการเถียงเป็นตัวเลข
- **Cardinality ระเบิดงบ:** label ที่มีค่าไม่จำกัด (user_id, request_id) ใน metrics ทำ time-series บวมมหาศาล — ของพวกนี้ไปอยู่ใน logs/traces ไม่ใช่ metric label
- **Blameless postmortem:** โฟกัส "ระบบ/กระบวนการปล่อยให้พลาดได้ยังไง" ไม่ใช่ "ใครผิด" — ไม่งั้นคนจะปิดข้อมูล แล้วเรียนรู้ไม่ได้
- **MTTD/MTTR:** ลด MTTD ด้วย alert ที่ดี (detect ก่อนลูกค้าโทรมา); ลด MTTR ด้วย runbook + ความสามารถ rollback เร็ว
- **อย่า over-alert ตอนเริ่ม:** เริ่มจาก SLO-based ไม่กี่ตัว แล้วค่อยเพิ่ม ดีกว่าเปิด 200 alert แล้วทุกคนปิดเสียงทิ้ง

## เชื่อมกับเฟสอื่น

- **ก่อนหน้า:** `/release-deploy` — deploy ขึ้น prod เสร็จแล้วถึงมาเฝ้าระวัง (การ deploy ทั้งหมดอยู่เฟสนั้น)
- **ผูกกลับ:** `/fr-nfr-spec` — SLO ทุกตัวต้อง trace กลับไปยัง NFR (availability/latency/throughput) ที่ตกลงไว้ตอนต้น
- **ป้อน action item ไปที่:** `/agile-delivery` — งานจาก postmortem/reliability เข้า backlog
- **ถัดไป:** — (จบวงจรของ increment นี้) เมื่อเริ่ม increment ใหม่ให้วนกลับ `/agile-delivery` แล้ว `/req-discovery`
- **ภาพรวมทั้งวงจร:** `/sdlc-agile`
