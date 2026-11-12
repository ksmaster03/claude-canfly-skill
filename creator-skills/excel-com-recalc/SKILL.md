---
name: excel-com-recalc
description: คำนวณสูตรใน .xlsx ที่สร้างด้วย openpyxl ด้วย Excel จริงบน Windows (แทน recalc.py ของสกิล xlsx ที่ใช้บนเครื่องนี้ไม่ได้) จัดความสูงแถว ส่งออก PDF แล้วเรนเดอร์ PNG ไว้ตรวจหน้าตา พร้อมตัวตรวจสูตรว่าไม่มี error. Trigger เมื่อพิมพ์ /excel-com-recalc หรือขอ "recalc excel / คำนวณสูตรในไฟล์ xlsx / ตรวจไฟล์ excel ก่อนส่ง / export excel เป็น pdf".
---

# /excel-com-recalc

ใช้หลังสร้างหรือแก้ .xlsx ด้วย openpyxl บนเครื่อง Windows นี้ openpyxl เขียนสูตรโดยไม่มีค่าที่คำนวณแล้ว
ถ้าไม่ recalc ใครเปิดด้วยตัวอ่านอื่น (pandas, previewer, `data_only=True`) จะเห็นช่องว่าง
`scripts/recalc.py` ของสกิล xlsx ใช้บนเครื่องนี้ไม่ได้ (ต้องใช้ LibreOffice + AF_UNIX)

ต้องมี: Microsoft Excel, pywin32 (`win32com.client`), openpyxl, PyMuPDF (`fitz`)

## ขั้นตอน (รันจริงแล้ว 16/10/2026)

```bash
K=~/.claude/skills/excel-com-recalc/scripts
# 1) คำนวณ + จัดความสูงแถว + บันทึกทับ (+ PDF ถ้าใส่) · เกิน 90 วิ ฆ่าเฉพาะ Excel ที่สคริปต์เปิดเอง
python -I $K/recalc_com.py "<path>/book.xlsx" "$WORK/scratch/book.pdf"
# 2) ตรวจสูตร: ทุกสูตรต้องมีค่า ไม่มี #error · ใส่สองไฟล์ = เทียบว่าสูตรและค่าตรงกัน (เช่นฉบับ TH กับ EN)
python -I $K/verify_xlsx.py book.xlsx book-EN.xlsx --no-thai
# 3) เรนเดอร์ PDF เป็น PNG แล้วเปิดดูด้วย Read tool
python -I $K/pdf_to_png.py "$WORK/scratch/book.pdf" "$WORK/scratch/book"
```

`verify_xlsx.py` คืน exit 1 เมื่อมีสูตรไม่มีค่า, มี #error, สองไฟล์ไม่ตรงกัน หรือเจออักษรไทยในไฟล์สุดท้าย (เมื่อใส่ `--no-thai`)
**ค่าที่ไม่มี error ไม่ได้แปลว่าถูก**: เทียบตัวเลขสำคัญกับที่คำนวณมือไว้ก่อนเสมอ

## กับดัก (เจอจริงทั้งหมด)

- **ต้องใช้ `DispatchEx` ไม่ใช่ `Dispatch`**: `Dispatch` เกาะ Excel ที่ผู้ใช้เปิดค้างอยู่ แล้ว `Quit()` จะปิดงานของเขา
- **`ExportAsFixedFormat` เคยค้างเกิน 3 นาทีโดยไม่มี error** ครั้งแรกที่รัน (ทิ้งไฟล์ `mso*.tmp` 0 ไบต์ไว้ในโฟลเดอร์ปลายทาง) แต่รันซ้ำด้วยโค้ดเดิมผ่านใน ~10 วิ ยังไม่รู้สาเหตุ จึงมี watchdog ในสคริปต์
  - ไฟล์ xlsx ถูก `Save()` ไปแล้วก่อนถึงขั้น export งานคำนวณจึงไม่เสีย
- **`import win32process` ถูก Smart App Control บล็อก** (`DLL load failed ... An Application Control policy has blocked this file`) ส่วน `win32com.client` ใช้ได้ → หา PID ด้วย ctypes `user32.GetWindowThreadProcessId` แทน
- **Excel ค้างอยู่เบื้องหลังเมื่อ `Workbooks.Open` ล้ม** ถ้าไม่ `Quit()` ใน `finally` · เก็บกวาดเฉพาะตัวที่สคริปต์เปิด:
  ```powershell
  Get-CimInstance Win32_Process -Filter "Name='EXCEL.EXE'" | Where-Object { $_.CommandLine -like '*/automation -Embedding*' } | ForEach-Object { Stop-Process -Id $_.ProcessId -Confirm:$false }
  ```
  Excel ที่ผู้ใช้เปิดเองไม่มี `/automation -Embedding` จึงไม่โดน
- **ข้อความที่ wrap ไม่ขยายแถวเอง** ถ้าสร้างด้วย openpyxl → สคริปต์เรียก `UsedRange.Rows.AutoFit()` ให้ทุกชีต
- **รูปแบบตัวเลข `#,##0.##` กับจำนวนเต็มแสดงเป็น `730.` (มีจุดห้อย)** ใช้ `#,##0` กับคอลัมน์จำนวนเต็ม
- **พาธใน Git Bash**: `"...\\$f.xlsx"` ทำให้ `$f` ไม่ถูกขยาย และ `python -c` ที่มี `'\\'` พังเพราะ quote ซ้อน → ส่งพาธแบบ `/` แล้วให้สคริปต์ `normpath` เอง และเขียนตัวตรวจเป็นไฟล์ ไม่ใช้ `-c`
- ไฟล์ที่มีภาษาไทย: ใช้ฟอนต์ที่มีตัวไทย (Leelawadee UI) ห้ามใช้ monospace · PDF จาก Excel วาดสระไทยถูกต้อง

## สร้างสองภาษาจากสคริปต์เดียว

ถ้าต้องส่งทั้งไทยและอังกฤษ ให้ใส่ข้อความเป็นคู่ `L(th, en)` ในตัวสร้างไฟล์ตัวเดียว แล้วรัน `gen.py th` / `gen.py en`
ตำแหน่งเซลล์และสูตรจะตรงกันเสมอ แล้วพิสูจน์ด้วย `verify_xlsx.py th.xlsx en.xlsx --no-thai`
ตัวอย่างที่ใช้จริง: `<your-project>/gen_spec.py`
