---
name: release-deploy
description: วาง deployment และ release management ระดับ production — CI/CD pipeline, กลยุทธ์ deploy (rolling/blue-green/canary/feature flag), environment promotion, IaC, change management, rollback plan และ release checklist (CI/CD pipeline, deployment strategies, environment promotion, infrastructure as code, change/release management, backout plan, release checklist). Trigger เมื่อผู้ใช้พิมพ์ /release-deploy หรือขอ "deploy / deployment / CI/CD / release / blue-green / canary / rollback / change management / IaC / ปล่อยระบบ / runbook deploy".
category: sdlc
phase: "13 Deployment & Release"
---

# /release-deploy — Deployment & Release Management

ออกแบบและคุมการปล่อยซอฟต์แวร์ขึ้น production อย่างปลอดภัยและกลับคืนได้ — ตั้งแต่ CI/CD pipeline, การเลื่อนระดับข้าม environment, การเลือก deployment strategy ที่เหมาะกับ risk profile, ไปจนถึง change management และ rollback ที่ซ้อมแล้ว ทำงานในระดับ release manager / senior DevOps ที่ "deploy ได้บ่อย เจ็บน้อย กลับได้ไว".

## ใช้ตอนไหน
- ต้องวาง CI/CD pipeline ใหม่ หรือเพิ่ม gate/stage ให้ pipeline เดิม
- ต้องเลือกกลยุทธ์ deploy (recreate / rolling / blue-green / canary / feature flag) สำหรับ service หนึ่ง
- เตรียมปล่อย release ที่มีความเสี่ยง (schema change, breaking API, traffic สูง) และต้องการ runbook + rollback plan
- ต้องผ่าน change management — เปิด change request, จอง maintenance window, แจ้ง stakeholder
- ออกแบบ environment promotion (dev → test → staging → prod) และการจัดการ config/secret แยกต่อ env
- ต้องการ release checklist / release notes / versioning policy ที่ใช้ซ้ำได้

## Input ที่ต้องถามก่อนเริ่ม
1. **ระบบ & สถาปัตยกรรม** — monolith/microservice, จำนวน service, stateful ไหม (DB, queue, cache), runtime (k8s / VM / serverless / on-prem)
2. **ความถี่และความเสี่ยงการปล่อย** — deploy บ่อยแค่ไหน, downtime ที่ยอมรับได้ (zero-downtime?), peak traffic window, SLA/SLO
3. **Pipeline & tooling ปัจจุบัน** — CI ที่ใช้ (GitHub Actions/GitLab/Jenkins/ArgoCD), registry, IaC tool (Terraform/Pulumi/CFN/Helm)
4. **Environment ที่มี** — มีกี่ env, อะไร gate การ promote, ใครอนุมัติ
5. **Database / migration** — มี schema change ไหม, รองรับ backward-compatible ได้ไหม, ขนาดข้อมูล/เวลา migrate
6. **Change governance** — มี CAB/change window ไหม, ใครเป็น approver, มีข้อบังคับ compliance (PDPA/ISO/SOC2) ไหม
7. **Rollback ปัจจุบัน** — กลับ version ได้ยังไง, เคยซ้อม rollback ไหม, RTO ที่ต้องการ

> ถ้าข้อมูลไม่ครบ ให้ตั้งสมมติฐานที่ระบุชัด (เช่น "สมมติ k8s + zero-downtime") แล้วเขียนกำกับไว้ใน output อย่า block งาน

## ขั้นตอน (Playbook)
1. **จัดประเภท release** — แยกว่าเป็น standard (ทำซ้ำ ความเสี่ยงต่ำ, pre-approved), normal (ต้องอนุมัติ), หรือ emergency (hotfix) — ระดับนี้กำหนดความเข้มของ gate และ change process
2. **ออกแบบ CI/CD pipeline** — เรียง stage: `build → unit/integration test → security scan → package/artifact → deploy-to-staging → smoke/acceptance → promote-to-prod`
   - ทุก stage มี **gate** ชัดเจน (pass/fail criteria) และ fail-fast
   - artifact **build ครั้งเดียว** แล้ว promote ตัวเดิมข้าม env (immutable artifact) — ห้าม rebuild ต่อ env
   - แยก **test gate** (อ้าง /regression-suite) และ **security scan gate** (อ้าง /security-testing) อย่างชัดเจน
