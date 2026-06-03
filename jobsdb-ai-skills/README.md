# JobsDB AI Skills — งานที่ AI ทำแทนได้ (อิงงานวิจัยตำแหน่งงานยอดนิยม)

24 skills ใน 8 สายงาน สร้างจากการ research ตำแหน่งงานยอดนิยมบน JobsDB Thailand + บทความว่างานไหน AI แทนได้/แทนไม่ได้
**จุดต่างจากชุดอื่น:** แต่ละไฟล์ระบุชัดว่า _AI แทนงานเดิมตรงไหน_ และ _⚠️ ส่วนไหนยังต้องใช้คน_

> สร้าง/แก้ทั้งชุดด้วย `python ../_make_jobsdb_ai_skills.py`

## สรุปงานวิจัย

**กลุ่มงานมาแรงบน JobsDB (2025-2026):** Sales/Field Sales, Marketing, HR/Admin, IT/Data/AI, Accounting, Supply Chain/Logistics, Customer Service, Engineering — เทรนด์ "Selective Hiring" จ่ายแพงให้ specialist

**งานที่ AI แทนได้ (ทำซ้ำ/เอกสาร/คีย์ข้อมูล):**
- บัญชี: บันทึกบัญชีรายวัน คีย์ข้อมูล กระทบยอด — "พนักงานบัญชี คีย์ข้อมูล กำลังถูกกลืน"
- บริการลูกค้า: chatbot ตอบอัตโนมัติ FAQ รับสาย
- ธุรการ: งานทำซ้ำเดิมๆ ไม่เปลี่ยนขั้นตอน

**งานที่ AI แทนไม่ได้ (อิง JobsDB + ผู้เชี่ยวชาญ):**
- ความคิดสร้างสรรค์/กลยุทธ์การตลาด, การเข้าใจอารมณ์ลูกค้า, การตัดสินใจเชิงกลยุทธ์, soft skills, AI literacy ในการกำกับ AI อีกที

## สายงานและ skills

| สายงาน | Skills | ตำแหน่ง JobsDB |
|--------|--------|----------------|
| **accounting** | expense-categorization, invoice-data-entry, monthly-report-draft | พนักงานบัญชี, AP, คีย์ข้อมูล |
| **customer-service** | faq-response-bank, complaint-reply-script, ticket-triage-summary | CS, Call Center, Support |
| **admin** | meeting-minutes-auto, email-draft-auto, report-data-compilation | ธุรการ, เลขา, Coordinator |
| **sales** | cold-outreach-writer, crm-followup-writer, lead-qualification | Field Sales, AE, Inside Sales |
| **marketing** | ad-copy-variations, content-calendar, seo-meta-writer | Performance/Content/SEO Marketer |
| **hr-recruitment** | jd-writer, resume-screening-criteria, candidate-email-templates | HR, Recruiter, TA |
| **data-analyst** | sql-query-writer, data-cleaning-plan, insight-summary | Data Analyst, BI, DE |
| **supply-chain** | demand-forecast-explainer, purchase-order-draft, inventory-analysis | Demand Planner, Procurement, Inventory |

**รวม 24 ไฟล์** (เนื้อหาจริง 19 — `meeting-minutes-auto`, `jd-writer`, `email-draft-auto`, `ad-copy-variations`, `inventory-analysis` เป็น 🔗 pointer ที่รวมกับชุดอื่น แต่ยังคงโน้ต "ส่วนที่ AI ยังแทนไม่ได้" ไว้ ดู [../README.md#-การรวมตัวซ้ำ-dedupe](../README.md))

## โครงแต่ละไฟล์
ตำแหน่งงานที่เกี่ยวข้อง → งานเดิมที่ AI ทำแทนได้ → ขั้นตอน → เทมเพลต → ⚠️ ส่วนที่ AI ยังแทนไม่ได้

## หมายเหตุการนำไปใช้
- เหมาะกับ "คนทำงานสายนั้น" ใช้ AI เพิ่ม productivity (ไม่ใช่แทนคนทั้งตำแหน่ง)
- skill บัญชี/HR มีคำเตือน — AI เสนอ คนตรวจ/อนุมัติเสมอ โดยเฉพาะเรื่องตัวเลข กฎหมาย และการตัดสินใจเรื่องคน

## แหล่งอ้างอิง (research)
- [JobsDB Thailand — jobs & categories](https://th.jobsdb.com/jobs)
- [JobsDB — อาชีพที่ AI แทนไม่ได้ ใช้ Soft Skill สู้](https://th.jobsdb.com/th/career-advice/article/jobs-ai-cannot-replace)
- [JobsDB Career Advice Hub](https://th.jobsdb.com/th/career-advice)
- [ประชาไท — 10 ตำแหน่งงานที่ AI ทดแทนได้](https://prachatai.com/journal/2024/01/107747)
- [Thairath — 10 อาชีพมาแรงยุค AI: บัญชี-คีย์ข้อมูลถูกกลืน](https://www.thairath.co.th/money/business_marketing/marketing_trends/2835684)
- [SCB — 5 สายงานรอด-ร่วง ยุค AI](https://www.scb.co.th/th/personal-banking/stories/salary-man/jobs-in-ai-era)
