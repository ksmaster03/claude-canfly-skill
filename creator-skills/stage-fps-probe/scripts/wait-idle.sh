#!/bin/bash
# Waits until nobody has touched the machine for $1 seconds (default 30) and the screen is not locked. Gives up after $2 tries (5 s each).
HERE="$(cd "$(dirname "$0")" && pwd)"
need=${1:-30}; tries=${2:-720}
for i in $(seq 1 "$tries"); do
  s=$(powershell -NoProfile -ExecutionPolicy Bypass -File "$HERE/idle.ps1" 2>/dev/null)
  v=$(echo "$s" | head -1 | sed -E 's/idle=([0-9]+)s.*/\1/')
  if ! echo "$s" | grep -q locked && [ "$v" -ge "$need" ]; then echo "go: $s"; exit 0; fi
  sleep 5
done
echo "never idle"; exit 1
