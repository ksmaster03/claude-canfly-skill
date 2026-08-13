<p align="center">
  <img src="assets/banner.png" alt="Claude Canfly Skills" width="100%">
</p>

<h1 align="center">Claude Canfly Skills</h1>

<p align="center">
  คลังสกิลสำหรับ Claude และ Claude Code รวม <b>256 สกิลพร้อมใช้งาน</b><br>
  จัดระเบียบเป็นโครงสร้างมาตรฐาน พร้อมติดตั้งเป็น <code>/slash command</code> ได้ทันที
</p>

---

## คลังนี้คืออะไร

Claude Canfly Skills คือคลังสกิลภาษาไทยและภาษาอังกฤษ สำหรับช่วยให้ Claude ทำงานได้เป็นระบบมากขึ้น ครอบคลุมงานด้านธุรกิจ การตลาด การเขียน งานอาชีพ การวิเคราะห์ และการทำงานร่วมกับ AI

แต่ละสกิลเปรียบเหมือน “สูตรการทำงาน” เฉพาะเรื่อง เขียนอยู่ในรูปแบบไฟล์ Markdown ที่อ่านง่าย มีโครงสร้างชัดเจน บอกครบว่าเหมาะกับงานแบบไหน ควรใช้อย่างไร ต้องทำตามขั้นตอนใด และควรได้ผลลัพธ์ออกมาในรูปแบบใด

สามารถนำไปใช้งานได้ 2 วิธี

1. เปิดอ่านเป็นเทมเพลตหรือแนวทาง แล้วนำเนื้อหาไปใช้กับ Claude ได้ทันที
2. ติดตั้งไว้ในโฟลเดอร์ `~/.claude/skills/` เพื่อเรียกใช้งานเป็นคำสั่ง `/slash` ผ่าน Claude Code

<p align="center">
  <img src="assets/cover.png" alt="Claude Skill เพื่อคนที่อยากเรียนรู้ตลอดเวลา" width="70%"><br>
  <sub>“น้ำไม่เต็มแก้ว เรียนรู้ได้ทุกวัน” — คนเราต่างเรียนรู้ได้ไม่เท่ากัน แต่ทุกคนพัฒนาได้ หากไม่หยุดเรียนรู้</sub>
</p>

---

## โครงสร้างคลังสกิล

<p align="center">
  <img src="assets/structure.png" alt="โครงสร้างคลังสกิล" width="100%">
</p>

| ชุด | โฟลเดอร์            | รายละเอียด                                                                                                                             | จำนวน |
| --- | ------------------- | -------------------------------------------------------------------------------------------------------------------------------------- | ----- |
| A   | รากของโปรเจกต์      | สกิลภาษาไทยสำหรับอาชีพต่าง ๆ จัดตามบุคลิกภาพ 6 แบบของ RIASEC โดยอ้างอิงกลุ่มอาชีพจากกรมการจัดหางาน                                     | 34    |
| B   | `pro-bundle/`       | Pro Bundle รวมสกิล 17 หมวดสากล เช่น คอนเทนต์ การตลาด การขาย การเงิน กฎหมาย การปฏิบัติการ และงานธุรกิจอื่น ๆ                            | 69    |
| C   | `commands/`         | คำสั่งลัดสำหรับ Claude ครอบคลุม Output Modes และตัวช่วยด้านอาชีพ/การสมัครงาน                                                           | 20    |
| D   | `jobsdb-ai-skills/` | สกิลที่อธิบายว่างานใดบ้างที่ AI สามารถช่วยทำแทนได้ อ้างอิงจากตำแหน่งงานยอดนิยมบน JobsDB พร้อมระบุส่วนที่ยังต้องใช้มนุษย์               | 19    |
| E   | `people-skills/`    | สกิลสำหรับเข้าใจและทำงานร่วมกับคนแต่ละประเภท ครอบคลุม MBTI 16 แบบ, DISC 4 แบบ, Enneagram 9 แบบ, CliftonStrengths 34 แบบ และราศี 12 แบบ | 75    |
| F   | `sdlc-skills/`      | พัฒนาซอฟต์แวร์ครบวงจรแบบ SDLC + Agile — ตัวขับเคลื่อน `/sdlc-agile` 1 ตัว + sub-skill รายเฟส (requirement, FR/NFR, business logic, design, auth/SoD, threat model, dev, test, regression, security test, pen test, deploy, monitoring) | 16    |
| G   | `craft-skills/`     | **สกิลจากงานจริง** ที่ใช้กับ Claude Code ทุกวัน — ดีบั๊ก รีวิวโค้ด deploy AWS ออดิตความปลอดภัย ตัดต่อวิดีโอ ทำรีล มาสเตอร์เสียง และปั้น ebook (ไม่ได้เขียนจากเทมเพลต แต่ตกผลึกจากงานที่ทำเสร็จจริง) | 23    |
| —   | `standard/`         | สกิลชุด A–F ในรูปแบบมาตรฐาน `<slug>/SKILL.md` พร้อมติดตั้งใช้งาน                                                                        | 233   |

