---
name: workflow-automation
description: ออกแบบ workflow อัตโนมัติเชื่อมเครื่องมือ (Zapier/Make) ลดงานมือ
category: operations-systems
---

# workflow-automation

## ใช้ตอนไหน
อยากลดงานซ้ำๆ ด้วยระบบอัตโนมัติ

## ขั้นตอน
1. แผนผังขั้นตอนงานปัจจุบัน หาจุดทำซ้ำ
2. ระบุ trigger → action → เครื่องมือที่เชื่อม
3. ใส่เงื่อนไข/branch + การแจ้งเตือนพลาด
4. ทดสอบ + วาง fallback ถ้าระบบล่ม

## เทมเพลต / โครงผลลัพธ์
```
Trigger / Steps(action) / เครื่องมือ / เงื่อนไข / error handling / ผลที่ประหยัด
```

## เคล็ดลับ
- เริ่ม automate งานที่ทำบ่อย+ขั้นตอนชัดก่อน
- มี fallback เสมอ เผื่อ automation พัง
