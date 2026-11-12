---
name: ec2-cost-cut
description: ลดค่า EC2 แบบวัดก่อนตัด ไล่ดูเครื่องทุกบัญชีทุก region ดึงราคาจริงจาก Pricing API วัด CPU 14 วันและ RAM จริง เปลี่ยนรุ่นเครื่อง (ปิด snapshot เปลี่ยน เปิด ตรวจ container และเว็บ) และตั้งเวลาปิดเปิดด้วย EventBridge Scheduler. Trigger เมื่อพิมพ์ /ec2-cost-cut หรือขอ "ลด cost ec2 / list ec2 ที่รันอยู่ / ย้ายเครื่องไปรุ่นถูกลง / ตั้งเวลาปิดเปิดเครื่อง / ปิดเครื่องตอนกลางคืน".
---

# /ec2-cost-cut

ตัวอย่างจากงานจริง: เครื่องทดสอบ c7i-flex.large → t3.medium ดับ 109 วิ · เครื่อง prod m7i-flex.large → t3.large ดับ 114 วิ · ตั้งเครื่องทดสอบปิด 23:00 เปิด 05:00
‼ ทุกขั้นที่ปิด เปลี่ยน หรือตั้งเวลาเครื่อง prod ต้องได้คำสั่งจากผู้ใช้ในเทิร์นนั้น

## 1. ดูว่ามีอะไรรันอยู่

```bash
bash scripts/list-ec2.sh              # ทุก profile ที่คีย์ใช้ได้ ทุก region + Elastic IP (กรุงเทพ)
```
- profile ที่คีย์ใช้ไม่ได้จะขึ้นว่าข้าม บอกผู้ใช้ด้วย เพราะเครื่องในบัญชีนั้นจะไม่ถูกนับ
- เครื่องที่ปิดอยู่ยังเสียค่าดิสก์และค่า EIP · EIP ที่ไม่ได้ผูกเครื่องก็เสียเงิน
- เครื่องที่ไม่มี EIP ได้ IP ใหม่ทุกครั้งที่ปิดเปิด (ดูว่ามีอะไรผูกกับ IP นั้นไหม เช่น whitelist ของลูกค้า)

## 2. ราคาจริง ไม่เดา

```bash
bash scripts/ec2-price.sh ap-southeast-7 t3.medium t3.large m7i-flex.large c7i-flex.large
```
ราคากรุงเทพ 22/10/2026 ($/ชม.): t3.medium 0.0475 · t3.large 0.095 · c7i-flex.large 0.0831 · m7i-flex.large 0.1018 · t4g.medium 0.0382 · t4g.micro 0.0095

## 3. วัดก่อนตัด

- CPU 14 วันจาก CloudWatch (เฉลี่ย, p95 รายชั่วโมง, พีค 1 นาที):
  `aws cloudwatch get-metric-statistics --namespace AWS/EC2 --metric-name CPUUtilization --dimensions Name=InstanceId,Value=<id> --start-time <14 วันก่อน> --end-time <ตอนนี้> --period 3600 --statistics Average Maximum`
- RAM จริงผ่าน SSM: `free -m` · `swapon --show` · `docker stats --no-stream` · `journalctl -k --since -14d | grep -ci oom`
- ตัดสินใจ:
  - CPU เฉลี่ยต่ำกว่า baseline ของ t3 มาก (t3.medium 20%/vCPU, t3.large 30%) → ใช้ t3 ได้ ค่าเริ่มต้นเป็น credit `unlimited`
  - **ห้ามลด RAM ถ้าเครื่อง build image บนตัวเอง หรือมี service กิน RAM ข้างเคียง** (ตัวอย่าง: เครื่อง prod ที่ใช้ 2.3 GB + build + service ข้างเคียง จึงไป t3.large ไม่ใช่ t3.medium)
  - บัญชี Free plan เปิดได้แค่บางรุ่น (c7i-flex/m7i-flex) อัปเป็น Paid แล้วค่อยย้ายมา t3
  - t4g ถูกกว่าแต่เป็น ARM ต้อง build image arm64 ใหม่ ไม่ใช่แค่เปลี่ยนรุ่น

## 4. เปลี่ยนรุ่นเครื่อง

ก่อนปิดเครื่อง prod:
- เช็ก `restart` policy ของ container ทุกตัว (`unless-stopped` ขึ้นเองหลังบูต แต่ตัวที่ `docker stop` ด้วยมือจะไม่ขึ้น)
- **dump ฐานข้อมูลจริงใหม่** + นับแถว (snapshot ถ่ายหลังเครื่องปิด ถ้าบริการไหนพังตอนโดน kill snapshot ก็ได้สภาพที่พังไปด้วย)
- บริการที่ไม่ตอบ SIGTERM (เช่น service ฝั่ง AI หรือ vector DB บางตัว) ให้หยุดเองก่อน แล้วเปิดเองหลังบูต

