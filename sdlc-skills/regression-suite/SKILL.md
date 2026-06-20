---
name: regression-suite
description: วางการทดสอบ regression และ non-regression — กันของเดิมพังเมื่อมีการแก้ไข, ทำ change impact analysis, คัดชุด regression แบบ risk-based, วาง automation และ smoke/sanity. Plan regression & non-regression testing to prevent breaking existing behavior on changes, run change impact analysis, select risk-based regression sets, and design automation + smoke/sanity. Trigger เมื่อผู้ใช้พิมพ์ /regression-suite หรือขอ "regression test / non-regression / impact analysis / smoke test / sanity / test automation / กันของเดิมพัง / regression suite".
category: sdlc
phase: "10 Regression Testing"
---

# /regression-suite — Regression & Non-regression Testing

ออกแบบและบำรุงรักษา "ตาข่ายความปลอดภัย" (safety net) ที่ยืนยันว่าโค้ดเดิมยังทำงานถูกหลังมีการแก้ไข โดยใช้ change impact analysis เลือกชุดทดสอบแบบ risk-based แล้ววาง automation + smoke/sanity ให้รันได้ใน CI/CD จริง. เน้นเฟส regression เท่านั้น — กลยุทธ์ทดสอบภาพรวมอยู่ที่ `/test-strategy`, pipeline อยู่ที่ `/release-deploy`.

## ใช้ตอนไหน
- มีการแก้บั๊ก / เพิ่มฟีเจอร์ / refactor / อัป dependency / merge branch แล้วต้องมั่นใจว่า "ของเดิมไม่พัง"
- ก่อน release / hotfix และต้องตัดสินใจว่าจะรัน regression แค่ไหน (เวลาจำกัด)
- suite ทดสอบโตจนรันช้า/flaky และต้องคัด-จัดลำดับ-ตัดทิ้งใหม่
- ต้องตอบทีม/ผู้บริหารว่า "การเปลี่ยนนี้กระทบอะไรบ้าง และเราทดสอบครอบคลุมพอไหม"
- จะวาง regression automation เข้า CI (per-PR / nightly / pre-release)

> **regression vs non-regression — แยกให้ชัด**
> - **Regression testing** = รันชุดทดสอบ "ของเดิม" ซ้ำ หลังมีการเปลี่ยน (fix/feature/refactor) เพื่อยืนยันว่าฟังก์ชันที่เคยทำงานได้ *ยังทำงานได้อยู่* — โฟกัสที่ "ตรวจจับ regression bug" (ของที่เคยดีแล้วพังเพราะการแก้ที่อื่น).
> - **Non-regression testing (NRT)** = พิสูจน์เชิงยืนยันว่าการเปลี่ยน *ไม่ได้ทำให้พฤติกรรมเดิมเปลี่ยน* นอกขอบเขตที่ตั้งใจ — มักทำกับ refactor/migration/perf-tuning ที่ "output ต้องเหมือนเดิมเป๊ะ". เทคนิคหลักคือ baseline comparison: golden master / snapshot / approval test, diff response เก่า-ใหม่, หรือ characterization test ของ legacy.
> - **เส้นแบ่งเชิงปฏิบัติ:** regression ถาม "ยังผ่าน assertion เดิมไหม"; non-regression ถาม "ผลลัพธ์/พฤติกรรม *ต่างจาก baseline* ตรงไหนบ้าง แล้วความต่างนั้น *ตั้งใจ* หรือไม่". เมื่อ feature เปลี่ยน behavior โดยตั้งใจ → ต้องอัป baseline/expected (intended change) ไม่ใช่นับเป็น fail.

## Input ที่ต้องถามก่อนเริ่ม
1. **ขอบเขตการเปลี่ยน:** diff/PR/commit, โมดูลที่แตะ, เป็น fix / feature / refactor / config / dependency-bump?
2. **สถาปัตยกรรม & coupling:** อะไรเรียกอะไร (shared service, DB, API contract, event/queue, feature flag) — มี dependency map ไหม
3. **ทรัพย์สินทดสอบที่มีอยู่:** มี test ระดับไหนบ้าง (unit/integration/e2e), coverage, suite ปัจจุบันรันที่ไหน-นานเท่าไร, framework
4. **เวลา & ความเสี่ยง:** หน้าต่าง release, ระดับความเสี่ยงของพื้นที่ที่แตะ (payment/auth = สูง), มี SLA/compliance ไหม
5. **Baseline สำหรับ NRT:** มี golden/snapshot ไหม, อนุญาตเทียบ prod traffic (shadow/replay) ได้ไหม
6. **CI/CD & flaky:** trigger ปัจจุบัน (per-PR/nightly), อัตรา flaky, quarantine มีหรือยัง