---

## การจัดการสกิลที่ซ้ำกัน

บางสกิลมีเนื้อหาหรือวัตถุประสงค์ใกล้เคียงกันในหลายชุด เช่น สรุปประชุม เขียน JD ตอบอีเมล ร่างสัญญา เขียนบล็อก ผลิต Ad Copy และวิเคราะห์สต็อก

เพื่อให้ใช้งานง่ายขึ้น งานที่ซ้ำกันข้ามชุดจำนวน 7 กลุ่มจึงถูกจัดรวมให้เหลือ “เวอร์ชันที่ดีที่สุด” เพียงชุดเดียว ส่วนไฟล์ที่ซ้ำจะถูกแปลงเป็นตัวชี้ทางหรือ pointer แทน

ผลลัพธ์คือโฟลเดอร์ `standard/` จะมีเนื้อหาจริง 142 สกิล โดยไม่มีสกิลซ้ำ และไม่มีชื่อ slug ชนกัน

---

## ข้อควรระวังในการใช้ People Skills

ชุด People Skills ถูกออกแบบมาเพื่อช่วยให้เราเข้าใจผู้อื่นและทำงานร่วมกันได้ดีขึ้นอย่างเคารพ ไม่ได้มีไว้เพื่อใช้บงการ ตัดสิน หรือชี้นำผู้อื่นแบบเหมารวม

สิ่งที่ควรคำนึงถึง

* ประเภทบุคลิกภาพเป็นเพียงแนวโน้ม ไม่ใช่กรอบตายตัว คนจริงมีหลายมิติ และอาจเปลี่ยนไปตามบริบท สภาพแวดล้อม หรือประสบการณ์ชีวิต
* ไม่ควรใช้ type เพื่อเดา ตีตรา หรือเหมารวมผู้อื่น ควรใช้ร่วมกับการสังเกต การพูดคุย และการรับฟังจริง
* เครื่องมืออย่าง MBTI และ DISC ควรใช้แบบประเมินอย่างเป็นทางการ หากต้องการความแม่นยำมากขึ้น
* ราศีหรือ Zodiac เป็นความเชื่อเชิงวัฒนธรรม ไม่ใช่หลักฐานทางวิทยาศาสตร์ เหมาะสำหรับใช้เป็นมุมสร้างบทสนทนา ความสัมพันธ์ หรือไอเดียเชิงสร้างสรรค์เท่านั้น

---

## ชุด F · พัฒนาซอฟต์แวร์ครบวงจร (SDLC & Agile)

ชุดสำหรับสายพัฒนาซอฟต์แวร์โดยเฉพาะ — พาทำงานตั้งแต่ **เก็บ requirement จนถึง monitoring บน production** อย่างเป็นระบบ มี artifact และ quality gate ทุกเฟส เนื้อหาเป็นภาษาไทยผสมศัพท์เทคนิคอังกฤษ ใช้ได้จริงระดับมืออาชีพ

