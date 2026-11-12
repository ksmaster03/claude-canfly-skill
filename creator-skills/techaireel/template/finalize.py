# -*- coding: utf-8 -*-
"""ประกบภาพกับมิกซ์ที่คุมความดังแล้ว เข้ารหัสเป็นโมโน แล้ววัดผลจริงเทียบเช็กลิสต์
ไม่บีบหรือเพิ่มเกนซ้ำ ความดังจบที่ sound.py แล้ว"""
import re, subprocess
ROOT = "__ROOT__"
r = subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", ROOT + "/out/video_only.mp4", "-i", ROOT + "/out/mix.wav",
                    "-map", "0:v", "-map", "1:a", "-c:v", "copy", "-af", "pan=mono|c0=c0",
                    "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-shortest", ROOT + "/out/reel.mp4"],
                   capture_output=True, text=True)
if r.returncode: raise SystemExit(r.stderr[:400])
txt = subprocess.run(["ffmpeg", "-hide_banner", "-i", ROOT + "/out/reel.mp4", "-af", "ebur128=peak=true", "-f", "null", "-"],
                     capture_output=True, text=True).stderr.split("Summary:")[-1]
I = float(re.search(r"I:\s*(-?[\d.]+) LUFS", txt).group(1))
LRA = float(re.search(r"LRA:\s*(-?[\d.]+) LU", txt).group(1))
TP = float(re.search(r"Peak:\s*(-?[\d.]+) dBFS", txt).group(1))
info = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration:stream=channels,width,height",
                       "-of", "default=nw=1", ROOT + "/out/reel.mp4"], capture_output=True, text=True).stdout
print("ไฟล์สุดท้าย I=%.1f LUFS  LRA=%.1f LU  TP=%.1f dBFS" % (I, LRA, TP))
print(info.strip())
print("ระดับเสียง -14 LUFS   ->", "ผ่าน" if abs(I + 14) <= 1 else "ไม่ผ่าน")
print("พีคจริง <= -1.5 dBTP  ->", "ผ่าน" if TP <= -1.5 else "ไม่ผ่าน")
print("โมโน                  ->", "ผ่าน" if "channels=1" in info else "ไม่ผ่าน")
