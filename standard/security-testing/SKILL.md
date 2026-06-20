---
name: security-testing
description: วางการทดสอบความปลอดภัยแบบอัตโนมัติใน CI/CD (shift-left) — SAST, DAST, SCA (ช่องโหว่ dependency/CVE), secret/IaC/container scanning, ใช้ OWASP ASVS เป็น checklist และ triage finding ด้วย CVSS. Automate security testing across the pipeline (SAST/DAST/SCA/secret/IaC/container), gate by severity, and verify against OWASP ASVS L1–L3. Trigger เมื่อผู้ใช้พิมพ์ /security-testing หรือขอ "security test / SAST / DAST / SCA / dependency scan / secret scan / OWASP / ทดสอบความปลอดภัย / DevSecOps".
category: sdlc
phase: "11 Security Testing"
---

# /security-testing — ทดสอบความปลอดภัยอัตโนมัติ (Security Testing / DevSecOps)

วางชั้นการทดสอบความปลอดภัยแบบ **อัตโนมัติ** เข้าไปในทุก stage ของ CI/CD (shift-left) ให้ช่องโหว่ถูกจับตั้งแต่ pre-commit ไม่ใช่ตอน prod — ครอบ SAST, DAST, SCA, secret/IaC/container scanning, ผูกกับ **OWASP ASVS** เป็น control checklist และ triage ด้วย **CVSS** พร้อม gating policy ที่ชัด ใครเป็นเจ้าของอะไร block ที่ระดับไหน

> ขอบเขต: เฟสนี้คือ **automated testing** เท่านั้น — การเจาะระบบโดยมนุษย์ (manual exploitation/pentest) ไปที่ `/pentest-plan` · threat ที่ต้องเอามาทดสอบมาจาก `/threat-model` · กฎ secure coding อยู่ที่ `/dev-standards`

## ใช้ตอนไหน

- ตั้ง pipeline ความปลอดภัยใหม่ หรือมีแต่ scan กระจัดกระจายไม่มี gate/owner ที่ชัด
- ทีมอยากรู้ว่า "ต้องมีการทดสอบประเภทไหนบ้าง วางตรง stage ไหน block ที่ severity เท่าไหร่"
- finding ทะลักเข้ามาเยอะ ต้องการกระบวนการ triage + จัดการ false positive อย่างเป็นระบบ
- ต้องพิสูจน์ compliance ว่าโค้ดผ่าน ASVS level เป้าหมาย (เช่น L2 สำหรับแอปที่จัดการข้อมูลสำคัญ)
- ก่อน release gate ที่ต้องการหลักฐานว่า security checks ผ่านครบ

## Input ที่ต้องถามก่อนเริ่ม

1. **เป้าหมาย ASVS level** — L1 (พื้นฐาน/opportunistic), L2 (มาตรฐานสำหรับแอปที่มีข้อมูลสำคัญ — ค่า default ที่แนะนำ), L3 (high-assurance: การเงิน/สุขภาพ/รัฐ)
2. **Tech stack & artifact** — ภาษา/เฟรมเวิร์ก, มี container image ไหม, IaC อะไร (Terraform/CloudFormation/K8s manifest), runtime ที่ deploy
3. **CI/CD platform** — GitHub Actions / GitLab CI / Jenkins / Azure Pipelines (กำหนดวิธีฝัง stage และ gate)
4. **Threat model input** — threat/abuse case จาก `/threat-model` ที่ต้องมี security test รองรับ (เช่น IDOR, SSRF, auth bypass)
5. **Risk appetite & SLA** — จะ block build ที่ severity ไหน (Critical? High?), SLA แก้แต่ละ severity กี่วัน, ใครเป็น security owner
6. **สถานะปัจจุบัน** — มี scanner อะไรอยู่แล้ว, มี baseline/suppression file ไหม, มีหนี้ finding ค้างเท่าไหร่

## ขั้นตอน (Playbook)