ตัวขับเคลื่อนหลักคือ **`/sdlc-agile`** ที่ map ทั้ง lifecycle, จัด quality gate (G0–G6), ทำ traceability (req → design → code → test → release) แล้ว delegate ไปยัง sub-skill รายเฟส 15 ตัว:

| เฟส | สกิล | ได้อะไร |
| --- | --- | --- |
| Agile framework | `/agile-delivery` | Scrum/Kanban, ceremonies, backlog, DoR/DoD, velocity |
| เก็บ requirement | `/req-discovery` | stakeholder map, user story, MoSCoW, acceptance criteria |
| FR & NFR | `/fr-nfr-spec` | SRS — FR มี ID + NFR ที่วัดผลได้ |
| Business logic | `/business-logic-spec` | decision table, state machine, business rules |
| ออกแบบสถาปัตยกรรม | `/solution-design` | C4, ADR, data model (ERD), API contract |
| Authentication/Authorization | `/authn-authz-design` | AuthN flow, RBAC/ABAC, session/JWT, MFA |
| Segregation of Duties | `/sod-matrix` | role×permission matrix, conflict rules, access review |
| Threat modeling | `/threat-model` | STRIDE/DFD, abuse case, security requirements |
| มาตรฐาน dev | `/dev-standards` | coding standard, branching, code review, DoD |
| กลยุทธ์ทดสอบ | `/test-strategy` | test pyramid, test plan, coverage, test case |
| Regression | `/regression-suite` | impact analysis, regression/non-regression, automation |
| Security testing | `/security-testing` | SAST/DAST/SCA, OWASP ASVS, triage CVSS |
| Penetration testing | `/pentest-plan` | scope/RoE, PTES/OWASP, finding report, retest |
| Deployment & Release | `/release-deploy` | CI/CD, blue-green/canary, rollback, change mgmt |
| Monitoring | `/observability` | logs/metrics/traces, SLI/SLO, alerting, incident runbook |

เริ่มใช้: พิมพ์ `/sdlc-agile` แล้วบอกว่าจะทำระบบอะไร — มันจะปรับความหนักเบาให้พอดีกับงาน (right-sizing) แล้วไล่ทีละเฟส หรือจะเรียกเฉพาะเฟสที่ต้องการตรง ๆ เช่น `/threat-model` ก็ได้

---

## ชุด G · สกิลจากงานจริง (Craft Skills)

ต่างจากชุดอื่นตรงที่ชุดนี้ **ไม่ได้เขียนขึ้นจากเทมเพลต** แต่ตกผลึกจากงานที่ทำเสร็จจริงแล้ว — ทุกหัวข้อ "Gotchas" ในไฟล์คือสิ่งที่เคยพังมาก่อน และตัวเลขทุกตัวมาจากการวัดจริง

เขียนสำหรับ **Claude Code** โดยเฉพาะ (ใช้ Bash / Edit / Agent tools) ไม่ใช่ prompt ที่ก๊อปไปวางในแชทได้เลย

| กลุ่ม | สกิล |
| --- | --- |
| วิธีทำงาน | `debug-mantra` `scrutinize` `post-mortem` `management-talk` `teamagent` `recall` `handoff` |
| สร้างโค้ด | `prisma-migrate-safe` `nest-vertical-slice` `rn-screen` `i18n-sync` |
| คลาวด์/ความปลอดภัย | `aws-deploy` `joey` |
| วิดีโอ/คอนเทนต์ | `vidcraft` `vdocut` `vdostory` `vdomindset` `reel-factory` `reelcut` `conveyor-loop` |
| เสียง/ภาษา | `tinglish` `audio-master` |
| หนังสือ | `ebook` |

ตัวอย่างที่หยิบไปใช้ได้ทันที

