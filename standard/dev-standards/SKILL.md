---
name: dev-standards
description: วางมาตรฐานการพัฒนาให้ทีม — coding standard/linting, branching strategy (Gitflow/trunk-based), commit convention, code review checklist, secure coding และ Definition of Ready/Done. Sets up team development standards: coding style, branching, commits, code review, secure coding, and DoR/DoD. Trigger เมื่อผู้ใช้พิมพ์ /dev-standards หรือขอ "coding standard / code review / branching / git flow / DoD / DoR / secure coding / มาตรฐานการเขียนโค้ด / รีวิวโค้ด".
category: sdlc
phase: "08 Development Standards"
---

# /dev-standards — มาตรฐานการพัฒนา (Development Standards & Practices)

วาง "กติกาการเขียนโค้ดของทีม" ให้ครบและบังคับใช้ได้จริง: ตั้งแต่ coding standard/linting, branching strategy, commit convention, code review checklist, secure coding ไปจนถึง Definition of Ready/Done และ CI gate ที่ต้องผ่านก่อน merge — เพื่อให้คุณภาพโค้ดสม่ำเสมอไม่ขึ้นกับว่าใครเขียน

## ใช้ตอนไหน

- เริ่มโปรเจกต์ใหม่หรือทีมโตขึ้น แล้วยังไม่มีมาตรฐานกลาง (โค้ดสไตล์มั่ว, รีวิวตามอารมณ์, branch ชนกัน)
- โค้ดรีวิวช้า/ปล่อยผ่านง่าย, PR ใหญ่จนรีวิวไม่ไหว, มี secret หลุดเข้า repo, bug ซ้ำ ๆ จาก input ไม่ validate
- onboarding คนใหม่แล้วไม่มีเอกสารบอกว่า "ทีมนี้ทำงานยังไง"
- ต้องตั้ง CI gate / quality gate ก่อน merge แต่ยังไม่รู้ว่าเกตอะไรควรเป็น blocking

> ขอบเขตเฉพาะเฟสนี้ — **test strategy → /test-strategy**, **pipeline/deploy → /release-deploy**, **security scanning tools (SAST/DAST/SCA) → /security-testing**

## Input ที่ต้องถามก่อนเริ่ม

1. **Stack & ภาษา** — เช่น TS/Node, Python, Go, Java; มี monorepo ไหม → กำหนด linter/formatter ให้ตรงภาษา
2. **ขนาดทีม & release cadence** — ทีม 3 คน deploy วันละหลายครั้ง vs ทีม 20 คนปล่อยเป็น release → ตัวกำหนดเลือก branching strategy
3. **ระบบ CI/CD ที่มี** — GitHub Actions / GitLab CI / Jenkins → ต้องรู้ก่อนเขียน CI gate
4. **ระดับ compliance/ความเสี่ยง** — PDPA/PCI/regulated หรือไม่ → ระดับความเข้มของ secure coding & review
5. **branching ปัจจุบัน & ความเจ็บปวด** — ของเดิมพังตรงไหน (merge hell? long-lived branch? hotfix ลำบาก?)
6. **เครื่องมือมีอยู่แล้วไหม** — pre-commit hook, linter config, PR template → จะ extend ของเดิมหรือเริ่มใหม่

## ขั้นตอน (Playbook)

