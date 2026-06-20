---
name: authn-authz-design
description: ออกแบบ Authentication (ยืนยันตัวตน: password/MFA/SSO/OAuth2-OIDC, session vs JWT) และ Authorization (กำหนดสิทธิ์: RBAC/ABAC) ให้ปลอดภัยตาม OWASP ASVS — produce a concrete, standards-aligned AuthN/AuthZ design (login flows, session/token strategy, role-permission model). Trigger เมื่อผู้ใช้พิมพ์ /authn-authz-design หรือขอ "authentication / authorization / login / OAuth / JWT / RBAC / ABAC / MFA / SSO / ระบบล็อกอิน / สิทธิ์ผู้ใช้".
category: sdlc
phase: "05 AuthN & AuthZ"
---

# /authn-authz-design — ออกแบบการยืนยันตัวตนและสิทธิ์ (Authentication & Authorization)

สกิลนี้ช่วยออกแบบ "ใครเข้าได้ (AuthN)" และ "เข้ามาแล้วทำอะไรได้ (AuthZ)" ให้ครบและปลอดภัยตามมาตรฐานปัจจุบัน (OWASP ASVS V2/V3/V4, OWASP Top 10 — Broken Authentication & Broken Access Control) โดยส่งมอบ artifact ที่เอาไปสร้างจริงได้ทันที ไม่ใช่หลักการลอย ๆ

## ใช้ตอนไหน

- เริ่มออกแบบระบบล็อกอินใหม่ หรือยกเครื่อง auth เดิมที่ทำแบบ ad-hoc
- ต้องตัดสินใจระหว่าง **cookie-session vs JWT**, **own auth vs SSO/IdP**, **RBAC vs ABAC**
- ต้องรองรับ MFA, passwordless, social login, หรือ enterprise SSO (SAML/OIDC)
- ก่อนเขียนโค้ด auth — เพื่อให้ dev มี flow + claim + policy ที่ตกลงกันแล้ว
- หลัง /solution-design (รู้สถาปัตยกรรมแล้ว) ก่อนลงราย permission ใน /sod-matrix

> ขอบเขต: เฟสนี้ออกแบบ **กลไกและโมเดล** auth เท่านั้น
> - เมทริกซ์บทบาท×สิทธิ์แบบละเอียด + กฎ Segregation of Duties → ไปที่ **/sod-matrix**
> - วิเคราะห์ภัยคุกคาม/attack tree → ไปที่ **/threat-model**

## Input ที่ต้องถามก่อนเริ่ม

1. **ประเภทผู้ใช้** — internal staff / external customer / B2B partner / machine-to-machine (service) ปนกันไหม
2. **จำนวน identity source** — self-register, มี IdP องค์กรอยู่แล้ว (Azure AD/Entra, Google Workspace, Keycloak), หรือต้องรองรับ social login
3. **ชนิด client** — web SPA, server-rendered web, mobile app, API/B2B, third-party ที่ขอ access แทนผู้ใช้
4. **ความอ่อนไหวของข้อมูล/ข้อบังคับ** — ต้อง MFA บังคับไหม, PDPA/PCI-DSS/HIPAA, ต้อง audit log แค่ไหน
5. **ความซับซ้อนของสิทธิ์** — role คงที่ไม่กี่แบบ (→ RBAC) หรือขึ้นกับ attribute/owner/แผนก/เวลา (→ ABAC/ReBAC)
6. **ข้อจำกัด** — มี API gateway/reverse proxy ทำ auth ได้ไหม, ต้อง stateless scale หรือมี session store (Redis) ได้, single sign-out จำเป็นไหม

## ขั้นตอน (Playbook)

1. **แยกแกน AuthN กับ AuthZ ให้ขาด** — AuthN = พิสูจน์ "คุณคือใคร", AuthZ = ตัดสิน "คุณทำสิ่งนี้ได้ไหม" สองอย่างนี้คนละ layer คนละการตัดสินใจ อย่าฝัง role ลงใน login logic
2. **เลือกกลยุทธ์ AuthN**
   - มี IdP องค์กร / ต้องการ SSO → ใช้ **OIDC (Authorization Code + PKCE)** เป็นหลัก, อย่าทำ auth เอง
   - มีแต่ผู้ใช้ในระบบเอง → password + MFA, พิจารณา passwordless (passkeys/WebAuthn) เป็น roadmap
   - enterprise legacy → SAML 2.0 (SP-initiated)
   - M2M/service → OAuth2 **Client Credentials**
   - **ห้ามใช้** Implicit flow หรือ Resource Owner Password Credentials (ROPC) — ถูก deprecate แล้ว