3. **กำหนด environment & config strategy** — dev/test/staging/prod; staging ต้อง "production-like"; config/secret แยกต่อ env ผ่าน env var / secret manager (Vault, SSM, Secrets Manager) — **ห้าม hardcode secret ใน artifact หรือ repo**
4. **เลือก deployment strategy ตาม risk** — ดูตาราง trade-off ด้านล่าง แล้ว match กับ SLA/stateful/traffic
5. **วาง IaC & immutable infra** — โครงสร้างพื้นฐานทั้งหมดเป็นโค้ด (review ได้, reproduce ได้), deploy ด้วยการ "เปลี่ยน image/instance ทั้งก้อน" แทนการแก้ของเดิมในที่ (no SSH-and-patch)
6. **ออกแบบ DB migration ให้ปลอดภัย** — ใช้ **expand-contract**: (a) expand เพิ่ม column/table แบบ backward-compatible ก่อน → (b) deploy โค้ดที่เขียนทั้งเก่า/ใหม่ → (c) backfill ข้อมูล → (d) สลับให้อ่านจากใหม่ → (e) contract ลบของเก่าใน release ถัดไป — แยก migration ออกจาก deploy ของแอป เพื่อให้ rollback แอปได้โดยไม่ติด schema
7. **เขียน rollback / backout plan** — กำหนด trigger (error rate, latency, business KPI), วิธีกลับ (สลับ blue-green, ลด canary weight, ปิด feature flag, redeploy previous artifact), และจุดที่ rollback ไม่ได้ (irreversible migration → ต้องมี forward-fix plan)
8. **ผ่าน change management** — เปิด change request, ขออนุมัติ/CAB ตามระดับ release, จอง maintenance window, ร่าง comms ถึง stakeholder ทั้งก่อน/หลัง
9. **กำหนด versioning & release notes** — ใช้ **semver** (MAJOR.MINOR.PATCH; MAJOR = breaking), tag git, เขียน release notes (feature/fix/breaking/known-issue)
10. **ปล่อยตาม runbook + เฝ้าระวัง** — รัน runbook step-by-step, monitor ตาม metric ที่ /observability กำหนด, ตัดสิน promote/rollback ตาม gate, แล้วปิด change + บันทึก

### ตาราง trade-off กลยุทธ์ deploy
| Strategy | กลไก | Downtime | Rollback | Cost (infra) | เลือกเมื่อ |
|---|---|---|---|---|---|
| **Recreate** | ดับเก่าหมด ค่อยขึ้นใหม่ | มี | redeploy เก่า (ช้า) | ต่ำ | dev/internal, ยอม downtime, stateful ที่รัน 2 version พร้อมกันไม่ได้ |
| **Rolling** | ทยอยเปลี่ยนทีละ batch | ~0 | ทยอยกลับ (ช้ากว่า BG) | ต่ำ | ค่า default ของ k8s, service ที่ backward-compatible |
| **Blue-Green** | ยกชุดใหม่คู่ขนาน แล้วสลับ traffic | 0 | สลับกลับทันที (เร็วสุด) | สูง (2 เท่า) | ต้องการ rollback ทันที, release เสี่ยง, มี budget infra |
| **Canary** | ปล่อยให้ traffic ส่วนน้อย → ค่อยเพิ่ม | 0 | ลด weight = กลับเร็ว | กลาง | traffic สูง, อยากวัด real impact ก่อนปล่อยเต็ม, มี metric/automation ดี |
| **Feature flag** | deploy ปิดไว้ → เปิดทีหลังด้วย flag | 0 | ปิด flag (ไม่ต้อง redeploy) | ต่ำ | แยก deploy ออกจาก release, A/B, ปล่อยเฉพาะกลุ่ม, kill switch |

> หลักเลือก: **stateful + version ชนกันไม่ได้ → recreate/blue-green** · **ต้อง rollback ทันที → blue-green/flag** · **ต้องวัด real impact → canary** · **อยาก decouple deploy จาก release → feature flag** (มักใช้ canary/BG + flag ร่วมกัน)

