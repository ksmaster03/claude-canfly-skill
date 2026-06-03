---
name: financial-model
description: สร้างแบบจำลองการเงิน (รายได้-ต้นทุน-กระแสเงินสด) สำหรับธุรกิจ/สตาร์ทอัพ
category: finance-pricing
---

# financial-model

## ใช้ตอนไหน
ต้องทำโมเดลการเงินคาดการณ์อนาคต

## ขั้นตอน
1. กำหนดสมมติฐานหลัก (ราคา, จำนวนลูกค้า, โต %)
2. สร้าง revenue build จาก driver จริง
3. ใส่ต้นทุนคงที่/ผันแปร + หา break-even
4. ทำ projection 12-36 เดือน + sensitivity

## เทมเพลต / โครงผลลัพธ์
```
สมมติฐาน / รายได้(driver) / ต้นทุน / กำไร / cash flow / break-even / scenario
```

## เคล็ดลับ
- โมเดลดีอยู่ที่สมมติฐาน ไม่ใช่สูตรซับซ้อน
- ทำ best/base/worst case เสมอ
