# standard/ — สกิลทั้งหมดในรูปแบบมาตรฐาน Claude Code

รวมสกิลจากชุด **A–D ทั้งหมด 142 ตัว** แปลงเป็นโครงสร้างมาตรฐานที่ Claude Code โหลด/ติดตั้งได้ตรงๆ:
```
standard/
  <slug>/
    SKILL.md   (frontmatter: name + description + trigger พร้อมใช้)
```

- ชื่อโฟลเดอร์ = ค่า `name:` ใน frontmatter (slug อังกฤษ a-z 0-9 -)
- **ข้ามไฟล์ pointer (status: merged) 9 ตัว** — เพราะ canonical ครอบคลุมแล้ว จึงไม่มีตัวซ้ำ
- ตรวจแล้ว: ไม่มี slug ชนกัน, ทุกไฟล์มี `name` + `description` ครบ

## ที่มา (142 = A+B+C+D − pointer)
| ชุด | ที่มา | จำนวน |
|-----|-------|-------|
| A | อาชีพ_skill (ไทย/RIASEC) | 34 |
| B | pro-bundle (หมวดสากล) | 69 |
| C | commands (คำสั่งลัด หน้า 1-2) | 20 |
| D | jobsdb-ai-skills | 19 |
| **รวม** | | **142** |

## ติดตั้งทั้งหมดเข้า Claude Code
```powershell
Copy-Item "D:\Project\claude-skills-bundle\standard\*" "$env:USERPROFILE\.claude\skills\" -Recurse -Force
```
หรือเลือกเฉพาะตัวที่ต้องการ:
```powershell
Copy-Item "D:\Project\claude-skills-bundle\standard\blog-post" "$env:USERPROFILE\.claude\skills\" -Recurse -Force
```

## สร้างใหม่
รันซ้ำได้ด้วย `python ../_make_standard.py` (อ่านจากชุด A-D ต้นฉบับ แล้ว gen ใหม่ทั้ง standard/)

> ⚠️ ก่อนติดตั้งทั้ง 142 ตัวจริง: สกิลจำนวนมากที่มี trigger กว้างอาจเด้งทำงานเองบ่อย แนะนำติดตั้งเฉพาะที่ใช้จริงก่อน หรือปรับ `description` ให้ trigger แคบลง
