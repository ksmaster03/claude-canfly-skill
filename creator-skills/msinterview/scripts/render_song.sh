#!/bin/bash
# render_song.sh <proj>=<Name>... : 3-part render, concat + master.wav -> <Name>_msinterview_9x16.mp4,
# + _youtube.mp4 (cover.jpg 0.5 s first) + _tiktok.mp4 when master_tt.wav exists (intro left silent for the TikTok library song), seam frames -> final_sheet.jpg
export PYTHONIOENCODING=utf-8
export PATH="$FFMPEG_BIN:$PATH"
R=~/.claude/skills/explainreel/scripts/render_range.py
for pn in "$@"; do P=${pn%%=*}; n=${pn#*=}
  N=$(python -c "import json,math;print(math.ceil(json.load(open('$P/timeline.json',encoding='utf-8'))['total']*30))"); a=$((N/3)); b=$((2*N/3))
  (python $R $P 0 $a $P/part1.mp4 > $P/r1.log 2>&1 & python $R $P $a $b $P/part2.mp4 > $P/r2.log 2>&1 & python $R $P $b -1 $P/part3.mp4 > $P/r3.log 2>&1 & wait)
  cd $P && printf "file 'part1.mp4'\nfile 'part2.mp4'\nfile 'part3.mp4'\n" > parts.txt && ffmpeg -v error -y -f concat -safe 0 -i parts.txt -c copy silent.mp4 && ffmpeg -v error -y -i silent.mp4 -i master.wav -map 0:v -map 1:a -c:v copy -c:a aac -b:a 192k -shortest ${n}_msinterview_9x16.mp4 && { [ ! -f master_tt.wav ] || ffmpeg -v error -y -i silent.mp4 -i master_tt.wav -map 0:v -map 1:a -c:v copy -c:a aac -b:a 192k -shortest ${n}_msinterview_tiktok.mp4; } && ffmpeg -y -loglevel error -loop 1 -t 0.5 -framerate 30 -i cover.jpg -f lavfi -t 0.5 -i anullsrc=r=48000:cl=stereo -i ${n}_msinterview_9x16.mp4 -filter_complex "[0:v]scale=1080:1920,setsar=1,format=yuv420p,fps=30[c];[2:v]fps=30,setsar=1,format=yuv420p[m];[2:a]aformat=sample_rates=48000:channel_layouts=stereo[ma];[c][1:a][m][ma]concat=n=2:v=1:a=1[v][a]" -map "[v]" -map "[a]" -c:v libx264 -crf 18 -preset medium -c:a aac -b:a 192k -movflags +faststart ${n}_msinterview_youtube.mp4
  echo "$P $(ffprobe -v error -show_entries format=duration -of csv=p=0 ${n}_msinterview_9x16.mp4) $(ffprobe -v error -show_entries format=duration -of csv=p=0 ${n}_msinterview_youtube.mp4) $(ffmpeg -hide_banner -i ${n}_msinterview_9x16.mp4 -af ebur128 -f null - 2>&1 | grep -A1 Integrated | tail -1)"
  # กันวิดีโอขาด (23 ต.ค. 2569: Figure.09 part2/3 เรนเดอร์ไม่ครบตอนรันพร้อมกัน ได้คลิป 103 วิ จากที่ควร 162)
  python -c "import sys;d=float(sys.argv[1]);t=$N/30;sys.exit(0 if d>=t-0.5 else 1)" $(ffprobe -v error -show_entries format=duration -of csv=p=0 silent.mp4) || echo "!! SHORT_VIDEO $P silent.mp4 สั้นกว่า timeline ($N เฟรม) เรนเดอร์ใหม่"
  mkdir -p fchk; i=0; for t in $(python -c "print(' '.join('%.2f'%x for x in ($a/30-0.1,$a/30+0.1,$b/30-0.1,$b/30+0.1,$N/30-1)))"); do ffmpeg -v error -y -ss $t -i ${n}_msinterview_9x16.mp4 -frames:v 1 fchk/s$i.jpg; i=$((i+1)); done
  ffmpeg -v error -y -i "fchk/s%d.jpg" -vf "scale=240:-1,tile=5x1" -frames:v 1 final_sheet.jpg
done; echo ALL_RENDERED
