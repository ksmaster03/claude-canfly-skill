#!/usr/bin/env bash
# Generate the footage stills one image per browser process (the batch tends to die after
# its first image), with retries; images that already exist are skipped, so re-running resumes.
# Usage: bash run_footage.sh [id-filter]
BR="$PROJECTS/chatgpt-bridge"
HERE="$(cd "$(dirname "$0")" && pwd)"
OUT="$HERE/out"; TMP="$HERE/.one"; mkdir -p "$OUT" "$TMP"
cd "$BR" || exit 1
ids=$(node -e "const p=require(process.argv[1]);console.log(p.map(x=>x.id).filter(i=>!process.argv[2]||i.includes(process.argv[2])).join(' '))" "$HERE/prompts.json" "$1")
for id in $ids; do
  [ -f "$OUT/$id.png" ] && { echo "skip $id"; continue; }
  node -e "const fs=require('fs');const p=require(process.argv[1]).filter(x=>x.id===process.argv[2]);fs.writeFileSync(process.argv[3],JSON.stringify(p))" "$HERE/prompts.json" "$id" "$TMP/$id.json"
  for try in 1 2 3; do
    powershell -NoProfile -ExecutionPolicy Bypass -File "$BR/kill-chatgpt-chrome.ps1" >/dev/null 2>&1
    sleep 3
    node chatgpt-ref.mjs "$TMP/$id.json" "$OUT" 2>&1 | grep -a "\[batch\]" | grep -avE "generating|rendering|waiting"
    [ -f "$OUT/$id.png" ] && { echo "OK $id (try $try)"; break; }
    echo "retry $id ($try)"
  done
  [ -f "$OUT/$id.png" ] || echo "FAILED $id"
done
ls "$OUT"