1. **กำหนด ASVS scope & target level** — เลือก L1/L2/L3, ตัดหมวด ASVS ที่ไม่เกี่ยวออก (เช่นไม่มี file upload ก็ตัด V12), แมป threat จาก `/threat-model` เข้ากับข้อ ASVS ที่ต้องทดสอบ
2. **เลือกประเภทการทดสอบให้ครบ 7 ชั้น** แล้วแมปเข้า stage:
   - **SAST** (Static — วิเคราะห์ซอร์สโค้ด ไม่รัน): จับ injection, hardcoded crypto, path traversal จาก code/AST · เครื่องมือ open-source เช่น Semgrep, CodeQL, Bandit(Python), gosec(Go) · เด่นเรื่อง coverage โค้ด แต่ false positive สูง
   - **SCA / dependency** (วิเคราะห์ไลบรารีของบุคคลที่สาม): จับ **CVE** ใน dependency + license + transitive deps · เช่น OWASP Dependency-Check, Trivy(fs), Grype, `npm audit`/`pip-audit` · ผูกกับ SBOM
   - **Secret scanning**: จับ key/token/credential ที่หลุดเข้า repo/history · เช่น gitleaks, trufflehog, detect-secrets · ต้องรันบน **commit history** ไม่ใช่แค่ working tree
   - **IaC scanning**: misconfig ใน Terraform/CFN/K8s (S3 public, security group 0.0.0.0/0, container privileged) · เช่น Checkov, tfsec, kube-score
   - **Container/image scanning**: CVE ใน base image + OS package + Dockerfile best-practice (รันเป็น root, latest tag) · เช่น Trivy(image), Grype
   - **DAST** (Dynamic — โจมตีแอปที่รันจริง black-box): จับ runtime issue ที่ SAST มองไม่เห็น (config, auth flow, reflected XSS) · เช่น OWASP ZAP (baseline/full scan), Nuclei · ต้องมี environment ที่ deploy แล้ว
   - **IAST** (Interactive — instrument runtime ตอนรัน test): ความแม่นสูง false positive ต่ำ เพราะเห็นทั้ง code path + ข้อมูลจริง แต่ตั้งยากและผูกกับ test coverage
3. **ฝังเข้า CI/CD แบบ shift-left** — เร็ว/ถูกไว้ซ้าย หนัก/ช้าไว้ขวา (ดู matrix ด้านล่าง): pre-commit (secret, lint) → PR (SAST diff, SCA, IaC) → build (image scan, SBOM) → pre-deploy (DAST baseline บน staging) → prod (DAST scheduled, runtime monitoring)
4. **เขียน security unit / abuse tests** — เคสที่ scanner ทั่วไปจับไม่ได้ ต้องเขียนเอง: authz negative test (ผู้ใช้ A เข้าถึงข้อมูลผู้ใช้ B ไม่ได้ → IDOR), rate-limit, input validation boundary, business-logic abuse จาก `/threat-model` · รันรวมในชุดเทสปกติ
5. **ตั้ง gating policy** — กำหนดว่าผลแต่ละประเภท × severity ทำให้ build **fail / warn / log** อย่างไร (เช่น secret พบ = fail ทันที, SCA Critical+มี fix = fail, High = warn + ticket); ใช้ baseline file กันของเก่าทำ build แดงทั้งกระดาน แล้วค่อย ๆ ลดเพดาน (ratchet)
6. **Triage & severity ด้วย CVSS** — ทุก finding ให้ CVSS base score → map เป็น severity (Critical 9.0–10 / High 7.0–8.9 / Medium 4.0–6.9 / Low 0.1–3.9) แล้วปรับด้วย context จริง (reachable ไหม, exposed ออกเน็ตไหม, มี compensating control ไหม) — CVSS เป็นจุดเริ่ม ไม่ใช่คำตัดสินสุดท้าย
7. **จัดการ false positive** — ยืนยัน → suppress แบบมี audit (inline comment / suppression file ที่ commit + เหตุผล + วันหมดอายุ review) ห้าม disable rule ทั้งตัวเงียบ ๆ
8. **มอบหมาย owner + SLA + ติดตามจนปิด** — ทุก finding ที่ valid ต้องมีเจ้าของ + กำหนดวันแก้ตาม SLA ของ severity, รายงานแนวโน้ม (เปิด/ปิด/อายุเฉลี่ย/หนี้ค้าง)
9. **ทวน ASVS checklist + ออก security gate report** เป็นหลักฐานก่อนส่งต่อ release

## Output / Artifact (เทมเพลตพร้อมใช้)

### 1) Security Testing Matrix (ประเภททดสอบ × stage × gate/threshold)

| ประเภททดสอบ | Stage ใน CI/CD | สิ่งที่ตรวจ | ตัวอย่างเครื่องมือ (OSS) | Gate / Threshold |
|---|---|---|---|---|
| Secret scanning | pre-commit + PR (full history) | key/token/credential หลุด | gitleaks, trufflehog | **พบ = fail ทันที** (เป็น hard block) |
| SAST | PR (diff-aware) | injection, crypto, path traversal | Semgrep, CodeQL | Critical/High ใหม่ = fail · เก่า = baseline |
| SCA / dependency | PR + build | CVE ใน deps, license | Trivy(fs), Grype, Dependency-Check | Critical+มี fixed version = fail · High = warn+ticket |
| IaC scanning | PR | misconfig Terraform/K8s/CFN | Checkov, tfsec | High misconfig (public exposure) = fail |
| Container/image scan | build (หลัง docker build) | CVE base image + Dockerfile | Trivy(image), Grype | Critical OS CVE มี fix = fail · gen SBOM แนบ |
| DAST (baseline) | pre-deploy (staging) | runtime, auth, headers, XSS | OWASP ZAP baseline, Nuclei | High alert = fail deploy ไป prod |
| DAST (full) + IAST | scheduled (nightly/prod-staging) | deep runtime scan | ZAP full, IAST agent | ออก ticket (ไม่ block pipeline หลัก) |
| Security unit/abuse test | PR (รวมในชุดเทส) | authz/IDOR, rate-limit, business logic | เฟรมเวิร์กเทสของโปรเจกต์ | fail = build fail เหมือน unit test ปกติ |

