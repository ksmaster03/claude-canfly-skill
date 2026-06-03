---
name: sql-query-writer
description: เขียน/แก้ query ดึงข้อมูล แทนการเขียน SQL เองทีละครั้ง
role: data-analyst
source: JobsDB research (งานที่ AI ทำแทนได้)
---

# sql-query-writer

## ตำแหน่งงานที่เกี่ยวข้อง (JobsDB)
Data Analyst / BI

## งานเดิมที่ AI ทำแทนได้
แปลงคำถามธุรกิจเป็น SQL query ที่ถูกต้อง

## ขั้นตอน
1. ทำความเข้าใจคำถาม + โครงตาราง/สคีมา
2. เขียน SQL พร้อมคอมเมนต์
3. พิจารณา join/aggregate/filter ให้ถูก
4. เตือน edge case (null/ซ้ำ/timezone)

## เทมเพลต / ผลลัพธ์
```
-- คำถาม: ..
SELECT ..
FROM ..
WHERE ..
-- หมายเหตุ/ข้อควรระวัง: ..
```

## ⚠️ ส่วนที่ AI ยังแทนไม่ได้ (ต้องใช้คน)
- ตรวจความถูกต้องของผลกับความจริงธุรกิจ
- เลือกว่า metric ไหนตอบโจทย์จริง
