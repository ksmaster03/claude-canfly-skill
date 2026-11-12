#!/usr/bin/env bash
# ยิงทีละภาพ = ทีละ process (วิธีจาก ref_chatgpt_bridge_profile_lock)
cd $PROJECTS/chatgpt-bridge
OUT=/d/tmp/reel-process-guide/img
for ID in s00_hero s01_research s02_script s03_images s04_voice s05_check s06_sync s07_music s08_render s09_qc_cover s10_publish; do
  for TRY in 1 2 3; do
    if [ -f "$OUT/$ID.png" ]; then echo "[$ID] มีแล้ว"; break; fi
    echo "=== $ID รอบ $TRY ==="
    powershell -NoProfile -ExecutionPolicy Bypass -File kill-chatgpt-chrome.ps1 >/dev/null 2>&1
    sleep 3
    node chatgpt-batch.mjs "$OUT/$ID.json" "$OUT" 2>&1 | grep -av "pid=" | grep -av "^\[2m" | tail -4
  done
  [ -f "$OUT/$ID.png" ] || echo "[$ID] ยังไม่ได้ภาพหลังลอง 3 รอบ"
done
ls -la "$OUT"/*.png 2>/dev/null | awk '{print $5, $9}'