## Output / Artifact (เทมเพลตพร้อมใช้)

### 1) Release Runbook (step-by-step)
```markdown
# Release Runbook — <service> v<X.Y.Z>
Release type: [standard | normal | emergency]   Strategy: [blue-green | canary | rolling]
Change ID: CHG-____   Window: <date time TZ>   Duration (est): __ min
Release manager: ____   On-call: ____   Approver: ____

## Pre-deploy (T-30m)
- [ ] CI เขียวครบ: build / test gate (/regression-suite) / security scan (/security-testing)
- [ ] Artifact v<X.Y.Z> มีใน registry + digest ตรง (immutable, promote ตัวเดิมจาก staging)
- [ ] Verified บน staging (production-like) + smoke test ผ่าน
- [ ] DB migration plan review แล้ว (expand-contract, backward-compatible) + backup/snapshot ล่าสุด
- [ ] Rollback plan ยืนยัน + ซ้อม/รู้คำสั่ง · feature flag/kill switch พร้อม
- [ ] แจ้ง stakeholder ว่า window กำลังจะเริ่ม

## Deploy
1. [ ] (ถ้ามี) รัน DB migration ส่วน expand → ตรวจสำเร็จ
2. [ ] Deploy artifact ตาม strategy:
       - blue-green: ยก green ขึ้น → health check green → สลับ router ไป green
       - canary: ปล่อย 5% → เฝ้า 10 นาที → 25% → 50% → 100% (gate ทุกขั้น)
3. [ ] Smoke test เส้นทางหลัก (login / checkout / API health) บน prod
4. [ ] เฝ้า metric (อ้าง /observability): error rate, p95 latency, saturation, business KPI

## Post-deploy (T+30m)
- [ ] Metric อยู่ในเกณฑ์ (ไม่เกิน gate) ต่อเนื่อง ≥30 นาที
- [ ] ปิด/เก็บ blue เดิมไว้ตามเวลาที่กำหนด (ยังไม่ทำลายทันทีเผื่อ rollback)
- [ ] รัน migration ส่วน contract (ถ้าถึงรอบ) · อัปเดต release notes + tag git
- [ ] ปิด change request + แจ้ง stakeholder ว่าเสร็จ

## Rollback trigger
ถ้า error rate > __% หรือ p95 > __ ms นานเกิน __ นาที หรือ smoke test fail → execute Rollback Plan ทันที
```

### 2) Rollback / Backout Plan
```markdown
# Rollback Plan — <service> v<X.Y.Z> (from v<prev>)
Trigger (ใดข้อหนึ่ง): error rate > __%  |  p95 latency > __ ms  |  health check fail  |  business KPI ลด > __%
Decision owner: ____ (สิทธิ์ตัดสินกลับโดยไม่ต้องประชุม)   RTO เป้าหมาย: __ นาที

## ขั้นตอนกลับ (ตาม strategy)
- blue-green: สลับ router กลับไป blue (artifact เดิม) — ~ทันที
- canary: ตั้ง weight ใหม่ = 0% / route 100% กลับ stable
- feature flag: ปิด flag <flag-name> (ไม่ต้อง redeploy)
- rolling/recreate: redeploy artifact v<prev>

## DB consideration
- migration นี้ backward-compatible หรือไม่: [ใช่ → กลับโค้ดได้เลย | ไม่ → ใช้ forward-fix เท่านั้น]
- ถ้า irreversible: ระบุ forward-fix plan + จุด backup/restore สุดท้าย: ____

## Verify หลังกลับ
- [ ] เวอร์ชันที่รันคือ v<prev>  - [ ] smoke test ผ่าน  - [ ] metric กลับสู่ baseline
- [ ] แจ้ง stakeholder + เปิด incident/post-mortem
```

### 3) Deployment / Release Checklist (Definition of Done — ดูหัวข้อถัดไป)

