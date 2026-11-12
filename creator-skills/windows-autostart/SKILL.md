---
name: windows-autostart
description: ทำให้ server/บริการ (bun, node, python ฯลฯ) เริ่มเองหลัง restart เครื่อง Windows โดยไม่ต้องมีสิทธิ์ admin ด้วย launcher .ps1 + .vbs ในโฟลเดอร์ Startup. Trigger เมื่อพิมพ์ /windows-autostart หรือขอ "ให้ start ทุกครั้งที่ restart เครื่อง / รันตอนเปิดเครื่อง / autostart / ใส่ startup".
---

# windows-autostart

ใช้เมื่อ: ต้องการให้โปรแกรมที่รันค้าง (server) ขึ้นเองหลัง reboot บน Windows และ session ไม่มีสิทธิ์ admin (สร้าง service ไม่ได้)
ผลที่ได้: โปรแกรมเริ่มตอน **user login** (ไม่ใช่ตอน boot) แบบซ่อนหน้าต่าง และเริ่มใหม่เองเมื่อดับ

## ขั้นตอน

1. **สำรวจก่อน** ว่าโปรแกรมรันอย่างไรและมีอะไร autostart อยู่แล้ว:
   - process: `Get-CimInstance Win32_Process | ? { $_.CommandLine -match '<ชื่อ>' }`
   - service / scheduled task / Run key (`HKCU:` และ `HKLM:\Software\Microsoft\Windows\CurrentVersion\Run`) / โฟลเดอร์ `$env:APPDATA\Microsoft\Windows\Start Menu\Programs\Startup`
   - ของที่ต้องขึ้นก่อน (ฐานข้อมูล, Docker container และ restart policy ของมัน)
2. **เขียน launcher `.ps1`** ไว้ในโปรเจกต์ (ตัวอย่างที่ใช้งานจริง: `$PROJECTS/panya\scripts\start-panya.ps1`) ให้มี:
   - mutex ชื่อผูกกับพอร์ต + เช็กว่าพอร์ตถูกฟังอยู่แล้วหรือยัง → ออกเลย กันเปิดซ้อน
   - รอ dependency: ถ้า `docker info` ไม่ผ่านให้ `Start-Process` Docker Desktop แล้วรอ, `docker compose up -d <service>`, รอพอร์ตด้วย `TcpClient`
   - loop: รันโปรแกรม → ถ้าออก รอ 15 วินาทีแล้วรันใหม่
   - รันผ่าน `cmd /c "\"<exe>\" args >> \"<log>\" 2>&1"` เพื่อให้ stdout/stderr ลง log ตรงตัว
   - อ่านพอร์ตจาก env ก่อน แล้วค่อย `.env` เพื่อให้ทดสอบบนพอร์ตอื่นได้
   - ใช้ path เต็มของ exe (เช่น `$env:USERPROFILE\.bun\bin\bun.exe`) อย่าพึ่ง PATH
3. **วางตัวเรียก `.vbs`** ใน Startup (`shell:startup`):
   ```vbs
   Set WshShell = CreateObject("WScript.Shell")
   WshShell.Run "powershell.exe -NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File ""<path>\start-x.ps1""", 0, False
   ```
4. **ทดสอบโดยไม่แตะตัวที่รันอยู่**: ตั้ง env เป็นพอร์ตทดสอบ (เช่น `PORT=6801`, host `127.0.0.1`) แล้วรัน launcher ซ่อนหน้าต่าง ตรวจ 4 อย่าง: health ตอบ, kill โปรแกรมแล้วกลับมาเอง, รัน launcher ซ้ำแล้วออกเอง, รัน `wscript <ไฟล์>.vbs` แล้วไปถึง launcher (ดูจาก log) จากนั้นปิดตัวทดสอบ (launcher ก่อน แล้วค่อยโปรแกรม)
5. **สลับตัวจริง** (เมื่อผู้ใช้ขอให้รัน): ปิดตัวเดิมที่เปิดมือ แล้วเรียก `.vbs` ตรวจ health อีกครั้ง

## Gotchas

- วาง `.ps1` ลง Startup ตรง ๆ ไม่ได้: Windows เปิดใน Notepad ไม่ได้รัน ต้องมี `.vbs` (ซ่อนหน้าต่าง) หรือ `.bat` (เห็นหน้าต่าง) เป็นตัวเรียก
- ระหว่างโปรแกรมรัน `cmd` ถือไฟล์ log ไว้ launcher เขียน log ของตัวเองไม่ได้ ให้ครอบ `AppendAllText` ด้วย try/catch
- PowerShell 5.1 อ่าน `.ps1` ที่เป็น UTF-8 ไม่มี BOM เป็น ANSI: ใช้ ASCII ในสคริปต์ (คอมเมนต์ภาษาไทยจะเพี้ยน)
- จะหยุด ต้องปิด `powershell.exe` ของ launcher ก่อน แล้วค่อยปิดโปรแกรม ไม่งั้นมันเริ่มใหม่
- ขึ้นหลัง login เท่านั้น ถ้าเครื่อง reboot แล้วค้างหน้า login โปรแกรมไม่ขึ้น Docker Desktop ก็ต้องมี session ผู้ใช้เหมือนกัน
- `Get-NetTCPConnection` แบบไม่ใช่ admin อาจคืนแถวว่าง: เช็กพอร์ตด้วย `TcpClient` หรือเรียก health แทน

## ยังไม่เคยรันจริง

- ทางเลือกที่ขึ้นก่อน login (Windows service ผ่าน nssm, scheduled task แบบ "At startup", auto-login) ต้องใช้ admin และยังไม่ได้ลอง
- ยังไม่ได้ยืนยันด้วยการ reboot เครื่องจริง ทดสอบแค่การเรียก `.vbs` ด้วย `wscript`
