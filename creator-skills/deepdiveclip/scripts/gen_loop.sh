#!/bin/bash
# 19/10/2026 เจนทีละภาพ ทีละ process (กัน batch ตายหลังภาพแรก) retry 3 รอบ ข้ามภาพที่มีแล้ว
OUT=__PROJECT__/gen
: "${CHATGPT_BRIDGE:?ตั้งตัวแปร CHATGPT_BRIDGE เป็นโฟลเดอร์ของ chatgpt-bridge ก่อน}"
cd "$CHATGPT_BRIDGE"
python -c "
import json,io
for p in json.load(io.open('__PROJECT__/src/gen_prompts.json',encoding='utf-8')):
    json.dump([p], io.open('__PROJECT__/gen/_one_'+p['id']+'.json','w',encoding='utf-8'), ensure_ascii=False)
"
for f in $OUT/_one_*.json; do
  id=$(basename "$f" .json); id=${id#_one_}
  for try in 1 2 3; do
    [ -f "$OUT/$id.png" ] && break
    powershell -NoProfile -ExecutionPolicy Bypass -File "__PROJECT__/src/kill_bridge.ps1"
    echo "=== $id try $try $(date +%T)"
    timeout 420 node chatgpt-batch.mjs "$f" "$OUT" 2>&1 | grep -av "pid=" | grep -av "^\[2m" | tail -4
  done
  [ -f "$OUT/$id.png" ] && echo "OK $id" || echo "FAIL $id"
done
powershell -NoProfile -ExecutionPolicy Bypass -File "__PROJECT__/src/kill_bridge.ps1"
echo ALLDONE
