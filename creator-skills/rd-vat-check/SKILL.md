---
name: rd-vat-check
description: ตรวจผู้ขายกับกรมสรรพากรผ่าน web service ฟรี (จด VAT รายสาขา เลขผู้เสียภาษีมีจริงไหม ออก e-Tax ได้ไหม) ไม่ต้องสมัคร พร้อมดึงทุกสาขาเป็น CSV และแบบที่ใช้เขียนโค้ดเชื่อมในระบบ. Trigger เมื่อพิมพ์ /rd-vat-check หรือขอ "ตรวจ VAT ผู้ขาย / เช็คเลขผู้เสียภาษี / ผู้ขายจด VAT ไหม / เชื่อมสรรพากรตรวจผู้ขาย / ดึงสาขาจากกรมสรรพากร".
---

# rd-vat-check

ตรวจผู้ขายกับ web service ของกรมสรรพากรที่เปิดให้ใช้ฟรี ผู้ใช้และรหัสผ่านคือ `anonymous` ตามที่กรมประกาศ
ทดสอบจริงแล้วกับบริษัทที่มีหลายสาขา (บริษัทค้าปลีกใหญ่มีหลายหมื่นสาขา) และเลขปลอม 1234567890123 (ในตัวอย่างด้านล่าง `0000000000000` คือที่ว่างให้ใส่เลขผู้เสียภาษี 13 หลักของคุณ)

## ใช้เมื่อไร
- ผู้ใช้ให้ตรวจว่าผู้ขายหรือลูกค้าจด VAT ไหม หรือเลขผู้เสียภาษีถูกไหม
- ต้องการที่อยู่หรือสาขาตามทะเบียน VAT (ที่อยู่ใน DBD ไม่ตรงกับทะเบียน VAT เสมอไป)
- ออกแบบหรือเขียนโค้ดตรวจผู้ขายในระบบเอกสาร เช่น ระบบจัดการเอกสารจัดซื้อ

## ขั้นตอน
ต้องมี `pip install defusedxml` 

1. ตรวจทีละราย ใส่เลขสาขาตามที่พิมพ์บนใบกำกับ ("สำนักงานใหญ่" = 0, "สาขาที่ 00001" = 1)
   ```
   python -I ~/.claude/skills/rd-vat-check/scripts/rd_check.py 0000000000000
   python -I ~/.claude/skills/rd-vat-check/scripts/rd_check.py 0000000000000 15
   python -I ~/.claude/skills/rd-vat-check/scripts/rd_check.py 0000000000000 99 --json
   ```
   ผลบรรทัดแรกเป็น `PASS` `FAIL` หรือ `PENDING` พร้อมเหตุผล ตามด้วยชื่อ ที่อยู่ และสถานะ e-Tax
2. ดึงทุกสาขาของบริษัทหนึ่งเป็น CSV (UTF-8 BOM เปิดใน Excel ได้)
   ```
   python -I ~/.claude/skills/rd-vat-check/scripts/rd_check.py 0000000000000 --branches out.csv
   ```
   ใช้กับบริษัทที่สาขาไม่มาก บริษัทค้าปลีกใหญ่ได้ไฟล์ 18 MB ใช้เวลา 10 วินาที

ตรรกะการตัดสินผลที่สคริปต์ใช้ (ทดสอบแล้วทุกแบบ ยกเว้นข้อ 3):
1. พบที่สาขานั้น → `PASS`
2. ไม่พบที่สาขานั้น แต่พบที่สาขา 0 → `FAIL` จด VAT แต่เลขสาขาบนใบไม่มีในทะเบียน
3. ไม่พบทั้งคู่ แต่ TIN Service บอกว่ามีอยู่จริง → `FAIL` มีเลขแต่ไม่ได้จด VAT (‼ ยังไม่เคยรันจริง ไม่มีเลขตัวอย่าง)
4. ไม่พบ และ TIN Service บอกว่าไม่มี → `FAIL` เลขไม่มีอยู่จริง
5. เรียกไม่สำเร็จหรือหมดเวลา → `PENDING`