3. **ออกแบบ session strategy** — เลือก cookie-session (stateful) หรือ JWT (stateless) ตามตารางตัดสินใจด้านล่าง; กำหนด expiry, refresh, การ revoke, logout, และ cookie flags
4. **เลือก AuthZ model** — RBAC / ABAC / ReBAC / PBAC (ดูเกณฑ์ด้านล่าง); ออกแบบ role→permission และ enforcement point (ที่ API/service layer เสมอ ไม่ใช่แค่ที่ UI)
5. **ออกแบบ token contents** — กำหนด claims/scopes ให้ access token เล็ก, อายุสั้น, ใส่เฉพาะที่ resource server ต้องใช้; อย่ายัด PII หรือสิทธิ์ทั้งหมดลง token
6. **ครอบ account lifecycle** — register, email/phone verify, reset password, lockout/throttle, deactivate/offboard ให้ครบ (ช่องโหว่ broken auth ส่วนใหญ่อยู่ตรง flow รอบ ๆ login ไม่ใช่ตัว login)
7. **ตรวจตาม OWASP ASVS** — กากบาทกับ V2 (Authentication), V3 (Session Management), V4 (Access Control) ก่อนปิดงาน
8. **เขียน artifact** — ส่งมอบ flow + role table + policy table + JWT example ตามเทมเพลตด้านล่าง

### เกณฑ์เลือก session: cookie-session vs JWT

| ประเด็น | Cookie-session (stateful) | JWT access token (stateless) |
|---|---|---|
| Revoke ทันที | ทำได้ (ลบ session ใน store) | ทำยาก — ต้องมี blocklist/short TTL |
| Scale หลาย service | ต้องแชร์ session store (Redis) | ดี — verify ด้วย key อย่างเดียว |
| เหมาะกับ | web app domain เดียว | API, microservices, mobile, M2M |
| ความเสี่ยงหลัก | CSRF (กัน SameSite+token) | token ขโมยแล้วใช้ได้จนหมดอายุ |
| คำแนะนำ default | web ทั่วไป → cookie-session | API/SPA/mobile → access(สั้น)+refresh(rotate) |

> แนวทางที่นิยม: SPA/mobile ใช้ access token อายุสั้น (5–15 นาที) + refresh token หมุน (rotation + reuse detection) เก็บใน httpOnly cookie หรือ secure storage; web แบบ classic ใช้ cookie-session ตรง ๆ ปลอดภัยและง่ายกว่า

### เกณฑ์เลือก AuthZ model

- **RBAC** — สิทธิ์ผูกกับ "บทบาท" จำนวนจำกัด (admin/manager/staff) เปลี่ยนไม่บ่อย → เริ่มที่นี่เสมอ ง่ายและ audit ได้
- **ABAC** — การอนุญาตขึ้นกับ attribute (แผนก, ระดับ, เวลา, วงเงิน, สถานะ record) → เมื่อ role อย่างเดียวระเบิดเป็นร้อย role
- **ReBAC** — สิทธิ์มาจาก "ความสัมพันธ์" (owner ของเอกสาร, สมาชิกทีม/โปรเจกต์) แบบ Google Zanzibar → เหมาะ collaboration/multi-tenant
- **PBAC** — รวมศูนย์เป็น policy engine (OPA/Cedar) แยก decision ออกจากโค้ด → องค์กรใหญ่ กฎเยอะ ต้องเปลี่ยนนโยบายโดยไม่ deploy
- เริ่ม RBAC + เสริม ABAC เฉพาะจุด (เช่น "แก้ได้เฉพาะ record ที่ตัวเองสร้าง") เป็นรูปแบบที่ใช้งานจริงบ่อยที่สุด

## Output / Artifact (เทมเพลตพร้อมใช้)

### 1) AuthN flow — OIDC Authorization Code + PKCE (สเต็ป)

