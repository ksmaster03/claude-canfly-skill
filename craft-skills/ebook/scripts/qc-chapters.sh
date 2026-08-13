#!/usr/bin/env bash
# qc-chapters.sh <project-dir> — ตรวจโครงสร้างบททุกบทก่อน build
# ใช้: bash qc-chapters.sh /d/Project/<slug>-ebook
set -u
DIR="${1:-.}"
cd "$DIR" || { echo "ไม่พบโฟลเดอร์ $DIR"; exit 1; }

echo "== โครงสร้างบท (ต้อง h1=1, jam3=1, img=0) =="
printf "%-6s %8s %7s %5s %5s %5s %5s %4s\n" บท ตัวอักษร kotlin ts มุม จำ3 รูป h1
for f in raw/ch*.md; do
  [ -e "$f" ] || { echo "ไม่มีไฟล์ raw/ch*.md เลย"; exit 1; }
  n=$(basename "$f" .md)
  printf "%-6s %8s %7s %5s %5s %5s %5s %4s\n" \
    "$n" \
    "$(wc -c < "$f")" \
    "$(grep -c '^```kotlin' "$f")" \
    "$(grep -c -E '^```(typescript|tsx|ts|js|jsx)$' "$f")" \
    "$(grep -c '^### มุม' "$f")" \
    "$(grep -c 'จำ 3 ข้อ' "$f")" \
    "$(grep -c '^!\[' "$f")" \
    "$(head -1 "$f" | grep -c '^# ')"
done

echo
echo "== บรรทัดแรกที่ไม่ใช่ชื่อบท (ต้องว่าง) =="
for f in raw/ch*.md; do head -1 "$f" | grep -q '^# ' || echo "  $f -> $(head -1 "$f")"; done

echo
echo "== มีคำว่า 'บทที่' นำหน้าชื่อบท (ต้องว่าง — build ใส่เลขให้เอง) =="
for f in raw/ch*.md; do head -1 "$f" | grep -q 'บทที่' && echo "  $f -> $(head -1 "$f")"; done

echo
echo "== ราคาเป็นตัวเงิน (ตรวจว่าตั้งใจหรือหลุด) =="
grep -n 'บาท\|ดอลลาร์\|USD\|\$[0-9]' raw/*.md | head -10

echo
echo "== URL ในบท (ปกติควรมีเฉพาะบทแหล่งอ้างอิงท้ายเล่ม) =="
grep -c 'https\?://' raw/*.md | grep -v ':0$'

echo
echo "== code fence: เช็กว่าทุกก้อนที่เปิดมีภาษากำกับ (fence ทั้งหมดควร = 2 × ก้อนที่มีภาษา) =="
for f in raw/ch*.md; do
  all=$(grep -c '^```' "$f"); lang=$(grep -c '^```[a-zA-Z]' "$f")
  [ "$all" -eq $((lang * 2)) ] || echo "  $(basename "$f"): fence $all แต่มีภาษา $lang ก้อน -> มี fence เปล่า $((all - lang * 2)) จุด (ดูด้วย: grep -n '^\`\`\`$' $f)"
done

echo
echo "== ภาษาของ fence ที่ใช้ทั้งเล่ม =="
grep -h '^```[a-z]' raw/*.md | sort | uniq -c | sort -rn
