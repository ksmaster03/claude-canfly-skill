#!/usr/bin/env bash
# ยิง chatgpt-bridge ทีละภาพ = ทีละ process (กันอาการ profile lock)
# งานที่มีรูปอ้างอิง (มีไฟล์ <id>.prompt.txt) ใช้ chatgpt-edit.mjs ไม่มีใช้ chatgpt-batch.mjs
# ใช้: bash gen_images.sh <jobs_dir> <out_dir> [id ...]   (ไม่ใส่ id = ทุกงานใน jobs_dir)
# ห้ามรันสองลูปพร้อมกัน ตัว kill ของลูปหนึ่งจะฆ่าเบราว์เซอร์ของอีกลูป
set -u
BRIDGE=${CHATGPT_BRIDGE:?ตั้ง CHATGPT_BRIDGE เป็นโฟลเดอร์ของ chatgpt-bridge ก่อน}
JOBS=$(cygpath -m "$(cd "$1" && pwd)")
mkdir -p "$2"
OUT=$(cygpath -m "$(cd "$2" && pwd)")
shift 2
if [ $# -gt 0 ]; then IDS="$*"; else IDS=$(ls "$JOBS" | grep -E '\.json$' | sed 's/\.json$//' | tr -d '\r'); fi

cd "$BRIDGE" || { echo "ไม่พบ chatgpt-bridge ที่ $BRIDGE"; exit 1; }
for ID in $IDS; do
  for TRY in 1 2 3; do
    if [ -f "$OUT/$ID.png" ]; then echo "[$ID] มีแล้ว"; break; fi
    echo "=== $ID รอบ $TRY ==="
    powershell -NoProfile -ExecutionPolicy Bypass -File kill-chatgpt-chrome.ps1 >/dev/null 2>&1
    sleep 3
    if [ -f "$JOBS/$ID.prompt.txt" ]; then
      REF=$(python -c "import json,sys;print(json.load(open(sys.argv[1],encoding='utf-8'))[0]['ref'])" "$JOBS/$ID.json" | tr -d '\r')
      node chatgpt-edit.mjs "@$JOBS/$ID.prompt.txt" "$REF" "$OUT/$ID.png" 2>&1 | grep -av "pid=" | grep -av "^\[2m" | tail -3
      if [ ! -f "$OUT/$ID.png" ]; then
        echo "[$ID] edit ไม่คืนภาพ ลองกู้จากแชตล่าสุด"
        powershell -NoProfile -ExecutionPolicy Bypass -File kill-chatgpt-chrome.ps1 >/dev/null 2>&1
        sleep 3
        node recover.mjs "$OUT/$ID.png" 2>&1 | tail -2
      fi
    else
      node chatgpt-batch.mjs "$JOBS/$ID.json" "$OUT" 2>&1 | grep -av "pid=" | grep -av "^\[2m" | tail -3
    fi
  done
  [ -f "$OUT/$ID.png" ] || echo "[$ID] ยังไม่ได้ภาพหลังลอง 3 รอบ"
done
powershell -NoProfile -ExecutionPolicy Bypass -File kill-chatgpt-chrome.ps1 >/dev/null 2>&1
echo "ALLDONE"
ls -la "$OUT"/*.png 2>/dev/null | awk '{print $5, $9}'