```
1. Client สร้าง code_verifier (สุ่ม) → คำนวณ code_challenge = BASE64URL(SHA256(verifier))
2. Browser → /authorize?response_type=code&client_id&redirect_uri
      &scope=openid profile email&state=<csrf>&code_challenge&code_challenge_method=S256
3. IdP ยืนยันตัวตนผู้ใช้ (password + MFA) → redirect กลับ redirect_uri?code=<auth_code>&state
4. Client ตรวจ state ตรงกับที่ส่งไป (กัน CSRF)
5. Client → POST /token  (code + code_verifier + client_id [+ secret ถ้าเป็น confidential client])
6. IdP ตรวจ verifier ↔ challenge → คืน id_token (JWT) + access_token + refresh_token
7. Client ตรวจ id_token: signature(JWKS), iss, aud, exp, nonce → สร้าง session ฝั่ง app
8. เรียก resource API ด้วย access_token (Authorization: Bearer ...); API ตรวจ sig+exp+aud+scope
9. access หมดอายุ → ใช้ refresh_token ขอใหม่ (rotation: คืน refresh ใหม่, เพิกถอนตัวเก่า)
```
> SPA/mobile = public client → **ต้องใช้ PKCE และไม่มี client_secret**

### 2) RBAC: role → permission matrix

| Permission \ Role | Admin | Manager | Staff | Viewer |
|---|:---:|:---:|:---:|:---:|
| user.create / user.delete | ✅ | — | — | — |
| user.read | ✅ | ✅ | ✅ | ✅ |
| order.create | ✅ | ✅ | ✅ | — |
| order.approve | ✅ | ✅ | — | — |
| order.read.all | ✅ | ✅ | own only | own only |
| report.export | ✅ | ✅ | — | — |
| settings.manage | ✅ | — | — | — |

> permission ตั้งชื่อแบบ `resource.action[.scope]`; "own only" คือจุดที่เสริม ABAC (`record.ownerId == subject.id`)

### 3) Policy table — password / MFA / session (ค่าที่แนะนำ อิง ASVS/NIST 800-63B)

| ด้าน | พารามิเตอร์ | ค่าที่แนะนำ |
|---|---|---|
| Password | ความยาวขั้นต่ำ | ≥ 12 อักขระ (ไม่บังคับ composition rule) |
| Password | ตรวจ breach list | บล็อกรหัสที่หลุดแล้ว (เช่น HaveIBeenPwned k-anon) |
| Password | hashing | Argon2id (หรือ bcrypt cost ≥ 12 / scrypt) ห้าม MD5/SHA1/plain |
| Password | บังคับเปลี่ยนตามรอบ | ไม่บังคับ เปลี่ยนเฉพาะเมื่อมีสัญญาณรั่ว |
| MFA | TOTP / WebAuthn(passkey) | บังคับสำหรับ admin/role สิทธิ์สูง; แนะนำกับทุกคน |
| MFA | SMS OTP | ใช้ได้แต่เป็น factor ที่อ่อนสุด หลีกเลี่ยงถ้ามีทางเลือก |
| Lockout | throttle/lock | exponential backoff + lock ชั่วคราวหลังพลาด ~5–10 ครั้ง + กัน enumeration |
| Session | idle timeout | 15–30 นาที (ระบบความอ่อนไหวสูง) |
| Session | absolute timeout | 8–12 ชม. แล้วบังคับ re-auth |
| Token | access token TTL | 5–15 นาที |
| Token | refresh token | rotation + reuse detection; absolute lifetime จำกัด (เช่น 7–30 วัน) |
| Cookie | flags | `Secure` + `HttpOnly` + `SameSite=Lax` (หรือ `Strict`); ตั้ง `__Host-` prefix |
| Logout | revoke | ลบ server session / เพิกถอน refresh; รองรับ single logout ถ้าใช้ SSO |

### 4) ตัวอย่าง JWT (access token) claims

```json
{
  "iss": "https://auth.example.com",
  "sub": "u_8f3a91c2",
  "aud": "https://api.example.com",
  "exp": 1718900000,
  "iat": 1718899100,
  "jti": "tok_4b1e...",
  "scope": "order.read order.create",
  "roles": ["staff"],
  "tenant": "acme",
  "amr": ["pwd", "otp"]
}
```
> หลักการ: ใส่เฉพาะ claim ที่ resource server ต้องใช้ตัดสิน, ไม่ใส่ PII/secret, ตั้ง `aud` ให้ตรง API, ตรวจ `exp`+signature(JWKS) ทุกครั้ง, ใช้ `jti` ทำ revoke/replay-protection; **ห้าม** ยอมรับ `alg: none`

