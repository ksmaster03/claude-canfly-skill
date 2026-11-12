#!/bin/bash
# build_many.sh [-j 2] <slug>=<Name> ... : รัน build_song.sh หลายเพลงพร้อมกัน (ค่าเริ่มต้น 2 เพลง เครื่องนี้ CPU 8 เธรด มากกว่านี้ช้าลงทั้งหมด)
J=2; if [ "$1" = "-j" ]; then J=$2; shift 2; fi
printf '%s\n' "$@" | xargs -P $J -I{} bash ~/.claude/skills/msinterview/scripts/build_song.sh {}
echo BUILD_MANY_END
