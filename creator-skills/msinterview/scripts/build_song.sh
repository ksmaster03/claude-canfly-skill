#!/bin/bash
# build_song.sh <slug>=<Name> : ทำครบ 1 เพลงหลังสร้างเสียงเสร็จ ($WORK/<slug>-reel)
#   1) concat_vo (โกสินทร์ x1.08)  2) ฉบับ YouTube ไม่มีฉากเปิดใน <slug>-reel-yt  3) ฉบับ FB/TikTok มีฉากเปิด (ต้องมี "intro" ใน clip.json)
#   ใช้ผลถอดเสียง (asr.json) ชุดเดียวกันทั้งสองฉบับ แสดงบรรทัด unmatched ให้ตรวจ
export PYTHONIOENCODING=utf-8
export PATH="$FFMPEG_BIN:$PATH"
S=~/.claude/skills; BGM=$WORK/lotr-reel/bgm/take2-9768a748.wav
pn=$1; p=${pn%%=*}; n=${pn#*=}; SRC=$WORK/$p-reel; Y=$WORK/$p-reel-yt
stills() { local P=$1; local T=$(python -c "
import json;tl=json.load(open('$P/timeline.json',encoding='utf-8'))
print(' '.join('%.2f'%(l['start']+0.7*(l['end']-l['start'])) for l in tl['lines']))")
  rm -rf $P/chk; python $S/explainreel/scripts/render_range.py $P shots $P/chk $T > /dev/null 2>&1
  ffmpeg -v error -y -i "$P/chk/s%02d.jpg" -vf "scale=216:-1,tile=7x3" -frames:v 1 $P/chk_sheet.jpg; }
echo "######## $p"
python $S/msinterview/scripts/concat_vo.py $SRC | tail -1
rm -f $SRC/asr.json
rm -rf $Y; mkdir -p $Y/vo; cp -r $SRC/frames $Y/; cp $SRC/scenes.html $SRC/cover.jpg $SRC/youtube.txt $SRC/caption.txt $Y/; cp $SRC/vo/voice.wav $Y/vo/
python - "$SRC/clip.json" "$Y/clip.json" <<'PY'
import json,sys
c=json.load(open(sys.argv[1],encoding='utf-8')); c.pop('intro',None)
json.dump(c,open(sys.argv[2],'w',encoding='utf-8'),ensure_ascii=False,indent=1)
PY
echo "[yt] $(python $S/explainreel/scripts/align.py $Y $Y/vo/voice.wav 2>&1 | grep -E 'unmatched')"
cp $Y/asr.json $SRC/asr.json
python $S/explainreel/scripts/mix.py $Y $Y/vo/voice.wav 12 $BGM > /dev/null 2>&1
stills $Y
bash $S/msinterview/scripts/render_song.sh $Y=$n 2>&1 | grep -E "LUFS|SHORT_VIDEO"
if python -c "import json,sys;sys.exit(0 if 'intro' in json.load(open('$SRC/clip.json',encoding='utf-8')) else 1)"; then
  echo "[main] $(python $S/explainreel/scripts/align.py $SRC $SRC/vo/voice.wav 2>&1 | grep -E 'unmatched')"
  python $S/msinterview/scripts/add_intro.py $SRC && python $S/msinterview/scripts/mix_intro.py $SRC $SRC/vo/voice.wav $BGM | tail -1
  stills $SRC
  bash $S/msinterview/scripts/render_song.sh $SRC=$n 2>&1 | grep -E "LUFS|SHORT_VIDEO"
else echo "[main] ไม่มี intro ใน clip.json ข้ามฉบับ FB/TikTok"; fi
echo "######## $p END"
