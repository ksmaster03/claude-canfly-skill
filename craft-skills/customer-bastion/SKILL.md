---
name: customer-bastion
description: ตั้ง bastion บน AWS ที่มี IP สาธารณะคงที่ (Elastic IP) ให้ลูกค้า whitelist แล้วให้ทีม SSH/RDP/ต่อ port เข้าระบบลูกค้าผ่าน SSM โดยไม่เปิด port ขาเข้าเลย พร้อมทดสอบ whitelist ด้วยเครื่องลูกค้าจำลอง. Trigger เมื่อพิมพ์ /customer-bastion หรือขอ "ลูกค้าให้ใช้ fix public ip / ทำ bastion host / ขอ IP คงที่ไว้ whitelist / SSH เข้าเครื่องลูกค้าผ่าน bastion / เปิดปิด bastion".
---

# /customer-bastion

ใช้เมื่อลูกค้าบังคับว่าต้องเข้าระบบของเขาจาก IP สาธารณะที่คงที่เท่านั้น
ตัวอย่างจากงานจริง: ลูกค้า A ใช้ Azure VM ที่เปิดแค่ SSH ให้ IP ที่ whitelist

## ทำไมเป็นแบบนี้

- **Elastic IP คือของที่ลูกค้า whitelist** ไม่ใช่ตัวเครื่อง เปลี่ยนเครื่อง (เช่นไป Windows) ก็ย้าย EIP เดิมไปติด ลูกค้าไม่ต้องแก้อะไร
- เครื่อง t4g.micro Amazon Linux 2023 **ไม่มี inbound rule เลย** ทีมเข้าผ่าน SSM Session Manager (สิทธิ์ผูกกับ IAM มี log) ไม่มี SSH key ให้หลุด
- traffic ที่ต่อผ่าน `AWS-StartPortForwardingSessionToRemoteHost` ออกไปหาลูกค้าจาก EIP ของ bastion
- ค่าใช้จ่ายที่ ap-southeast-7 (Pricing API 21/10/2026): t4g.micro $0.0095/ชม. + gp3 8 GB + IPv4 $0.005/ชม. ≈ **$11/เดือน** ถ้าเปิด 24 ชม. ปิดเครื่องแล้วยังเสียค่า EIP ~$3.6/เดือน
- เครื่องนี้ไม่ได้แก้ IP ขาออกของเซิร์ฟเวอร์อื่น ถ้าเซิร์ฟเวอร์ prod ต้องเรียก API ลูกค้า ต้องติด EIP ที่เครื่องนั้นเอง (เครื่องที่ไม่มี EIP ได้ IP ใหม่ทุกครั้งที่ปิดเปิด)

## ก่อนเริ่ม

- AWS CLI v2 + Session Manager plugin (ติดตั้งตามเอกสาร AWS)
- สคริปต์ใน `scripts/` อ่านค่าจากตัวแปรสภาพแวดล้อม `AWS_PROFILE`, `AWS_REGION` (ดีฟอลต์ `ap-southeast-7`) และ `EXPECTED_ACCOUNT` (เลขบัญชี 12 หลักที่อนุญาตให้สร้าง ดีฟอลต์เป็นค่าตัวอย่าง `123456789012` ต้อง export เป็นของคุณก่อนรัน) แก้ `NAME` ที่ส่วนบนของ `create-bastion.sh` ได้
- ก๊อป `scripts/` ไปไว้ในโฟลเดอร์งาน (เช่น `$WORK/customer-bastion/`) เพราะ `create-bastion.sh` เขียน `bastion-state.env` (IID, SG, ALLOC, EIP) ไว้ข้างตัวมัน และ `connect.sh` อ่านไฟล์นั้น
- **การสร้าง EC2/IAM/EIP เป็นการสร้าง resource บนคลาวด์ ต้องได้คำสั่งจากผู้ใช้ในเทิร์นนั้น**

## ขั้นตอน

1. ตรวจโควตา vCPU ของ region ก่อน (`VcpuLimitExceeded` = เต็ม) แล้วพรีวิว:
   ```bash
   bash create-bastion.sh            # แสดงแผน ไม่สร้างอะไร
   bash create-bastion.sh --apply    # role+profile (SSM อย่างเดียว) → SG ไม่มี inbound → EC2 → EIP → รอ SSM → ตรวจ IP ขาออก
   ```
   ขั้นสุดท้ายสั่ง `curl checkip.amazonaws.com` บน bastion ต้องได้ EIP ตรงกัน
2. ทดสอบ whitelist แบบครบวง (ประมาณ 3 นาที ไม่ถึง 1 บาท ลบของทดสอบเองแม้ล้ม):
   ```bash
   bash test-whitelist.sh
   ```
   สร้างเครื่องลูกค้าจำลองที่ **สิงคโปร์** (SG รับ tcp 8080 จาก EIP/32 เท่านั้น) แล้วทดสอบ 3 ทาง: PC ต่อตรงต้องโดนบล็อก · bastion ต่อได้และปลายทางเห็น EIP · PC ผ่าน `connect.sh forward` ปลายทางเห็น EIP