1. **Audit ของเดิม** — ดู repo จริง: มี `.editorconfig`/linter config/PR template/CODEOWNERS ไหม, ขนาด PR เฉลี่ย, lead time ของรีวิว, มี secret ใน history ไหม (`gitleaks detect`)
2. **เลือก coding standard & เครื่องมือบังคับ** — ใช้ formatter ที่ตัดสินใจแทนคน (Prettier/Black/gofmt) + linter ที่จับ bug (ESLint/Ruff/golangci-lint); ตั้งกฎ naming/structure แบบ language-agnostic; ทำให้ "auto-fix ได้" มากที่สุดเพื่อไม่ให้รีวิวเสียเวลากับเรื่อง style
3. **เลือก branching strategy** — ตัดสินใจตามตารางด้านล่าง แล้วเขียน cheat-sheet ชื่อ branch + กติกา merge + branch protection
4. **กำหนด commit convention & PR policy** — Conventional Commits, PR ขนาดเล็ก (< ~400 บรรทัด diff), squash-merge, ผูก ticket
5. **ร่าง code review checklist + SLA + ใครรีวิว** — กำหนดว่า approve กี่คน, CODEOWNERS, SLA รีวิว (เช่น ภายใน 1 วันทำการ), what reviewers look for
6. **เขียน secure coding baseline** — input validation, output encoding, secrets handling, dependency hygiene, error/logging — โยง OWASP Top 10 / ASVS
7. **ตั้ง CI gate (quality gate)** — ระบุเกตที่ "blocking" ก่อน merge: build, lint, unit test + coverage threshold, secret scan, SCA — รายละเอียดเครื่องมือสแกนอยู่ที่ /security-testing
8. **นิยาม DoR/DoD ฝั่ง dev** — story พร้อมหยิบ (DoR) และ "งานเสร็จจริง" (DoD) ที่รวม review/test/doc
9. **วาง technical debt management** — บันทึก debt เป็น ticket (label `tech-debt`), ใส่ `// TODO(owner, ticket)`, จัด budget เช่น 10-20% ของ sprint
10. **เผยแพร่ + บังคับใช้** — commit เอกสารลง repo (`/CONTRIBUTING.md`, `.github/`), เปิด branch protection, รีวิวมาตรฐานนี้ทุกไตรมาส

### เลือก Branching Strategy

| Strategy | เหมาะเมื่อ | ข้อควรระวัง |
|---|---|---|
| **Trunk-based** | ทีม deploy บ่อย, มี CI/test แน่น, feature flags | ต้องมี test อัตโนมัติแข็งแรง; branch อายุสั้น (< 1-2 วัน) |
| **GitHub flow** | ทีมเล็ก-กลาง, CD เป็น main, SaaS เดียว | ไม่มี release branch — environment-based ต้องพึ่ง tag/flag |
| **Gitflow** | ปล่อยเป็น version/release, มี QA gate, รองรับ multi-version | หนัก, branch อายุยาว → merge hell; หลีกเลี่ยงถ้า deploy ต่อเนื่อง |

> Default แนะนำสำหรับทีมส่วนใหญ่ที่มี CI ดี: **trunk-based หรือ GitHub flow** + short-lived branch + squash merge

## Output / Artifact (เทมเพลตพร้อมใช้)

### 1) Branching cheat-sheet (`/CONTRIBUTING.md`)
```
main            → deployable เสมอ, protected, ห้าม push ตรง
feature/<ticket>-<slug>   เช่น feature/TMS-142-driver-eta
fix/<ticket>-<slug>       แก้บั๊ก
hotfix/<ticket>-<slug>    แตกจาก main สำหรับ prod ด่วน
กติกา: branch อายุสั้น (rebase บน main บ่อย) · 1 PR = 1 เรื่อง · squash merge · ลบ branch หลัง merge
Branch protection: ต้องผ่าน CI gate ทุกเช็ค + อย่างน้อย 1 approval + up-to-date กับ main
```

### 2) Conventional Commit (ตัวอย่าง)
```
<type>(<scope>): <subject>          # type: feat|fix|docs|refactor|test|chore|perf|build|ci

feat(auth): add refresh-token rotation
fix(api): reject negative quantity in order payload   # validation bug
refactor(pricing): extract discount rule into strategy
feat(api)!: drop v1 /users endpoint        # "!" = breaking change

BREAKING CHANGE: v1 endpoint removed, ใช้ /v2/users แทน
Refs: TMS-142
```

