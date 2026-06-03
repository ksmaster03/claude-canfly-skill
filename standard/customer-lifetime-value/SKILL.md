---
name: customer-lifetime-value
description: คำนวณและวิเคราะห์ CLV เพื่อวางงบหาลูกค้าและ retention
category: analytics-data
---

# customer-lifetime-value

## ใช้ตอนไหน
อยากรู้ว่าลูกค้าหนึ่งคนมีมูลค่าเท่าไหร่ตลอดอายุ

## ขั้นตอน
1. คำนวณรายได้เฉลี่ย/ลูกค้า/รอบ
2. หา churn rate + อายุลูกค้าเฉลี่ย
3. คำนวณ CLV + เทียบ CAC
4. แยก CLV ตาม segment หาลูกค้าทำเงิน

## เทมเพลต / โครงผลลัพธ์
```
ARPU / churn / อายุเฉลี่ย / CLV / LTV:CAC / CLV แยก segment
```

## เคล็ดลับ
- รู้ CLV → รู้ว่าจ่ายหาลูกค้าได้สูงสุดเท่าไหร่
- เพิ่ม retention มักคุ้มกว่าหาลูกค้าใหม่
