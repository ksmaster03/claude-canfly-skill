#!/bin/bash
# สร้างเสียงทีละบรรทัดผ่าน $PROJECTS/lumina-bridge  (ต้องล็อกอินใน bridge แล้ว: node lumina-login.mjs)
# ชื่อเสียงอ่านจาก <proj>/voice/<who>.txt  (เช่น voice/L.txt = ลินดา, voice/K.txt = โกสินทร์3) เขียนเป็นไฟล์ UTF-8 ห้ามส่งชื่อไทยผ่าน argument
# ข้ามบรรทัดที่มี mp3 แล้ว หยุดทันทีเมื่อบรรทัดไหนล้ม ไม่วนลองซ้ำ (ข้อตกลงของ Lumina ห้ามบอต)
# ใช้: bash gen_vo.sh <proj> [ตัวกรองชื่อไฟล์ เช่น 16]
P=$(cd "$1" && pwd); F=${2:-}
cd $PROJECTS/lumina-bridge || exit 1
for f in "$P"/vo/lines/${F}*_?.txt; do
  b=$(basename "$f" .txt); out="$P/vo/lines/$b.mp3"; who=${b##*_}
  [ -s "$out" ] && { echo "skip $b"; continue; }
  v="$P/voice/$who.txt"; [ -f "$v" ] || { echo "ไม่มี $v"; exit 1; }
  echo "== $b"
  node lumina-tts.mjs "$f" "$out" --voice-file "$v" --headless > "$P/vo/lines/$b.log" 2>&1
  rc=$?; tail -1 "$P/vo/lines/$b.log"; grep -h "ใช้ไป" "$P/vo/lines/$b.log"
  [ $rc -eq 0 ] || { echo "FAILED $b exit $rc (ดู $P/vo/lines/$b.log และ $PROJECTS/lumina-bridge/fail.png)"; exit $rc; }
done
echo ALL_DONE