### 4) Change Request
```markdown
# Change Request — CHG-____
Title: <สิ่งที่จะเปลี่ยน>            Type: [standard | normal | emergency]   Risk: [low|med|high]
Requested by: ____   Approver/CAB: ____   Scheduled window: <date time TZ> (duration __)
Systems affected: ____            User impact / downtime: ____
Description: <ทำอะไร ทำไม>
Implementation plan: <ref: Release Runbook>
Backout plan: <ref: Rollback Plan>      Validation/test evidence: <staging result, CI run #>
Comms plan: แจ้งใคร / ช่องทางไหน / เมื่อไหร่ (ก่อน-หลัง)
Approval: [ ] อนุมัติ  [ ] ปฏิเสธ   โดย ____ วันที่ ____
```

## Checklist / Definition of Done
- [ ] เลือก deployment strategy พร้อมเหตุผล match กับ risk/SLA/stateful แล้ว
- [ ] Pipeline มี gate ครบ: build, test (/regression-suite), security scan (/security-testing), artifact, deploy, smoke
- [ ] Artifact build ครั้งเดียว + promote ตัวเดิมข้าม env (immutable) — ไม่ rebuild ต่อ env
- [ ] Config/secret แยกต่อ env ผ่าน secret manager — ไม่มี secret ใน repo/artifact
- [ ] Infra เป็น IaC, review ได้, deploy แบบ immutable (เปลี่ยนทั้งก้อน ไม่ patch in-place)
- [ ] DB migration เป็น backward-compatible (expand-contract) และแยกจาก deploy แอป
- [ ] Rollback/backout plan เขียนชัด + ระบุ trigger + (ถ้าทำได้) ซ้อมแล้ว
- [ ] Change request เปิด/อนุมัติ + maintenance window จอง + comms plan พร้อม
- [ ] Release notes + version (semver) + git tag ครบ
- [ ] Release runbook พร้อม owner/on-call และ metric ที่จะเฝ้า (ส่งต่อ /observability)

## เคล็ดลับ & ข้อควรระวัง
- **Deploy ≠ Release** — แยกการ "เอาโค้ดขึ้น" ออกจากการ "เปิดให้ผู้ใช้เห็น" ด้วย feature flag จะลดความเสี่ยงมหาศาล (rollback = ปิด flag ไม่ต้อง redeploy)
- **Migration ที่ลบ/แก้ column ทันทีพร้อม deploy = กับดัก rollback** — ถ้ากลับโค้ดแต่ schema เปลี่ยนไปแล้วจะพังหนักกว่าเดิม ยึด expand-contract เสมอ
- **rebuild artifact ต่อ env** ทำให้ "ของที่ทดสอบบน staging ≠ ของที่ขึ้น prod" — promote artifact เดิมเท่านั้น
- **canary ที่ไม่มี automated metric gate = แค่ปล่อยช้า ๆ** — ต้องมีเกณฑ์ auto-rollback ไม่งั้น human จะตัดสินช้าเกินไป
- **blue-green กิน infra 2 เท่า** และ DB shared ระหว่าง blue/green ทำให้ migration ต้อง backward-compatible อยู่ดี — blue-green ไม่ช่วยเรื่อง schema
- **อย่าทำลาย environment เก่าทันที** — เก็บ blue/previous artifact ไว้จนมั่นใจ (เช่น 30–60 นาที) เผื่อ rollback
- **emergency change ก็ต้องมี backout plan** — hotfix ที่ไม่มีทางกลับคือ incident ซ้อน incident
- **staging ต้อง production-like จริง** (data shape, scale, config) ไม่งั้น smoke test ผ่านก็เชื่อไม่ได้
- **secret ต้องหมุนได้** และไม่ผูกติด artifact — ใช้ inject ตอน runtime จาก secret manager

## เชื่อมกับเฟสอื่น
- **ก่อนหน้า:** /pentest-plan — ผลทดสอบเจาะระบบต้องเคลียร์ก่อนตั้ง release gate
- **ถัดไป:** /observability — runbook ส่งต่อ metric/alert ที่ต้องเฝ้าหลัง deploy เพื่อตัดสิน promote/rollback
- **ภาพรวมทั้งวงจร:** /sdlc-agile
- **อ้างอิงข้าม:** test gate ใน pipeline → /regression-suite · security scan ใน pipeline → /security-testing · เฝ้าระวังหลัง deploy → /observability