### 3) PR template (`.github/pull_request_template.md`)
```markdown
## What & Why
<อธิบายสิ่งที่เปลี่ยน + เหตุผล/ticket>  Closes #___

## Type
- [ ] feat  - [ ] fix  - [ ] refactor  - [ ] docs  - [ ] chore

## How to test
<ขั้นตอนทดสอบ / คำสั่ง / screenshot ถ้ามี UI>

## Checklist (ผู้เขียน)
- [ ] PR เล็ก โฟกัสเรื่องเดียว (< ~400 บรรทัด diff)
- [ ] ผ่าน lint + test + build ในเครื่องแล้ว
- [ ] เพิ่ม/อัปเดต test สำหรับโค้ดใหม่
- [ ] ไม่มี secret/credential/PII ใน diff หรือ log
- [ ] input ใหม่มี validation; error handling ครบ
- [ ] อัปเดต doc/README/migration ถ้าจำเป็น
```

### 4) Code review checklist (ผู้รีวิว)
```
ความถูกต้อง  : โค้ดทำตาม requirement? edge case/null/empty/concurrency ครบ?
ออกแบบ      : เรียบง่าย? ไม่ over-engineer? ตรง pattern ของ codebase? ไม่ซ้ำ (DRY)?
ความปลอดภัย : input validate? output encode? ไม่มี SQLi/XSS/secret hardcode? authz ถูกชั้น?
ทดสอบได้   : มี test คุ้ม path สำคัญ? test อ่านรู้เรื่อง ไม่ผูก implementation?
อ่านง่าย    : ชื่อสื่อความ? ฟังก์ชันสั้น? ไม่มี dead/commented code?
ผลกระทบ    : performance (N+1, loop หนัก)? backward-compat? migration ปลอดภัย?
มารยาทรีวิว : comment ชี้ที่โค้ดไม่ใช่คน · แยก "ต้องแก้" (blocking) ออกจาก "nit/แล้วแต่"
SLA        : รีวิวรอบแรกภายใน 1 วันทำการ · approver ≥ 1 (+CODEOWNERS ถ้าแตะ critical path)
```

### 5) Definition of Ready (DoR — ก่อนหยิบ story)
```
[ ] มี acceptance criteria ชัด วัดได้   [ ] dependency/blocker เคลียร์
[ ] design/API contract ตกลงแล้ว        [ ] estimate แล้ว ทีมเข้าใจตรงกัน
[ ] test ระดับ story กำหนดได้           [ ] เล็กพอจบใน 1 sprint
```

### 6) Definition of Done (DoD — ฝั่ง dev)
```
[ ] โค้ดผ่าน CI gate ทั้งหมด (build + lint + test + scan) เป็น green
[ ] code review approved (≥1) และแก้ comment blocking ครบ
[ ] มี unit/integration test ครอบ logic ใหม่ + coverage ไม่ตก threshold
[ ] secure coding ผ่าน: validate input, no hardcoded secret, dependency ไม่มี CVE สูง
[ ] doc/README/CHANGELOG/migration อัปเดต   [ ] merged เข้า main, deploy ได้, ไม่มี flag ค้าง
[ ] tech debt ที่เกิด บันทึกเป็น ticket label tech-debt แล้ว
```

### 7) Secure coding baseline (โยง OWASP)
```
Input validation : allow-list ที่ขอบระบบ; parametrized query (กัน SQLi); validate type/range/length
Output encoding  : encode ตาม context (HTML/JS/URL) กัน XSS; ไม่เชื่อ data จาก client
Secrets          : ห้าม hardcode → ใช้ env/secret manager; เปิด gitleaks ใน CI; หมุน key เป็นรอบ
Dependency       : lockfile committed; รัน SCA (CVE) ใน CI; อัปเดต/แพตช์เป็นกิจวัตร
Error & logging  : ไม่ leak stack/secret/PII ออก response หรือ log; fail closed; log event ด้านความปลอดภัย
AuthN/AuthZ      : เช็ค authorization ทุก request ฝั่ง server; least privilege (ดู /authn-authz-design)
```