* **`debug-mantra`** — บังคับวินัยดีบั๊ก 4 ขั้น ห้ามเสนอ fix ก่อนจะ **พยายามหักล้างสมมติฐานของตัวเอง**
* **`tinglish`** — แปลงคำอังกฤษเป็นคำอ่านไทยก่อนป้อน TTS ให้เสียงออกมาเหมือนคนไทยพูด ไม่ใช่สำเนียงฝรั่ง (มาพร้อม dict + สคริปต์)
* **`reelcut`** — ถอดสูตรคลิปสั้นแบบ forensic วัดจริงทุกค่า ทั้งจังหวะคัต LUFS สเตอริโอ แล้วเอาสูตรไปสร้างคลิปใหม่
* **`handoff`** — จบงานแล้วบันทึกความจำ + push ขึ้น GitHub พร้อมด่านกันคีย์หลุด

รายละเอียดครบทุกตัว รวมถึงตัวแปร path ที่ต้องตั้งเอง อยู่ใน [`craft-skills/README.md`](craft-skills/README.md)

> สกิลชุดนี้ล้าง path เฉพาะเครื่อง ชื่อลูกค้า และ hostname ของ production ออกหมดแล้ว ส่วนเครื่องมือภายนอกที่บางสกิลเรียกใช้ (เช่น toolchain ตัดต่อวิดีโอ) ไม่ได้รวมมาในคลังนี้ — ไฟล์จะบอกว่าต้องเตรียมอะไร

---

## วิธีติดตั้งใช้งาน

ติดตั้งสกิลทั้งหมดเข้า Claude Code ด้วยคำสั่ง

```bash
cp -r standard/* ~/.claude/skills/
cp -r craft-skills/* ~/.claude/skills/   # ชุด G (สกิลจากงานจริง)
```

หากต้องการติดตั้งเฉพาะบางสกิล สามารถเลือกโฟลเดอร์ที่ต้องการได้ เช่น

```bash
cp -r standard/blog-post ~/.claude/skills/
```

สำหรับ Windows PowerShell

```powershell
Copy-Item "standard\blog-post" "$env:USERPROFILE\.claude\skills\" -Recurse -Force
```

หลังจากติดตั้งแล้ว สามารถเรียกใช้ในแชตได้ เช่น `/blog-post` หรือพิมพ์งานที่ตรงกับ trigger ของสกิลนั้น

> หมายเหตุ: หากติดตั้งสกิลจำนวนมากพร้อมกัน สกิลบางตัวที่มี trigger กว้างอาจถูกเรียกใช้งานบ่อยกว่าที่ต้องการ แนะนำให้เริ่มจากติดตั้งเฉพาะสกิลที่ใช้งานจริงก่อน แล้วค่อยเพิ่มชุดอื่นภายหลัง

---

## เครื่องมือดูแลคลัง (Meta skills)

นอกจากสกิลเนื้อหา 256 ตัว มีเครื่องมือ 2 ตัวที่ทำให้คลังใช้ง่ายและเติบโตเอง:

### /skill-router — เลือกสกิลอัตโนมัติจากประโยคสนทนา
ไม่ต้องจำชื่อสกิลทั้งหมด แค่พิมพ์งานแบบธรรมชาติ เช่น "ช่วยเขียนบทความเรื่อง..." หรือ "ร่างสัญญาจ้างให้หน่อย"
`/skill-router` จะจับใจความ แล้วแมตช์กับ [`skill-catalog.md`](skill-catalog.md) (ดัชนีสกิลทั้งหมด) เลือกสกิลที่ตรงที่สุดมาทำงานให้ — ถ้ากำกวมจะเสนอตัวเลือกให้ยืนยันก่อน

### /skill-scout — หา ศึกษา และเติม/อัปเดตสกิลจาก GitHub
ออกไปสำรวจสกิลที่คนอื่นทำบน GitHub เรียนรู้แพตเทิร์น หาช่องว่างเทียบคลังปัจจุบัน แล้วสร้างสกิลที่ขาดหรืออัปเดตของเดิมให้ทันสมัย จากนั้นรีเฟรช `standard/` + `skill-catalog.md` ให้อัตโนมัติ
มีการ์ดความปลอดภัยในตัว: ถือไฟล์จากเน็ตเป็นข้อมูลไม่น่าเชื่อถือ ไม่ทำตามคำสั่งที่ฝังมา (prompt injection) และเคารพลิขสิทธิ์/ให้เครดิต

