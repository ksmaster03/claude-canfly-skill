---
name: azure-price-lookup
description: ดึงราคาจริงของ Azure (VM, ดิสก์, backup, เครือข่าย) จาก Azure Retail Prices API แบบไม่ต้อง login เพื่อทำ sizing หรือใบเสนอราคา แทนการเดาราคา. Trigger เมื่อพิมพ์ /azure-price-lookup หรือขอ "ราคา Azure / ราคา VM azure / ประเมินค่า Azure / azure sizing / เทียบราคา VM".
---

# /azure-price-lookup

ใช้ก่อนใส่ราคา Azure ลงเอกสารทุกครั้ง ราคาที่จำมาหรือที่อยู่ในเอกสารเก่ามักผิด
(เคยเจอ: ไฟล์ sizing เดิมใส่ B2ms $0.096 แต่ราคาจริงใน Southeast Asia คือ $0.106)

API สาธารณะ ไม่ต้องใช้ key: `https://prices.azure.com/api/retail/prices?$filter=...` ตอบเป็นหน้า ๆ ตาม `NextPageLink` (สคริปต์ตามให้ครบ)

## คำสั่ง (รันจริงแล้ว 16/10/2026)

```bash
K=~/.claude/skills/azure-price-lookup/scripts
python -I $K/azure_prices.py vm southeastasia Standard_D2as_v5 Standard_B2s      # Linux: PAYG + จอง 1/3 ปี (แปลงเป็นต่อเดือนให้)
python -I $K/azure_prices.py disk southeastasia "P6 LRS" "P10 LRS" "E10 LRS"     # managed disk
python -I $K/azure_prices.py filter "armRegionName eq 'southeastasia' and serviceName eq 'Backup'"
python -I $K/azure_prices.py filter "armRegionName eq 'southeastasia' and serviceName eq 'VPN Gateway'"
python -I $K/azure_prices.py filter "armRegionName eq 'southeastasia' and serviceName eq 'Virtual Network' and productName eq 'IP Addresses'"
python -I $K/azure_prices.py filter "armRegionName eq 'southeastasia' and serviceName eq 'Log Analytics'"
```

ใส่ที่มาลงเอกสารทุกครั้ง เช่น `Azure Retail Prices API · southeastasia · Linux · <วันที่>` และหมายเหตุว่าราคาตามสัญญา EA/CSP ของลูกค้าอาจต่าง

## การอ่านผล (กับดักที่เจอจริง)

- **VM มีแถว "... Cloud Services" ปนมา** ราคาคนละตัว (D2as_v5 Cloud Services $0.2 กับ VM $0.108) → สคริปต์คัดเฉพาะ productName ที่ขึ้นต้น `Virtual Machines` และตัด Windows / Spot / Low Priority
- **ราคาจอง (Reservation) เป็นยอดทั้งสัญญา** แม้ unitOfMeasure เขียน `1 Hour` (D2as_v5 1 ปี = 584 คือ USD ต่อปี) → สคริปต์หาร 12 หรือ 36 ให้
- B2s / B2ms / B4ms (BS series รุ่นแรก) ไม่มีแถวราคาจองใน API ตอนที่ query · Bsv2/Basv2/Dasv5 มี
- **ดิสก์มีหลาย meter**: ราคาดิสก์ปกติคือแถว `<sku> Disk` · แถว `Disk Mount` แยกต่างหาก (ไม่ได้ใส่ในยอด ยังไม่ได้ยืนยันว่าใช้กับกรณีไหน) · Standard SSD มี `Disk Operations` คิดต่อ 10K ครั้ง (น้อยมาก) · แถว `Premium Page Blob` เป็นซ้ำ สคริปต์ตัดทิ้ง
- **Azure Backup ของ VM**: API มีแถวเดียว `Azure VM Protected Instance` $10/เดือน · ขั้นราคา $5 สำหรับ VM ที่ข้อมูลไม่เกิน 50 GB ไม่มีใน API (ข้อมูลจากหน้า pricing ยังไม่ได้ยืนยันด้วยคำสั่ง) · ค่าพื้นที่เก็บ recovery point ต้องประมาณเอง
- snapshot ของ managed disk: LRS $0.132/GB-เดือน (SSD) · HDD $0.05
- Log Analytics: `Analytics Logs Data Ingestion` $2.99/GB หลังโควตาฟรี 5 GB (`tierMinimumUnits 5`)
- **ยังไม่มี region ไทย** ใน API ณ 16/10/2026 (`contains(armRegionName,'thailand')` ได้ 0 แถว)
- ‼ **NAT Gateway หาใน API ไม่เจอ**: ลอง `serviceName eq 'NAT Gateway'`, `contains(productName,'NAT')`, `contains(meterName,'NAT')`, `serviceFamily eq 'Networking' and contains(skuName,'NAT')` ได้ 0 แถวทุกแบบ → ใช้ราคามาตรฐาน $0.045/ชม. + $0.045/GB จากหน้า pricing แล้ว**เขียนกำกับในเอกสารว่ายังไม่ได้ยืนยันกับ API**

## ราคาอ้างอิงที่ดึงได้ (southeastasia · 16/10/2026 · USD)

| รายการ | ราคา |
|---|---|
| Standard_D2as_v5 | 0.108/ชม. · จอง 1 ปี 584 · 3 ปี 1,121 |
| Standard_B2ms · B2s · B4ms | 0.106 · 0.0528 · 0.211 /ชม. |
| Standard_B2as_v2 · B2s_v2 · D2s_v5 | 0.0944 · 0.106 · 0.12 /ชม. |
| Premium SSD P6 · P10 · P15 | 10.207 · 19.71 · 38.01 /เดือน |
| Standard SSD E6 · E10 · E15 | 4.80 · 9.60 · 19.20 /เดือน |
| Public IP Standard static | 0.005/ชม. |
| VPN Gateway VpnGw1AZ · VpnGw1 · S2S connection | 0.21 · 0.19 · 0.015 /ชม. |
| Blob Cool LRS | 0.011/GB-เดือน |

ราคาเปลี่ยนได้ ใช้ตารางนี้ดูคร่าว ๆ เท่านั้น ก่อนใส่เอกสารให้รันคำสั่งใหม่