## Checklist / Definition of Done (ของเฟสนี้)

- [ ] เลือกและบันทึก coding standard + formatter/linter config commit ลง repo, auto-fix ทำงานใน pre-commit
- [ ] เลือก branching strategy พร้อมเหตุผล + cheat-sheet + เปิด branch protection บน main
- [ ] commit convention + PR template + ขนาด PR policy ใช้งานจริง
- [ ] code review checklist + ผู้รีวิว/CODEOWNERS + SLA ประกาศแล้ว
- [ ] DoR/DoD เผยแพร่ ทีมเห็นชอบร่วมกัน
- [ ] secure coding baseline เขียนและโยง OWASP; gitleaks/SCA อยู่ใน CI
- [ ] CI gate ระบุชัดว่าอันไหน blocking (build/lint/test+coverage/secret scan/SCA)
- [ ] กลไกจัดการ tech debt (label + budget) ตั้งแล้ว
- [ ] เอกสารทั้งหมดอยู่ใน repo (`CONTRIBUTING.md`, `.github/`) และเข้า onboarding

## เคล็ดลับ & ข้อควรระวัง

- **ทำให้ automate แทน "ขอความร่วมมือ"** — อะไรที่บังคับด้วย formatter/linter/CI ได้ อย่าฝากไว้กับวินัยคน; review ควรเหลือไว้คุยเรื่อง design/logic ไม่ใช่ขนาด indent
- **PR เล็กคือคันโยกคุณภาพอันดับหนึ่ง** — PR ใหญ่ = รีวิวผ่านมั่ว ๆ; แตกงานก่อนเขียน ดีกว่าขอให้รีวิวก้อนใหญ่
- **branch protection ต้องเปิดจริง** — มาตรฐานที่ไม่ enforce = แค่ของประดับ; ตั้ง required status checks + required review
- **อย่าตั้ง coverage เป็นเป้าหลอกตา** — 100% coverage ไม่เท่ากับ test ดี; เน้น path สำคัญและ assertion ที่มีความหมาย (รายละเอียดที่ /test-strategy)
- **secret ที่ commit ไปแล้ว = หลุดถาวร** — แม้ลบ commit ก็ต้อง "ถือว่าหลุด" และ rotate key ทันที; ป้องกันต้นทางด้วย pre-commit gitleaks
- **Gitflow ไม่ใช่ default ที่ดีเสมอ** — ถ้า deploy ต่อเนื่อง มันสร้าง merge hell; เลือกตาม cadence จริง ไม่ใช่ตามความคุ้นเคย
- **tech debt ที่ไม่ถูกบันทึก = หายเข้ากลีบเมฆ** — บังคับให้ทุก shortcut มี ticket + เจ้าของ ไม่งั้นไม่มีวันได้คืน
- **มาตรฐานต้องมีชีวิต** — review รายไตรมาส, ปรับตาม pain จริง, ให้ทีมมีส่วนร่วมในการกำหนด ไม่ใช่ยัดจากบนลงล่าง

## เชื่อมกับเฟสอื่น

- **ก่อนหน้า:** /threat-model — ความเสี่ยงที่ระบุไว้ feed เข้า secure coding baseline ของเฟสนี้
- **ถัดไป:** /test-strategy — DoD ที่นี่อ้าง test/coverage ที่นิยามรายละเอียดในเฟสนั้น
- **ที่เกี่ยวข้อง:** /security-testing (เครื่องมือ SAST/DAST/SCA ที่ต่อเข้า CI gate) · /release-deploy (pipeline/deploy ที่ต่อจาก gate) · /authn-authz-design (authz ใน secure coding) · /agile-delivery & /req-discovery (ที่มาของ acceptance criteria ใน DoR)
- **ภาพรวมทั้งวงจร:** /sdlc-agile