> หลัก shift-left: ซ้าย = เร็ว/ถูก/feedback ไว (วินาที–นาที) · ขวา = ลึก/ช้า/ต้องมี environment

### 2) OWASP ASVS Checklist (ตัวอย่างข้อ — target L2)

| ASVS Ref | หมวด | ข้อกำหนด (control) | L1 | L2 | L3 | ทดสอบด้วย | ผ่าน? |
|---|---|---|---|---|---|---|---|
| V2.1.1 | Authentication | password ≥12 ตัวอักษร, ไม่จำกัด max ต่ำเกินไป | ✔ | ✔ | ✔ | SAST + unit test | ☐ |
| V3.3.1 | Session | logout ทำลาย session token ฝั่ง server จริง | ✔ | ✔ | ✔ | DAST + abuse test | ☐ |
| V4.1.1 | Access Control | บังคับ authz ทุก request ที่ฝั่ง server (ไม่เชื่อ client) | ✔ | ✔ | ✔ | abuse test (IDOR negative) | ☐ |
| V5.1.3 | Validation | validate input ทุกตัวที่ตรง schema/allowlist | ✔ | ✔ | ✔ | SAST + unit test | ☐ |
| V5.3.4 | Injection | ใช้ parameterized query กัน SQLi ทุกจุด | ✔ | ✔ | ✔ | SAST | ☐ |
| V6.2.1 | Cryptography | ไม่มี secret/key hardcoded ในโค้ด | ✔ | ✔ | ✔ | secret scan + SAST | ☐ |
| V7.1.1 | Logging | ไม่ log ข้อมูลอ่อนไหว (credential/PII) | – | ✔ | ✔ | SAST + code review | ☐ |
| V14.2.1 | Dependency | ไม่มี component ที่มี CVE known-vulnerable | ✔ | ✔ | ✔ | SCA | ☐ |
| V14.4.x | Config | security headers (CSP, HSTS, X-Content-Type) ครบ | ✔ | ✔ | ✔ | DAST baseline | ☐ |

> เทียบกับ **OWASP Top 10** เป็น sanity check ระดับความเสี่ยง: A01 Broken Access Control, A02 Crypto Failures, A03 Injection, A06 Vulnerable Components (= SCA), A07 Auth Failures ฯลฯ — ASVS คือ checklist ที่ละเอียดกว่า ใช้เป็น control จริง

### 3) Triage Finding Register (ช่องโหว่ / CVSS / severity / owner / สถานะ)

| ID | Finding | ประเภท | CVSS (v3.1) | Severity | Reachable/Exposed? | Owner | SLA | สถานะ |
|---|---|---|---|---|---|---|---|---|
| SEC-001 | SQLi ใน `/api/search?q=` | SAST/DAST | 9.8 | Critical | ใช่ (public) | @dev-a | 24 ชม. | Open |
| SEC-002 | `lodash@4.17.15` CVE-2021-23337 | SCA | 7.2 | High | ใช่ (โดน import จริง) | @dev-b | 7 วัน | In Progress |
| SEC-003 | S3 bucket public-read (Terraform) | IaC | 7.5 | High | ใช่ | @devops | 7 วัน | Fixed |
| SEC-004 | AWS key ใน git history | Secret | 9.1 | Critical | ใช่ | @sec-lead | ทันที (rotate) | Rotated |
| SEC-005 | base image OS CVE (ไม่มี fix) | Container | 5.3 | Medium | ไม่ (ไม่ใช้ path) | @dev-c | 30 วัน | Accepted (risk) |
| SEC-006 | reflected XSS หน้า error | DAST | 6.1 | Medium | ใช่ | @dev-a | 30 วัน | Open |
| SEC-007 | Bandit B608 (string SQL) | SAST | – | False Positive | – | @dev-b | – | Suppressed (มี audit) |

**SLA แนะนำตาม severity:** Critical = 24–48 ชม. · High = 7 วัน · Medium = 30 วัน · Low = best-effort/backlog

## Checklist / Definition of Done