## Checklist / Definition of Done

- [ ] แยก AuthN กับ AuthZ ชัดเจน เลือกกลยุทธ์ของแต่ละแกนพร้อมเหตุผล
- [ ] เลือกแล้วว่า cookie-session หรือ JWT (+refresh) และอธิบายเหตุผล/วิธี revoke
- [ ] AuthN flow เขียนเป็นสเต็ป (PKCE/state/nonce ครบสำหรับ OIDC)
- [ ] MFA strategy ระบุชัด (ใครต้องบังคับ, factor ใด)
- [ ] เลือก AuthZ model (RBAC/ABAC/...) + ตาราง role→permission ฉบับแรก
- [ ] enforcement อยู่ที่ server/API ทุกจุด (ไม่ไว้ใจ UI), deny-by-default
- [ ] กำหนด token claims/scopes, TTL, signing/verify (JWKS, ห้าม alg=none)
- [ ] cookie flags Secure/HttpOnly/SameSite ครบ + กัน CSRF
- [ ] account lifecycle ครบ: register, verify, reset, lockout, deactivate/offboard
- [ ] ป้องกัน user enumeration ใน login/reset/register (ข้อความ+เวลาตอบกลับสม่ำเสมอ)
- [ ] กากบาท OWASP ASVS V2/V3/V4 ผ่าน
- [ ] ส่งต่อราย permission ละเอียด + SoD ไปยัง /sod-matrix แล้ว

## เคล็ดลับ & ข้อควรระวัง

- **อย่าทำ auth เอง ถ้าเลี่ยงได้** — ใช้ IdP/library ที่ผ่านการตรวจสอบ; crypto/flow ทำเองพังง่าย
- **Authorization ต้องเช็คทุก request ที่ฝั่งหลังบ้าน** — Broken Access Control คืออันดับ 1 ของ OWASP; ซ่อนปุ่มที่ UI ไม่ใช่การ enforce
- **กัน IDOR/BOLA** — object-level: ตรวจว่า subject เป็นเจ้าของ/มีสิทธิ์ใน `id` ที่ขอ ไม่ใช่แค่ "ล็อกอินแล้ว"
- **Deny by default** — ไม่มี rule ตรง = ปฏิเสธ; ห้าม allow-by-default
- **อย่าใส่สิทธิ์/PII ทั้งหมดลง JWT** — token ยิ่งใหญ่ยิ่งช้า, revoke ยาก, ข้อมูลรั่วถ้าถูกอ่าน
- **Refresh token ต้องหมุน + ตรวจ reuse** — ถ้าเจอ refresh เก่าถูกใช้ซ้ำ = ถูกขโมย ให้เพิกถอนทั้งสาย
- **กัน enumeration & timing** — response ของ "อีเมลนี้มีอยู่จริง" กับ "ไม่มี" ต้องดูเหมือนกัน
- **MFA ที่ admin** — บัญชีสิทธิ์สูงคือเป้าหมายอันดับแรก บังคับ MFA และ re-auth ก่อนทำงานอันตราย
- **Logout ต้องจบจริง** — เพิกถอน session/refresh ฝั่ง server; client-side ลบ token อย่างเดียวไม่พอ
- **อย่าผูก authorization กับข้อมูลที่ client ส่งมาแก้ได้** (เช่น role ใน request body/JWT ที่ไม่ verify)

## เชื่อมกับเฟสอื่น

- **ก่อนหน้า: /solution-design** — สถาปัตยกรรม, ขอบเขต service, ตำแหน่ง gateway/IdP ที่ auth จะไปวาง
- **ถัดไป: /sod-matrix** — ลงรายละเอียด role×permission เต็ม + กฎ Segregation of Duties บนโครง RBAC ที่ออกแบบไว้
- **เกี่ยวข้อง: /threat-model** — วิเคราะห์ภัยคุกคามต่อ auth (credential stuffing, token theft, privilege escalation); **/security-testing** & **/pentest-plan** — ทดสอบว่า control ที่ออกแบบใช้ได้จริง
- **ภาพรวมทั้งวงจร: /sdlc-agile**
