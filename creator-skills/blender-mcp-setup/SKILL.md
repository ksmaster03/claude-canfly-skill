---
name: blender-mcp-setup
description: ติดตั้ง Blender + uv + mcp-for-blender บน Windows ให้ Claude Code สั่ง Blender ได้ พร้อมวัดความเร็วเรนเดอร์ของเครื่อง. Trigger เมื่อพิมพ์ /blender-mcp-setup หรือขอ "ติดตั้ง Blender MCP", "ต่อ Claude กับ Blender", "ตั้งเครื่องใหม่ทำคลิป 3D", "set up Blender MCP".
---

# blender-mcp-setup — Blender + Claude Code via mcp-for-blender (Windows)

ใช้เมื่อเครื่องยังไม่มี Blender หรือยังไม่ได้ต่อ MCP และต้องการสั่ง Blender จาก Claude Code
ขั้นที่ 1 ถึง 7 รันจริงแล้วเมื่อ 2026-10-13 (Blender 5.2.2 LTS, uv 0.13.0, mcp-for-blender 2.1.9, Windows 11)

## ขั้นตอน

1. **ตรวจเครื่องก่อน** — การ์ดจอ RAM และของที่มีอยู่แล้ว:
   ```powershell
   Get-CimInstance Win32_VideoController | Select-Object Name, DriverVersion
   Get-Command blender, uvx, nvidia-smi -ErrorAction SilentlyContinue
   ```
   ไม่มีการ์ดจอแยก = Cycles บน GPU ใช้ไม่ได้ ให้บอกผู้ใช้ก่อนติดตั้ง

2. **ติดตั้ง** (Blender จะขอ UAC ผู้ใช้ต้องกด Yes เอง ให้รันแบบ background แล้วแจ้งผู้ใช้):
   ```powershell
   winget install --id astral-sh.uv -e --accept-source-agreements --accept-package-agreements --disable-interactivity
   winget install --id BlenderFoundation.Blender -e --accept-source-agreements --accept-package-agreements --disable-interactivity
   ```

3. **รีเฟรช PATH ใน shell เดิม** แล้วหา path เต็มของ uvx:
   ```powershell
   $env:Path = [Environment]::GetEnvironmentVariable('Path','Machine') + ';' + [Environment]::GetEnvironmentVariable('Path','User')
   (Get-Command uvx).Source
   ```

4. **ให้ Blender สร้างโฟลเดอร์ addon ของผู้ใช้** (ยังไม่เคยเปิด Blender = `install-addon` หาโฟลเดอร์ไม่เจอ):
   ```powershell
   $b = (Get-ChildItem "C:\Program Files\Blender Foundation" -Recurse -Filter blender.exe | Select-Object -First 1).FullName
   & $b -b --factory-startup --python-expr "import bpy; print(bpy.utils.user_resource('SCRIPTS', path='addons', create=True))"
   ```

5. **ลง addon แล้วเปิดใช้งานใน preferences**:
   ```powershell
   $env:DISABLE_TELEMETRY='true'; uvx mcp-for-blender install-addon
   & $b -b --python-expr "import bpy, addon_utils
   addon_utils.enable('blender_mcp', default_set=True, persistent=True)
   bpy.ops.wm.save_userpref()
   print('ENABLED=' + str('blender_mcp' in bpy.context.preferences.addons))"
   ```

6. **เขียน `.mcp.json` ในโฟลเดอร์โปรเจกต์** ใช้ path เต็มของ uvx จากขั้น 3:
   ```json
   {
     "mcpServers": {
       "blender": {
         "command": "<path เต็มของ uvx.exe>",
         "args": ["mcp-for-blender"],
         "env": { "BLENDER_MCP_SAFE_MODE": "1", "DISABLE_TELEMETRY": "true" }
       }
     }
   }
   ```