## ขั้นตอน (Playbook)
1. **ระบุการเปลี่ยน (delta):** ดึงรายการไฟล์/โมดูล/endpoint/schema ที่แก้จาก diff. แยกประเภทเพราะกำหนดกลยุทธ์: bug-fix (เพิ่ม test ดักเคสที่พลาด), feature (อาจต้องอัป baseline), refactor/migration (เน้น non-regression baseline comparison).
2. **Change Impact Analysis:** ไล่จาก delta ออกไปยังสิ่งที่ "กระทบทางอ้อม" — caller/dependent, shared util, API/contract consumer, data ที่ไหลต่อ, feature flag. แยก **direct impact** (โค้ดที่แก้) กับ **ripple/indirect impact** (สิ่งที่พึ่งพา). map ออกมาเป็นตาราง (เทมเพลตด้านล่าง). ใช้ coverage data / call graph / dependency graph ช่วยถ้ามี.
3. **เลือกกลยุทธ์คัดชุด (selection):**
   - **Retest-all** — รันทั้ง suite. ใช้เมื่อเปลี่ยนกระทบวงกว้าง (core/shared lib, framework upgrade) หรือ suite เร็วพอ. ปลอดภัยสุดแต่แพง.
   - **Selective / Regression Test Selection (RTS)** — รันเฉพาะ test ที่แมพกับโค้ดที่เปลี่ยน (จาก impact map / coverage-based). ลดเวลา แต่เสี่ยงพลาดถ้า map ไม่ครบ → กันด้วย full run nightly.
   - **Test-case prioritization (TCP)** — ไม่ตัดออก แต่ "จัดลำดับ" ให้ test เสี่ยงสูง/เคยเจอบั๊ก/ครอบคลุมพื้นที่ที่แตะ รันก่อน เพื่อเจอ fail เร็ว (fail-fast) ในเวลาจำกัด.
   - แนวปฏิบัติจริง: ผสม — per-PR ใช้ selective+prioritized (เร็ว), nightly/pre-release ใช้ retest-all (ครอบคลุม).
4. **จัด smoke & sanity ให้ถูกชั้น:**
   - **Smoke test** — ชุดสั้นมาก กว้างแต่ตื้น ("build ยังหายใจไหม"): app ขึ้นได้, login, health endpoint, critical happy-path 5–15 เคส. รันก่อนทุกอย่างเป็น gate — fail = หยุด ไม่ต้องรัน regression เต็ม.
   - **Sanity test** — แคบแต่ลึก เจาะเฉพาะพื้นที่/ฟังก์ชันที่เพิ่งแก้ ว่า "ส่วนที่แก้ทำงานสมเหตุผลไหม" ก่อนลงทุนรัน regression เต็ม. มัก ad-hoc/unscripted หลัง build ใหม่.
   - ลำดับ: smoke (gate) → sanity (พื้นที่ที่แตะ) → regression (impact set) → full (nightly).
