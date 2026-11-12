#!/usr/bin/env bash
# ใช้: bash render_song.sh <proj> <Name>   ต้องมี <proj>/bg.png และ <proj>/song.wav
# ได้ <proj>/<Name>_9x16.mp4 ภาพนิ่ง + คลื่นเสียงสีทอง ความดัง -14 LUFS และ chk60.jpg (เฟรมวินาทีที่ 60)
set -e
export PATH="$FFMPEG_BIN:$PATH"
P="$1"; N="$2"; cd "$P"
DUR=$(ffprobe -v error -show_entries format=duration -of csv=p=0 song.wav | cut -d. -f1)
ffmpeg -v error -y -loop 1 -framerate 30 -i bg.png -i song.wav -filter_complex \
 "[0:v]format=yuv420p[bg];[1:a]asplit[a1][a2];[a1]aformat=channel_layouts=mono,showwaves=s=900x150:mode=cline:rate=30:colors=0xFFD79A:draw=full:scale=sqrt,format=rgba,colorchannelmixer=aa=0.7[w];[bg][w]overlay=90:900:shortest=1[v];[a2]loudnorm=I=-14:TP=-1.5:LRA=11[a]" \
 -map "[v]" -map "[a]" -c:v libx264 -preset medium -crf 23 -tune stillimage -pix_fmt yuv420p -c:a aac -b:a 192k -t "$DUR" -movflags +faststart "${N}_9x16.mp4"
ffmpeg -v error -y -ss 60 -i "${N}_9x16.mp4" -frames:v 1 -q:v 3 chk60.jpg
ffprobe -v error -show_entries format=duration,size -of default=nw=1 "${N}_9x16.mp4"
ffmpeg -hide_banner -i "${N}_9x16.mp4" -af ebur128 -f null - 2>&1 | grep -E '^\s+I:' | tail -1
