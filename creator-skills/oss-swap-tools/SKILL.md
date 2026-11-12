---
name: oss-swap-tools
description: คู่มือ 7 เครื่องมือ open source ที่ใช้แทนแอปเสียเงินรายเดือน (OpenSEO แทน Semrush, Chatwoot แทน Intercom, OpenWhispr แทน Wispr Flow, Cap แทน Loom, AppFlowy แทน Notion, VoiceStudio แทน ElevenLabs, Open Higgsfield แทน Higgsfield) ติดตั้งอย่างไร เสียเงินตรงไหน สกิลลูกตัวไหนใช้ต่อ. Trigger เมื่อพิมพ์ /oss-swap-tools หรือขอ "ติดตั้ง OpenSEO / Chatwoot / OpenWhispr / Cap / AppFlowy / VoiceStudio / Open Higgsfield" หรือ "หาแอปฟรีแทน Semrush Loom Notion ElevenLabs".
---

# /oss-swap-tools: 7 เครื่องมือฟรีแทนค่าสมาชิก

ที่มา: รีล David Iya (ดู `/repo-swap-reel`) ตรวจ repo ด้วย gh และ clone ไว้แล้ว 7 พ.ย. 2569
โค้ดต้นฉบับ (shallow clone): `$PROJECTS/_github\<owner>__<repo>` อัปเดตด้วย `git -C <dir> pull`
**ยังไม่ได้ติดตั้งหรือรันตัวไหนบนเครื่องนี้เลย** คำสั่งด้านล่างคัดจาก README ของแต่ละ repo

| เครื่องมือ | แทน | ติดตั้ง (จาก README) | เสียเงินตรงไหน | สกิลลูกบนเครื่อง |
|---|---|---|---|---|
| OpenSEO `every-app__open-seo` | Semrush/Ahrefs | ใช้ hosted (app.openseo.so, ราว $10/เดือน) หรือ self-host ด้วย Docker (`docs/SELF_HOSTING_DOCKER.md`) | ข้อมูล SEO ทั้งหมดมาจาก DataForSEO API ต้องมีคีย์และจ่ายตามใช้ | `openseo-*` 12 ตัว (ต้องต่อ MCP `https://app.openseo.so/mcp` ก่อน) |
| Chatwoot `chatwoot__chatwoot` | Intercom/Zendesk | Docker image `chatwoot/chatwoot` หรือ Heroku/DigitalOcean (ดู docs ของ Chatwoot) | ฟรีเมื่อ self-host; ฟีเจอร์ enterprise และ Captain AI แยก | ไม่มี |
| OpenWhispr `OpenWhispr__openwhispr` | Wispr Flow | ตัวติดตั้ง Windows `.exe` จาก GitHub Releases | ฟรีกับโมเดลในเครื่อง (Whisper/Parakeet); คลาวด์ต้องใช้คีย์ตัวเอง | `openwhispr-cli`, `openwhispr-api` |
| Cap `CapSoftware__Cap` | Loom | แอปจาก cap.so/download; self-host เว็บด้วย `docker compose up -d` | Cap Cloud เสียเงิน; self-host/อัดเก็บในเครื่องฟรี | ไม่มี |
| AppFlowy `AppFlowy-IO__AppFlowy` | Notion | แอปเดสก์ท็อปจาก GitHub Releases; self-host ตามคู่มือ appflowy.com | ฟรีแบบใช้ในเครื่อง; AI/cloud มีแผนเสียเงิน | ไม่มี |
| VoiceStudio `debpalash__VoiceStudio` | ElevenLabs | Windows: ตัวติดตั้งจาก Releases (README มีคำสั่ง `irm https://voicestudio.sh/install.ps1 \| iex` แต่ควรใช้ไฟล์จาก Releases แทนการรันสคริปต์จากเน็ต) | ฟรีในเครื่อง แต่ต้องมี GPU ถึงจะเร็ว เครื่องนี้ไม่มีการ์ดจอแยก | `voicestudio` (REST API/MCP ของแอป) |
| Open Higgsfield `wide-trace__open-higgsfield` | Higgsfield | `pnpm install` + `pnpm dev` (Next.js, พอร์ต 3000) | ต้องตั้ง `HF_API_BASE_URL` เป็น API สร้างภาพ/วิดีโอของผู้ให้บริการ จ่ายตามใช้ ไม่ใช่ฟรีจริง; repo ไม่มี license | ไม่มี |

## ก่อนติดตั้งตัวไหน

- ถามผู้ใช้ก่อน การติดตั้งแอปและการรัน Docker เปลี่ยนเครื่อง ไม่ทำเองโดยไม่ได้สั่ง
- พอร์ตที่ชนบนเครื่องนี้: 80 (IIS), 3000, 3100, 8088, 8089, 6800 (panya), 8765 (VS Code Web) ใช้ตัวอื่น
- RAM จำกัด: panya + Onyx Lite กินอยู่แล้ว Chatwoot/Cap self-host ใช้ Postgres/MySQL + Redis เพิ่ม
- คีย์ API (DataForSEO, ผู้ให้บริการโมเดล) ใส่ใน `.env` ที่ gitignore ห้ามพิมพ์คีย์ออกจอ

## เชื่อมกับงานคลิป

- VoiceStudio อาจเป็นทางสำรองของ Lumina (โคลนเสียงในเครื่อง) แต่ยังไม่ได้ทดสอบภาษาไทย และไม่มี GPU (เทียบ VoxCPM2 ที่ใช้ CPU ราว 100 นาที/คลิป) ทดสอบก่อนเสนอผู้ใช้
- OpenWhispr ใช้พิมพ์ด้วยเสียงในเครื่อง ไม่เกี่ยวกับสายงานคลิปโดยตรง