5. **วาง/อัปเดต non-regression baseline:** เลือกเทคนิคให้เข้ากับงาน — snapshot/approval test (UI, API response), golden master (output ไฟล์/รายงาน), diff-testing/replay (เทียบ response prod เก่า vs ใหม่บน traffic จริง). กำหนดกติกาชัดว่า "เมื่อ behavior เปลี่ยนโดยตั้งใจ → อัป baseline พร้อม review/justify ใน PR" ไม่ใช่กด accept มั่ว.
6. **วาง automation strategy:** ตัดสินใจว่าเคสไหน automate (เกณฑ์ candidacy ด้านล่าง), เคสไหนคง manual. กระจายตาม test pyramid (unit เยอะ, e2e น้อยแต่คุ้ม), idempotent + ข้อมูลทดสอบ self-managed, hook เข้า CI ตาม trigger (per-PR = smoke+selective, nightly = full+e2e).
7. **จัดการ flaky test:** ตั้งกติกา detect (รันซ้ำ/ดู pass-rate), **quarantine** (ย้ายออกจาก gate ไม่ให้ block แต่ยังรันเก็บสถิติ), ตั้ง owner + กำหนดเวลาแก้ (ห้าม quarantine ค้างถาวร), ห้าม blanket-retry กลบปัญหา. flaky กัดกร่อนความเชื่อใจใน suite — ถือเป็นบั๊กของ test.
8. **บำรุงรักษา suite:** ลบ/รวม test ซ้ำซ้อนและล้าสมัย (dead test ที่ assert ฟีเจอร์ที่ถูกถอด), จัด tag/หมวด (`@smoke @critical @slow`), วัด value (เคยจับบั๊กไหม) เพื่อตัดสิน keep/cut, รีวิว coverage ของพื้นที่เสี่ยงสูง.
9. **สรุป & gate:** ออก regression report (อะไรรัน, ผล, อะไร quarantine, ความเสี่ยงที่เหลือ) ให้เป็น go/no-go input ของ release.

## Output / Artifact (เทมเพลตพร้อมใช้)

**1) ตาราง Change Impact Analysis** — เปลี่ยนอะไร → กระทบโมดูลไหน → ต้องรัน test อะไร
```markdown
| # | สิ่งที่เปลี่ยน (file/module/endpoint) | ประเภท (fix/feat/refactor) | Direct impact | Ripple / indirect impact | พื้นที่เสี่ยง (H/M/L) | Test ที่ต้องรัน (id/tag) | Baseline ต้องอัป? |
|---|---|---|---|---|---|---|---|
| 1 | auth/token.service.ts | refactor | login, refresh | ทุก endpoint ที่ใช้ guard, session store | H | TS-AUTH-*, @smoke | ไม่ (behavior เดิม) |
| 2 | order/discount.ts (rule ใหม่) | feat | คำนวณราคา order | invoice, รายงานยอดขาย, cart total | H | TS-ORDER-PRICE-*, TS-INVOICE-* | ใช่ (snapshot ราคา) |
| 3 | bump lib X 2.x→3.x | dep | ทุกที่ที่ import X | serialization, date parsing | M | retest-all (nightly) | ตรวจ diff response |
```

**2) Regression Suite Catalog** — รายการ test / พื้นที่ / priority / automated?
```markdown
| Test ID | ชื่อ/พฤติกรรมที่ยืนยัน | พื้นที่/โมดูล | ระดับ (unit/int/e2e) | Priority (P1–P3) | Automated? | Tag | Trigger (PR/nightly/release) | Owner |
|---|---|---|---|---|---|---|---|---|
| TS-AUTH-001 | login สำเร็จด้วย cred ถูกต้อง | Auth | e2e | P1 | ✅ | @smoke @critical | PR | qa-a |
| TS-ORDER-PRICE-014 | ส่วนลด + ภาษีคำนวณถูก | Order | int | P1 | ✅ | @regression | PR | qa-b |
| TS-REPORT-220 | export ยอดขายตรง golden file | Report | int | P2 | ✅ | @nrt @golden | nightly | qa-b |
| TS-UI-310 | flow checkout ครบ | Web | e2e | P2 | ⏳ manual | @regression @slow | release | qa-a |
```

**3) เกณฑ์คัด Automation Candidate** — ให้คะแนน, ผ่านเกณฑ์ = automate
```markdown
ควร automate เมื่อเข้าหลายข้อต่อไปนี้ (ยิ่งมาก ยิ่งคุ้ม):
[ ] รันบ่อย/ซ้ำทุก release (regression value สูง)        +3
[ ] ครอบคลุม business-critical / high-risk path           +3
[ ] deterministic ผลคงที่ ตั้ง assert ชัดได้              +2
[ ] เสถียร ไม่ขึ้นกับ UI/timing ที่เปลี่ยนบ่อย (ไม่ flaky) +2
[ ] manual แล้วช้า/น่าเบื่อ/ผิดพลาดง่าย                   +1
[ ] data-driven หลายชุดอินพุต (คุ้มกับการ parametrize)     +1
อย่าเพิ่ง automate เมื่อ:
( ) UI/spec ยังเปลี่ยนรายสัปดาห์ — รอ stabilize           −3
( ) ต้องใช้วิจารณญาณมนุษย์ (usability, look-and-feel)      −3
( ) one-off / รันครั้งเดียว                                −2
→ คะแนน ≥ 5 = automate (เลือก level ต่ำสุดที่ครอบคลุมได้: unit > int > e2e)
```

