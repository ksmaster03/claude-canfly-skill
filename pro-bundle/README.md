# Pro Bundle — 72 Skills จัดหมวดหมู่สากล

ชุดทักษะธุรกิจ/การตลาด/ปฏิบัติการ จัดเป็น 17 หมวด รวมจาก 2 แหล่ง (ภาพ bundle + รายการที่สั่งเพิ่ม) **ตัดตัวซ้ำออกแล้ว**
แต่ละไฟล์มีโครง: `name / description / category` + ใช้ตอนไหน + ขั้นตอน + เทมเพลตผลลัพธ์ + เคล็ดลับ

> สร้างใหม่/แก้ทั้งชุดได้ด้วย `python ../_make_pro_bundle.py`

## หมวดหมู่และ skills

| หมวด | Skills |
|------|--------|
| **content-copy** (7) | blog-post, twitter-thread, tiktok-script, pillar-page, landing-page-copy, social-caption, product-description |
| **email-automation** (4) | email-sequence, abandoned-cart-email, black-friday-emails, email-marketing |
| **sales-funnels** (4) | sales-funnel-builder, tripwire-offer, webinar-sales-script, upsell-flow |
| **ads-paid-media** (4) | facebook-ad-campaign, google-ads-campaign, tiktok-ad-script, ad-copy-tester |
| **seo-search** (4) | keyword-research, seo-audit, local-seo-plan, featured-snippet-optimizer |
| **finance-pricing** (5) | financial-model, revenue-forecast, unit-economics, invoice-generator, pricing-strategy |
| **legal-compliance** (4) | contract-writer, saas-agreement, gdpr-compliance-checklist, privacy-policy |
| **launch-growth** (4) | product-launch-plan, product-hunt-launch, beta-launch-plan, waitlist-builder |
| **social-media** (3) | viral-content-formula, instagram-carousel, youtube-strategy |
| **client-consulting** (3) | discovery-call-script, scope-of-work, service-productization |
| **operations-systems** (6) | sop-builder, okr-builder, workflow-automation, onboarding-checklist, meeting-summary, hiring-job-description |
| **ai-automation** (3) | ai-use-case-finder, prompt-library, tool-stack-audit |
| **courses-education** (4) | course-outline, cohort-program, certification-program, video-script |
| **personal-brand** (4) | personal-brand-strategy, linkedin-strategy, ted-talk-outline, book-proposal |
| **analytics-data** (5) | ab-test-plan, customer-lifetime-value, conversion-funnel-analysis, data-dashboard, competitor-analysis |
| **saas-ecommerce** (4) | checkout-optimization, shipping-policy, customer-onboarding, feature-roadmap |
| **industry-specific** (4) | property-listing, menu-design-brief, fitness-program-outline, industry-deep-dive |

**รวม 72 ไฟล์** (เนื้อหาจริง 69 — `meeting-summary`, `hiring-job-description`, `contract-writer` เป็น 🔗 pointer ที่รวมกับชุดอื่นแล้ว ดู [../README.md#-การรวมตัวซ้ำ-dedupe](../README.md))

## ตัวที่ตัดเพราะซ้ำ (dedupe)
- `automation-workflow` ≈ `workflow-automation` → เก็บ workflow-automation
- `personal-brand-positioning` ≈ `personal-brand-strategy` → เก็บ personal-brand-strategy
- `email-sequence` ถูกจัดไว้ใน email-automation (ไม่ทำซ้ำใน content-copy)
- `sales-funnel-builder`, `facebook-ad-campaign`, `keyword-research`, `course-outline`, `ab-test-plan`, `contract-writer`, `meeting-summary` ปรากฏหลายภาพ → เก็บไฟล์เดียว

## หมายเหตุการนำไปใช้
- ไฟล์เหล่านี้เป็น "สูตรการทำงาน" ก๊อปเนื้อหาให้ Claude หรือใช้เป็นต้นแบบ
- ถ้าจะติดตั้งเป็น slash command ใน Claude Code: ย้ายไป `~/.claude/skills/<slug>/SKILL.md` (slug เป็น a-z 0-9 - อยู่แล้ว ใช้ได้ทันที)
- skill หมวด legal/finance มีคำเตือน ⚠️ ให้ผู้เชี่ยวชาญตรวจก่อนใช้จริง — ไม่ใช่คำแนะนำทางกฎหมาย/การเงิน
