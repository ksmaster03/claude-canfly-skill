---
name: windows-update-restart-fix
description: หาสาเหตุที่เครื่อง Windows restart เองทุกวันจาก event log แล้วซ่อนอัปเดตที่ลงไม่ผ่านจน Windows Update สั่ง restart วนทุกคืน. Trigger เมื่อพิมพ์ /windows-update-restart-fix หรือถามว่า "เครื่อง restart เองทุกวัน / รีสตาร์ทเองตอนกลางคืน / ทำไมเครื่องรีบูต / บริการดับตอนเช้า".
---

# windows-update-restart-fix

ใช้เมื่อ: เครื่อง Windows รีบูตเองเป็นประจำ หรือบริการที่เริ่มตอน login หายไปทุกเช้า

## ขั้นตอน (รันจริงแล้วบน DESKTOP-H26BL86, 2026-10-17)

1. **ดูว่าใครสั่ง restart** อ่านได้โดยไม่ต้องเป็น admin:
   ```powershell
   Get-WinEvent -FilterHashtable @{LogName='System'; Id=1074,6008,41; StartTime=(Get-Date).AddDays(-10)} |
     Sort-Object TimeCreated | ForEach-Object { '{0:MM-dd HH:mm} [{1}] {2}' -f $_.TimeCreated, $_.Id, ($_.Message -replace '\s+',' ').Substring(0,200) }
   ```
   - `MoUsoCoreWorker.exe` / `MoNotificationUx.exe` = Windows Update
   - `TrustedInstaller.exe` = กำลังลงอัปเดตระบบ
   - 6008 / 41 = ดับแบบไม่ปกติ (ไฟดับ หรือเครื่องค้าง) ไม่ใช่เรื่องอัปเดต
2. **ดูว่าอัปเดตตัวไหนลงไม่ผ่านซ้ำ ๆ** (event 20 = ล้มเหลว, 19 = สำเร็จ, 43 = เริ่ม):
   ```powershell
   Get-WinEvent -FilterHashtable @{LogName='System'; ProviderName='Microsoft-Windows-WindowsUpdateClient'; StartTime=(Get-Date).AddDays(-10)} |
     Where-Object Id -eq 20 | ForEach-Object { '{0:MM-dd HH:mm} {1}' -f $_.TimeCreated, ($_.Message -replace '\s+',' ') }
   ```
   ถ้าตัวเดียวกันล้มตรงเวลาเดียวกับ restart ทุกคืน ตัวนั้นคือต้นเหตุ เช่น `Pantum Printer Driver Update (1.0.16.0)` error `0x8024200B`
3. ดู active hours ประกอบ: `Get-ItemProperty HKLM:\SOFTWARE\Microsoft\WindowsUpdate\UX\Settings` (restart จะเกิดนอกช่วงนี้)
4. **ซ่อนอัปเดตตัวนั้น** ต้องใช้ admin: ให้ผู้ใช้กด Yes ที่ UAC แล้วอ่านผลจาก log:
   ```powershell
   $s = "$env:USERPROFILE\.claude\skills\windows-update-restart-fix\scripts\hide-update.ps1"
   Start-Process powershell.exe -Verb RunAs -Wait -ArgumentList '-NoProfile','-ExecutionPolicy','Bypass','-File',"`"$s`"",'-Pattern','Pantum'
   Get-Content "$env:USERPROFILE\.claude\skills\windows-update-restart-fix\scripts\hide-update.log"
   ```
   ต้องเห็นชื่ออัปเดตใต้ `all hidden updates now`
5. **ยืนยันผลหลังผ่านไปสองคืน** ด้วยคำสั่งข้อ 1 และ 2

## Gotchas

- คืนแรกหลังซ่อนอาจยัง restart อีกรอบ เพราะรอบนั้นถูกตั้งคิวไว้ก่อนซ่อน ให้ดูผลจากคืนที่สอง
- ไดรเวอร์เวอร์ชันใหม่นับเป็นอัปเดตตัวใหม่ ซึ่งไม่ถูกซ่อน ถ้าอาการกลับมา ให้ทำข้อ 2 ใหม่
- อัปเดตความปลอดภัยประจำเดือน (cumulative) ที่สั่ง restart เดือนละครั้งเป็นเรื่องปกติ อย่าซ่อนตัวนั้น
- เครื่องที่ไม่มี auto-login จะค้างที่หน้า login หลัง restart ทุกอย่างที่เริ่มตอน login (Docker Desktop, pm2, Startup folder) จะดับจนกว่าจะมีคน login ส่วน service ของ Windows กลับมาเอง

## ยังไม่เคยรันจริง

- ทางเลือกอื่นแทนการซ่อน: ลงไดรเวอร์จากเว็บผู้ผลิตเอง หรือ policy `ExcludeWUDriversInQualityUpdate=1`
- สคริปต์ตัวนี้ปรับให้รับ `-Pattern` และค้นอัปเดตทุกประเภท ตัวที่รันจริงค้นเฉพาะ `Type='Driver'` และใส่ "Pantum" ไว้ในสคริปต์ตายตัว
