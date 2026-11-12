# -*- coding: utf-8 -*-
# 21/10/2026 ประกอบคลิปเจาะลึกฉบับเดี่ยว: parts/silent.mp4 ถึงเฟรม END_FRAME + การ์ดท้าย parts/end_single.mp4 + เสียง audio/master.wav
# ใช้: python src/assemble.py   (ก่อนหน้านั้น concat parts/p0..p3 เป็น silent.mp4 และเรนเดอร์ end_single ด้วย CREDIT)
import subprocess, sys
sys.path.insert(0, '__PROJECT__/src')
from timeline import END_FRAME
P = '__PROJECT__/'
fc = '[0:v]trim=end_frame=%d,setpts=PTS-STARTPTS[a];[1:v]setpts=PTS-STARTPTS[b];[a][b]concat=n=2:v=1:a=0[v]' % END_FRAME
subprocess.run(['ffmpeg', '-hide_banner', '-loglevel', 'error', '-y', '-i', P + 'parts/silent.mp4', '-i', P + 'parts/end_single.mp4',
                '-i', P + 'audio/master.wav', '-filter_complex', fc, '-map', '[v]', '-map', '2:a', '-c:v', 'libx264', '-crf', '16',
                '-preset', 'medium', '-pix_fmt', 'yuv420p', '-r', '24', '-c:a', 'aac', '-b:a', '256k', '-shortest', '-movflags', '+faststart',
                P + 'deepdive.mp4'], check=True)
print('ok -> deepdive.mp4')
