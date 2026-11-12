#!/bin/bash
# prep_song.sh <proj>... : align + mix (take2 bgm, 12 dB) + stills at start+70% -> <proj>/chk_sheet.jpg
# ใช้หลังผ่านตรวจคำเพี้ยน (20 ต.ค. 2569 แผนลงเพลงเช้า)
export PYTHONIOENCODING=utf-8
export PATH="$FFMPEG_BIN:$PATH"
S=~/.claude/skills; BGM=${BGM:-$WORK/lotr-reel/bgm/take2-9768a748.wav}
for P in "$@"; do echo "######## $P"; rm -f $P/asr.json
  python $S/explainreel/scripts/align.py $P $P/vo/voice.wav 2>&1 | grep -E "^ref|^phrases|^total|ratio|unmatched|WARN"
  python $S/explainreel/scripts/mix.py $P $P/vo/voice.wav 12 "$BGM" 2>&1 | tail -1
  T=$(python -c "
import json;tl=json.load(open('$P/timeline.json',encoding='utf-8'))
print(' '.join('%.2f'%(l['start']+0.7*(l['end']-l['start'])) for l in tl['lines']))")
  rm -rf $P/chk; python $S/explainreel/scripts/render_range.py $P shots $P/chk $T > /dev/null 2>&1
  ffmpeg -v error -y -i "$P/chk/s%02d.jpg" -vf "scale=216:-1,tile=7x3" -frames:v 1 $P/chk_sheet.jpg
done