- ☐ เลือก ASVS target level แล้ว และแมป threat จาก `/threat-model` ครบ
- ☐ มีการทดสอบครบทั้ง SAST / SCA / secret / IaC / container / DAST (+ abuse test) — ไม่ขาดชั้นใด
- ☐ แต่ละ scanner ฝังในถูก stage (secret/SAST ซ้าย, DAST ขวา) และทำงานอัตโนมัติทุก PR
- ☐ Gating policy ชัด: ระบุว่า severity ไหน block, ไหน warn, มี baseline กันของเก่า
- ☐ ทุก finding มี CVSS + severity + owner + SLA และติดตามใน register
- ☐ False positive ถูก suppress แบบมี audit trail + เหตุผล + วัน review (ไม่ disable เงียบ)
- ☐ SBOM ถูก gen และเก็บไว้ทุก build
- ☐ ASVS checklist ทวนครบ ออก security gate report ได้ก่อน release
- ☐ ไม่มี Critical/High ที่ reachable ค้างเกิน SLA ก่อนปล่อย prod

## เคล็ดลับ & ข้อควรระวัง

- **SAST ≠ DAST ≠ SCA — อย่าสับ**: SAST อ่านโค้ด (white-box, ไม่รัน, เห็นทุก path แต่ false positive เยอะ) · DAST โจมตีแอปที่รันจริง (black-box, จับ runtime/config ที่ SAST มองไม่เห็น แต่ครอบเฉพาะ path ที่ยิงถึง) · SCA ดู dependency ของคนอื่น (CVE) ไม่ดูโค้ดคุณ — ต้องมีครบทั้งสามถึงจะปิด gap
- **CVSS เป็นจุดตั้งต้น ไม่ใช่คำตัดสิน**: ปรับด้วย context จริงเสมอ — Critical ที่ไม่ reachable/อยู่หลัง auth อาจต่ำกว่า Medium ที่ public; ใช้ CVSS Environmental หรือ EPSS (โอกาสถูก exploit จริง) ช่วยจัดลำดับ
- **false positive คือศัตรูตัวจริงของ DevSecOps**: ถ้าทีมเจอ noise มากจะ "ปิดตา" ทั้งระบบ — ลงทุนกับการ tune rule + baseline/suppression มากกว่าเพิ่ม scanner; วัด signal-to-noise
- **secret scan ต้องสแกน git history** ไม่ใช่แค่ working tree — ที่หลุดแล้วถือว่า compromised: **rotate ก่อน** แล้วค่อยลบออกจาก history (ลบเฉย ๆ ไม่ช่วย เพราะอยู่ใน commit เก่าแล้ว)
- **อย่า block ทุกอย่างวันแรก**: ตั้ง baseline ของ finding เดิมเป็น "known", block เฉพาะ *ของใหม่* แล้วค่อย ๆ ลดเพดาน (ratchet down) ไม่งั้น pipeline แดงทั้งกระดาน ทีมจะ bypass
- **DAST ต้องมี environment ที่ deploy แล้ว** + ข้อมูลเทสที่ปลอดภัย — อย่ายิง full scan ใส่ prod จริง (ใช้ baseline บน staging, full scan แบบ scheduled)
- **gen SBOM ทุก build** (CycloneDX/SPDX) เก็บไว้ — พอมี CVE ใหม่โผล่ (เช่น Log4Shell) จะตอบได้ทันทีว่ากระทบ artifact ไหน
- **abuse/authz test ต้องเขียนเอง**: scanner จับ IDOR/business-logic ไม่ได้ — เขียน negative test (ผู้ใช้ A เข้าถึง resource ผู้ใช้ B ต้อง 403) จาก abuse case ใน `/threat-model`
- **container: pin base image digest** ไม่ใช้ `latest`, รันเป็น non-root, scan ทั้งตอน build และ periodic (CVE ใหม่โผล่หลัง build ได้)

## เชื่อมกับเฟสอื่น

- **ก่อนหน้า:** `/regression-suite` — ชุดเทสถดถอยพร้อม จึงเสริมชั้นความปลอดภัยทับลงไปใน pipeline เดียวกัน
- **ถัดไป:** `/pentest-plan` — automated test ปิด gap ส่วนที่เครื่องจับได้; ที่เหลือ (business logic, chained exploit, manual exploitation) ส่งต่อให้คนเจาะ
- **Input จาก:** `/threat-model` — threat/abuse case คือที่มาของ security test ที่ต้องมี · `/authn-authz-design` + `/sod-matrix` — กำหนด authz ที่ abuse test ต้องพิสูจน์ · `/dev-standards` — secure coding rule ที่ SAST บังคับ
- **ภาพรวมทั้งวงจร:** `/sdlc-agile`