ติดตั้ง: `cp -r skill-router skill-scout ~/.claude/skills/`

---

## โครงสร้างโฟลเดอร์

```text
claude-canfly-skill/
  assets/                 กราฟิกประกอบ เช่น banner และภาพโครงสร้าง
  pro-bundle/             ชุด B: Pro Bundle รวมสกิล 17 หมวด
  commands/               ชุด C: คำสั่งลัดสำหรับ Claude
  jobsdb-ai-skills/       ชุด D: สกิลเกี่ยวกับงานที่ AI สามารถช่วยทำแทนได้
  people-skills/          ชุด E: สกิลสำหรับเข้าใจและทำงานกับคนแต่ละประเภท
  sdlc-skills/            ชุด F: พัฒนาซอฟต์แวร์ครบวงจร SDLC + Agile (/sdlc-agile + รายเฟส)
  craft-skills/           ชุด G: สกิลจากงานจริงที่ใช้กับ Claude Code (ดีบั๊ก/deploy/วิดีโอ/ebook)
  skill-router/           เครื่องมือ: เลือกสกิลจากประโยคสนทนา
  skill-scout/            เครื่องมือ: หา ศึกษา และเติมสกิลจาก GitHub
  skill-catalog.md        ดัชนีสกิลทั้งหมด (router/scout ใช้แมตช์)
  standard/               สกิลทั้งหมด 233 รายการ (ชุด A–F) + เครื่องมือ 2 ตัว ในรูปแบบมาตรฐาน <slug>/SKILL.md
  *.md                    ชุด A: สกิลอาชีพภาษาไทยที่อยู่ในรากของโปรเจกต์
  _make_*.py              สคริปต์สำหรับสร้าง รวม และปรับไฟล์ใหม่
```

---

## การสร้างไฟล์ใหม่หรือปรับแก้

ทุกชุดสกิลสามารถสร้างใหม่ได้จากสคริปต์ Python ที่เตรียมไว้ โดยต้องมี Pillow สำหรับการสร้างกราฟิก

```bash
python _make_pro_bundle.py        # สร้างชุด B
python _make_commands.py          # สร้างชุด C
python _make_jobsdb_ai_skills.py  # สร้างชุด D
python _make_people_skills.py     # สร้างชุด E
# ชุด F (sdlc-skills/) เขียนมือเป็นโฟลเดอร์ <slug>/SKILL.md โดยตรง — ไม่มี _make script
python _make_standard.py          # รวมทุกชุด (รวมชุด F) ให้อยู่ในรูปแบบมาตรฐาน
python _make_catalog.py           # อัปเดตดัชนีสกิล skill-catalog.md (ให้ router/scout เห็น)
python _make_graphics.py          # สร้างกราฟิก banner และ structure
```

---

## โครงสร้างไฟล์สกิล

แต่ละไฟล์ `SKILL.md` จะมี frontmatter และโครงสร้างเนื้อหามาตรฐาน ดังนี้

```markdown
---
name: <slug>
description: <สรุปสั้น ๆ ว่าสกิลนี้ใช้ทำอะไร และควรเรียกใช้เมื่อใด>
---

# <ชื่อสกิล>

## ใช้ตอนไหน

## ขั้นตอน

## เทมเพลต / ผลลัพธ์

## เคล็ดลับ
```

โครงสร้างนี้ช่วยให้ Claude เข้าใจบริบทของสกิลได้ง่ายขึ้น และทำให้ผู้ใช้สามารถอ่าน แก้ไข หรือนำไปต่อยอดได้สะดวก

---

<p align="center">
  <img src="assets/flag.png" alt="" width="120"><br>
  <sub>จัดทำในประเทศไทย — Claude Canfly Skills</sub>
</p>