7. **ให้ผู้ใช้เปิด Blender** กด `N` ในหน้าต่าง 3D เลือกแท็บ **MCP for Blender** แล้วกด Start MCP Server จากนั้นยืนยันจากฝั่งเรา:
   ```powershell
   Get-NetTCPConnection -LocalPort 9876 -State Listen
   $c = New-Object Net.Sockets.TcpClient; $c.Connect('127.0.0.1', 9876); $s = $c.GetStream(); $s.ReadTimeout = 15000
   $q = [Text.Encoding]::UTF8.GetBytes('{"type":"get_scene_info","params":{}}'); $s.Write($q,0,$q.Length)
   $buf = New-Object byte[] 65536; $n = $s.Read($buf,0,$buf.Length); [Text.Encoding]::UTF8.GetString($buf,0,$n); $c.Close()
   ```
   ได้ `"status": "success"` พร้อมรายชื่อวัตถุ = ฝั่ง Blender พร้อม

8. **ให้ผู้ใช้เปิด Claude Code ในโฟลเดอร์โปรเจกต์** แล้วอนุมัติ MCP ชื่อ `blender`
   ‼ ยังไม่เคยรันจริง: การเรียกเครื่องมือ MCP จาก Claude Code หลังขั้นนี้

## วัดความเร็วเรนเดอร์

```powershell
& $b -b --factory-startup --python "$env:USERPROFILE\.claude\skills\blender-mcp-setup\scripts\render_test.py" -- <โฟลเดอร์ผลลัพธ์>
```
เรนเดอร์ฉากตั้งต้นที่ 1280x720 ด้วย EEVEE และ Cycles CPU (64 กับ 256 samples) แล้วพิมพ์บรรทัด `RESULT` กับ `CYCLES_DEVICES`
เปิดดูภาพที่ได้ด้วยทุกครั้ง ตัวเลขจากลูกบาศก์ตั้งต้นใช้ประเมินฉากจริงไม่ได้

## ข้อควรระวัง

- **ชื่อแท็บ**: ใน Blender ชื่อ "MCP for Blender" คู่มือเก่าเรียก "BlenderMCP" ผู้ใช้จะหาไม่เจอ
- **ชื่อแพ็กเกจ**: `mcp-for-blender` (ชื่อเดิม `blender-mcp` ยังรันได้)
- **ไม่มี `claude` CLI ใน PATH** เมื่อใช้ผ่าน VS Code extension: ใช้ `.mcp.json` แทน `claude mcp add`
- **`.mcp.json` มีผลเฉพาะ session ที่เปิดในโฟลเดอร์นั้น** session ที่เปิดอยู่ที่อื่นจะไม่เห็นเครื่องมือ
- **`spawn uvx ENOENT`**: โปรแกรมที่เปิดจาก GUI ไม่ได้รับ PATH ของ terminal จึงต้องใช้ path เต็ม
- **ต้องกด Start MCP Server ใหม่** ทุกครั้งที่เปิด Blender
- **`blender -b --python-expr` ไม่คืน exit code ผิดพลาด** ถ้าไม่ใส่ `--python-exit-code <n>` และอย่ากรอง output ด้วย `Select-String` จนมองไม่เห็นข้อผิดพลาด
- **safe mode**: ตาม README ไม่บล็อกเรนเดอร์ เซฟ และ import/export ‼ ยังไม่เคยรันจริง: การ bake simulation ภายใต้ safe mode
- **socket ไม่มีการยืนยันตัวตน**: ต้องผูกที่ 127.0.0.1 เท่านั้น
- **ไม่ต้องติ๊ก** Poly Haven, Sketchfab, Hyper3D, Hunyuan หรือ telemetry ถ้างานไม่ได้ใช้

## ตรวจว่าสำเร็จ

`uvx mcp-for-blender addon-paths` แสดงโฟลเดอร์พร้อม `(exists)`, ขั้น 5 พิมพ์ `ENABLED=True`, และขั้น 7 ได้ `"status": "success"`