## บริการและวิธีเรียก (ใช้เขียนโค้ดในระบบ)
| บริการ | URL | รูปแบบ |
|---|---|---|
| VAT | `https://rdws.rd.go.th/serviceRD3/vatserviceRD3.asmx` | SOAP 1.2 `Service` (TIN, Name, ProvinceCode 0, BranchNumber, AmphurCode 0) · `ServiceArr` (TINs) คืนทุกสาขา |
| TIN | `https://rdws.rd.go.th/serviceRD3/checktinpinservice.asmx` | SOAP 1.2 `ServiceTIN` → `vDigitOk` `vIsExist` |
| e-Tax | `https://etaxws.rd.go.th/etaxapi/services/checkRegstration` | POST JSON `{"taxNo": "..."}` → `code` T001 ถึง T999, `data.isVat` `registerDatetime` `endDatetime` |

Header ของ SOAP คือ `Content-Type: application/soap+xml; charset=utf-8` ส่วน namespace และตัวอย่างคำขอดูใน `scripts/rd_check.py`
เอกสารทางการ: rd.go.th/42535.html (VAT) · 42533.html (TIN) · 62829.html (e-Tax) · ไฟล์ตัวอย่าง `fileadmin/webservice/Sample_SOAP_Request_V5.pdf`

## กับดัก (เจอจริงทั้งหมด)
- **ทาง IPv6 ของ `rdws.rd.go.th` ต่อไม่ติด** จากเครือข่ายสำนักงาน ทำให้ค้าง 21 วินาทีทุกคำขอ (`curl -6` หมดเวลา `curl -4` ได้ 0.23 วินาที) สคริปต์จึงบังคับ IPv4 โค้ดในระบบต้องทำแบบเดียวกัน
- หาไม่พบได้ **HTTP 200** พร้อม `vmsgerr` (VAT) หรือ `vMessageErr` (TIN) ไม่ใช่ HTTP error
- ส่งแค่ชื่อโดยไม่มีเลขผู้เสียภาษีได้ **HTTP 500**
- `GET ?WSDL` ถูก redirect ไปหน้า error เป็นเรื่องปกติ ไม่ได้แปลว่าบริการปิด ให้เขียนคำขอเอง อย่าสร้างไคลเอนต์จาก WSDL
- `vBusinessFirstDate` เป็นปี **พ.ศ.** · ช่องที่ว่างเป็น `-` · `vName` มีช่องว่างซ้อน ต้องรวมช่องว่างก่อนเทียบชื่อ
- e-Tax ต้องใช้คีย์ `taxNo` เท่านั้น (`taxId` ได้ T003, form-urlencoded ได้ 415) ครั้งแรกของแต่ละเลขช้าราว 10 วินาที
- ไม่มี SLA และไม่ประกาศเพดานจำนวนคำขอ ให้แคชผล หน่วงจังหวะ และมีทางตรวจด้วยมือ
- แปลง XML ด้วยตัวที่ปิด entity (`defusedxml` ใน Python, fast-xml-parser `processEntities: false` ใน TypeScript)
- ไม่ต้องติดตั้งใบรับรองเพิ่ม TLS ผ่านด้วยชุด CA มาตรฐาน (certifi) แม้ PDF ของกรมจะบอกให้ติดตั้ง

## ตรวจผล
- เลขสำนักงานใหญ่ของบริษัทที่จด VAT จริง ต้องได้ `PASS` พร้อมวันที่จด VAT และที่อยู่ตรงกับทะเบียน
- `--branches` ต้องได้จำนวนสาขาเท่ากับที่เห็นในทะเบียนของกรมสรรพากร
- เลขปลอม `1234567890123` ต้องได้ `FAIL` เลขไม่มีอยู่จริง