```bash
bash scripts/resize-instance.sh <instance-id> <new-type> https://site1 https://site2
```
สคริปต์ทำ: จดรายชื่อ container ที่รันอยู่ → ปิด → snapshot root volume → เปลี่ยนรุ่น → **เปิดเสมอแม้เปลี่ยนรุ่นไม่สำเร็จ** → รอ SSM → รอ container ครบชุดเดิมและหาย `health: starting` → ยิง URL ต้องได้ 200 → บอกเวลาดับ (ตั้ง `AWS_PROFILE` / `AWS_REGION` ที่ด้านบนสคริปต์หรือ export ไว้ก่อน)

ถ้างานมีหลายขั้น (backup + หยุด service + resize + ตรวจหลังบูต) ให้ห่อเป็นสคริปต์รวมไฟล์เดียวแล้วเก็บ log ไว้

## 5. ตั้งเวลาปิดเปิด (EventBridge Scheduler)

1. role ที่ scheduler assume ได้ จำกัดเฉพาะบัญชีและเฉพาะเครื่อง:
   - trust: `scheduler.amazonaws.com` + `Condition StringEquals aws:SourceAccount=<account>`
   - inline policy: `ec2:StartInstances`, `ec2:StopInstances` บน `arn:aws:ec2:<region>:<account>:instance/<id>` เท่านั้น
2. สร้าง schedule สองตัว ใช้เขตเวลาไทยตรง ๆ:
   ```bash
   aws scheduler create-schedule --name <x>-stop --schedule-expression "cron(0 23 * * ? *)" \
     --schedule-expression-timezone Asia/Bangkok --flexible-time-window Mode=OFF --target file://target-stop.json
   ```
   target: `{"Arn":"arn:aws:scheduler:::aws-sdk:ec2:stopInstances","RoleArn":"<role arn>","Input":"{\"InstanceIds\":[\"<id>\"]}"}` (start ใช้ `startInstances`) · เขียน JSON ลงไฟล์แล้วส่ง `file://$(cygpath -m file)` จะไม่เจอปัญหา quote ใน Git Bash
   - role เพิ่งสร้างจะยังใช้ไม่ได้ทันที ต้องลองซ้ำทุก 10 วินาที (เจอจริง 2 รอบ)
3. ตรวจ: `aws scheduler get-schedule` และ `aws iam simulate-principal-policy` ต้อง `allowed` กับเครื่องนี้ และ `implicitDeny` กับเครื่องอื่น
4. ลบ schedule เก่า: `get-schedule` เก็บ config ไว้ก่อน แล้ว `delete-schedule`

## กับดักที่เจอจริง

- **cron ในเครื่องที่ตรงกับช่วงปิดจะไม่รัน** เครื่องทดสอบเป็น UTC และ backup `30 19 * * *` = 02:30 ไทย อยู่ในช่วงปิด 23:00-05:00 → ดู `crontab -l`, `/etc/cron.d/*` และ timezone ของเครื่องก่อนตั้งเวลา
- **โควตา vCPU นับเครื่องที่รันอยู่ทุกเครื่องใน region** (Standard A/C/D/H/I/M/R/T/Z) บัญชีตัวอย่างมี 8 vCPU ถ้าเต็ม schedule เปิดเครื่องจะล้ม (`VcpuLimitExceeded`) เครื่องจะดับทั้งวันโดยไม่มีใครรู้ → ก่อนเปิดเครื่องเพิ่มหรือตั้ง schedule ให้รวม vCPU ของทุกเครื่องที่จะรันพร้อมกัน: `aws service-quotas get-service-quota --service-code ec2 --quota-code L-1216C47A`
- ระบบสิทธิ์ของ Claude Code บล็อก `python ssm_run.py` ตอนรันเองครั้งแรก ("Modify Shared Resources") แต่สคริปต์รวมทุกขั้นไฟล์เดียวผ่านหลังผู้ใช้สั่ง "ดำเนินการได้เลย" · ถ้าโดนบล็อกให้หยุดแล้วยื่นสคริปต์ให้ผู้ใช้รันเอง
- ระบบสิทธิ์บล็อก `rm -f "$OUT"/*` ที่ตัวแปรอาจว่าง → ใช้ `mktemp -d` หรือ `"${OUT:?}"`
- `aws configure list-profiles` แล้ว `sts get-caller-identity` ใน Git Bash ต้อง `tr -d '\r'` ไม่งั้นชื่อ profile มี CR ติดมาแล้วไม่เจอ