## Checklist / Definition of Done
- [ ] มี Change Impact Analysis ครบทั้ง direct + ripple พร้อม mapping ไป test
- [ ] เลือกกลยุทธ์ selection ชัด (retest-all / selective / prioritized) + เหตุผล และมี full run กันพลาด (nightly)
- [ ] smoke เป็น gate ก่อน regression; sanity เจาะพื้นที่ที่แตะ — แยกบทบาทถูก
- [ ] non-regression baseline ครอบคลุมพื้นที่ refactor/migration และมีกติกาอัป baseline เมื่อ change ตั้งใจ
- [ ] เคส automation candidate ผ่านเกณฑ์, กระจายตาม pyramid, hook เข้า CI ตาม trigger
- [ ] flaky test มี quarantine + owner + กำหนดแก้ ไม่ block release ถาวรและไม่ retry กลบ
- [ ] suite ผ่านการ prune (ลบซ้ำ/ล้าสมัย), มี tag/หมวด
- [ ] มี regression report เป็น go/no-go input และระบุความเสี่ยงที่เหลือ

## เคล็ดลับ & ข้อควรระวัง
- **อย่าสับสน fail จริงกับ intended change:** refactor ที่ "ตั้งใจไม่เปลี่ยน behavior" → NRT จับทุก diff; แต่ feature ที่เปลี่ยน output โดยตั้งใจ → ต้องอัป baseline พร้อม justify ไม่ใช่กด accept หรือ comment-out test.
- **selective/RTS อันตรายถ้า impact map ไม่ครบ** (dynamic dispatch, reflection, config, feature flag หลุด map). กันด้วย full retest nightly + เพิ่ม margin ในพื้นที่เสี่ยงสูง.
- **smoke ≠ regression เต็ม:** smoke แค่บอกว่า "พังจน build ใช้ไม่ได้ไหม" ไม่ได้แทน regression — อย่าตัด regression เพราะ smoke ผ่าน.
- **flaky คือบั๊กของ test:** retry blanket = ซ่อนปัญหา + ซ่อน regression จริง. quarantine ชั่วคราว + ตามแก้ ไม่ปล่อยค้าง; ถ้า quarantine บวมแปลว่าสุขภาพ suite แย่.
- **baseline เน่าได้:** golden/snapshot ที่ไม่มีใครรีวิวเวลาอัป จะกลายเป็น "rubber-stamp" — บังคับ review diff ของ snapshot ใน PR.
- **เลือก level ให้ถูก:** ดัน regression ไปไว้ระดับต่ำสุดที่ครอบคลุม (unit/integration เร็ว+เสถียร) แทนกอง e2e ที่ช้า+flaky — e2e ไว้เฉพาะ critical journey.
- **วัดคุณค่า test:** test ที่ไม่เคยจับบั๊กและแพงต่อการดูแล = candidate ตัดทิ้ง; coverage สูงไม่เท่ากับ regression แข็งแรงถ้า assert อ่อน.
- **ข้อมูลทดสอบต้อง self-managed/idempotent** ไม่งั้น regression จะ flaky จาก state ค้าง.

## เชื่อมกับเฟสอื่น
- **ก่อนหน้า:** `/test-strategy` — กำหนด test levels, coverage target, pyramid, environment ที่ regression suite นี้ต่อยอด
- **ถัดไป:** `/security-testing` — regression ด้านความปลอดภัย/ช่องโหว่ (ต่อด้วย `/pentest-plan`)
- **เกี่ยวข้อง:** `/release-deploy` — เอา regression/smoke ไปวางใน CI/CD pipeline (per-PR/nightly/pre-release gate) และ `/observability` — สัญญาณ prod ที่ feed กลับมาเป็นเคส regression ใหม่
- **ภาพรวมทั้งวงจร:** `/sdlc-agile`