3. ส่ง EIP ให้ลูกค้า whitelist
4. ใช้งานประจำ:
   ```bash
   bash connect.sh ssh user@customer-host       # เปิด bastion เองถ้าปิด → tunnel localhost:2222 → ssh → ปิด session ตอนออก
   bash connect.sh forward 10.0.1.10 3389      # RDP ที่ localhost:13389
   bash connect.sh shell                        # shell บน bastion
   bash connect.sh start | stop | status        # ปิดเครื่องประหยัดเงิน EIP ไม่เปลี่ยน
   ```

## ทดสอบ SSH ที่ใช้รหัสผ่านแบบไม่ให้รหัสหลุด

- **ห้ามส่งรหัสผ่านผ่าน `aws ssm send-command`** คำสั่งถูกเก็บเป็นประวัติในคอนโซล AWS
- ให้ ssh ในเครื่องเราอ่านรหัสจากไฟล์ผ่าน askpass:
  ```bash
  printf '#!/bin/sh\nhead -n 1 "/path/to/pwd.txt" | tr -d "\\r\\n"\n' > askpass.sh; chmod +x askpass.sh   # บรรทัดแรกเท่านั้น ผู้ใช้มักต่อความลับอื่นท้ายไฟล์เดิม
  SSH_ASKPASS=$PWD/askpass.sh SSH_ASKPASS_REQUIRE=force DISPLAY=none \
    bash connect.sh ssh user@host -o PubkeyAuthentication=no 'hostname; lsblk; df -h; sudo -n true && echo sudo-ok'
  ```
- ถ้าไฟล์รหัสอยู่ใน git repo ให้ใส่โฟลเดอร์นั้นใน `.git/info/exclude` ทันที (เจอจริง: ไฟล์รหัสผ่านอยู่ใน repo และไม่ได้ ignore)
- ตรวจครั้งแรกให้อ่านอย่างเดียว: hostname, OS, CPU/RAM, ดิสก์ที่ยังไม่ mount, sudo, docker, ขาออกอินเทอร์เน็ต แล้วจด host key fingerprint ไว้ให้ลูกค้ายืนยัน

## กับดักที่เจอจริง

- **Git Bash แปลง `/aws/service/...` และ `/dev/xvda` เป็นพาธ Windows** → `export MSYS_NO_PATHCONV=1` (สคริปต์ตั้งไว้แล้ว) · ไฟล์ที่ส่งให้ aws.exe ใช้ `file://$(cygpath -m path)`
- **คำสั่ง SSM คำสั่งแรกที่ส่งตอน agent เพิ่ง Online ค้าง Pending ไม่จบ** (รอ 4 นาทีแล้วยังค้าง) → cancel แล้วส่งใหม่ (`create-bastion.sh` ทำเองแล้ว)
- **โควตา vCPU นับต่อ region** บัญชีหนึ่งที่กรุงเทพเต็ม 8/8 ทำให้สร้างเครื่องทดสอบไม่ได้ → ไปสร้างที่สิงคโปร์แทน (ใกล้ของจริงกว่าด้วย เพราะอยู่คนละเครือข่าย)
- **bastion ที่เปิดค้างกินโควตาของเครื่องอื่น** ถ้ามีเครื่องที่ schedule เปิดตอนเช้า (เช่น เครื่องทดสอบที่ตั้งเปิด 05:00) แล้วโควตาเต็ม เครื่องนั้นจะเปิดไม่ขึ้นทั้งวัน → ใช้เสร็จแล้ว `connect.sh stop` ทุกครั้ง และเช็กโควตาด้วย `aws service-quotas get-service-quota --service-code ec2 --quota-code L-1216C47A` เทียบกับ vCPU ที่รันอยู่
- ทดสอบ banner ด้วย `head -c 60 </dev/tcp/host/22` จะค้าง เพราะ banner SSH สั้นกว่า 60 ไบต์ ทำให้ดูเหมือนต่อไม่ได้ ให้ใช้ `ssh` จริงหรือ `timeout 8 bash -c "</dev/tcp/host/22"` ดูแค่ว่า port เปิด
- shell แบบโต้ตอบของ SSM พังใน mintty (Git Bash หน้าต่างแยก) ให้ใช้ PowerShell หรือ Windows Terminal · `connect.sh ssh` ใช้ใน terminal ของ VS Code ได้
- `connect.sh ssh` ใส่ `HostKeyAlias=<host จริง>` ไม่งั้น known_hosts จะจดเป็น `[127.0.0.1]:2222` แล้วชนกันเมื่อมีหลายลูกค้า
- ระบบสิทธิ์ของ Claude Code บล็อก `rm -f "$VAR"/*` ที่ตัวแปรอาจว่าง → ใช้ `"${VAR:?}"` หรือโฟลเดอร์ใหม่แทนการลบ

## ที่ยังไม่ได้ทำ (ยังไม่เคยรันจริง)

- IAM user รายคนที่มีสิทธิ์แค่ `ssm:StartSession` กับ bastion ตัวนี้ (ตอนนี้ใช้ access key ของ admin ซึ่งห้ามแจก)
- เก็บ log ของ session ลง S3 / CloudWatch สำหรับ audit
- bastion แบบ Windows สำหรับลูกค้าที่บังคับให้ใช้ VPN client ของตัวเอง (FortiClient ฯลฯ)
