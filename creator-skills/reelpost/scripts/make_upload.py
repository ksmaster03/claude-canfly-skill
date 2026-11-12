# -*- coding: utf-8 -*-
# Kosin 17/10/2026 ทำไฟล์อัปโหลดคลิปแนวตั้ง 3 ไฟล์ จากคลิปที่เสร็จแล้ว
#   <name>_youtube.mp4       ปกเป็นเฟรมแรก 0.5 วินาที (YouTube Shorts ใช้เฟรมจากคลิปเป็นปก) H.264 คุณภาพเต็ม
#   <name>_youtube_hevc.mp4  ฉบับเดียวกันบีบเป็น HEVC ให้ไม่เกินเพดาน (ใช้อัปผ่าน claude-in-chrome)
#   <name>_fb_hevc.mp4       ไม่มีเฟรมปก (Facebook อัปภาพขนาดย่อแยกได้) HEVC ไม่เกินเพดาน
# เพดาน: file_upload ของ claude-in-chrome รับรวมไม่เกิน 10 MB ต่อครั้ง จึงตั้งเป้า 9.3 MB และเช็กขนาดจริง ถ้าเกิน 9.8 MB บีบซ้ำที่บิตเรต 85%
# ใช้: python make_upload.py <clip.mp4> [cover.jpg]   (ไฟล์ออกข้างคลิป ชื่อ <name> คือชื่อคลิปตัด _9x16 ออก)
# HEVC ช้า: คลิป 127 วินาทีใช้ราว 15 นาที ให้รันด้วย run_in_background และอย่าทำงานใน Chrome ไปพร้อมกัน (CPU เต็ม หน้าเว็บค้าง)
import os, subprocess, sys

src = os.path.abspath(sys.argv[1])
cover = os.path.abspath(sys.argv[2]) if len(sys.argv) > 2 else os.path.join(os.path.dirname(src), "cover.jpg")
d = os.path.dirname(src)
name = os.path.splitext(os.path.basename(src))[0]
for suf in ("_9x16", "_lumina_9x16"):
    if name.endswith(suf):
        name = name[: -len(suf)]
TARGET_MB, LIMIT_MB, AUDIO_K, VMAX_K = 9.3, 9.8, 96, 1100


def run(a):
    subprocess.run(["ffmpeg", "-v", "error", "-y"] + a, check=True)


def dur(p):
    return float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", p],
                                capture_output=True, text=True).stdout.strip())


def hevc(i, o, vk):
    run(["-i", i, "-c:v", "libx265", "-b:v", f"{vk}k", "-maxrate", f"{int(vk * 1.8)}k", "-bufsize", f"{int(vk * 2.4)}k",
         "-tag:v", "hvc1", "-preset", "medium", "-x265-params", "log-level=error:pools=4",
         "-c:a", "aac", "-b:a", f"{AUDIO_K}k", "-movflags", "+faststart", o])


def fit(i, o):
    t = dur(i)
    vk = min(VMAX_K, int(TARGET_MB * 8 * 1024 / t - AUDIO_K - 8))
    hevc(i, o, vk)
    mb = os.path.getsize(o) / 1048576
    if mb > LIMIT_MB:
        vk = int(vk * 0.85)
        hevc(i, o, vk)
        mb = os.path.getsize(o) / 1048576
    print(f"{os.path.basename(o)}  {t:.1f}s  video {vk}k  {mb:.2f} MB", "‼ ยังเกินเพดาน" if mb > LIMIT_MB else "")


yt = os.path.join(d, f"{name}_youtube.mp4")
if not os.path.exists(cover):
    sys.exit(f"ไม่เจอปก {cover} ทำด้วย /clipcover ก่อน")
run(["-loop", "1", "-t", "0.5", "-framerate", "30", "-i", cover, "-f", "lavfi", "-t", "0.5", "-i", "anullsrc=r=48000:cl=stereo", "-i", src,
     "-filter_complex", "[0:v]scale=1080:1920,setsar=1,format=yuv420p,fps=30[c];[2:v]fps=30,setsar=1,format=yuv420p[m];"
     "[2:a]aformat=sample_rates=48000:channel_layouts=stereo[ma];[c][1:a][m][ma]concat=n=2:v=1:a=1[v][a]",
     "-map", "[v]", "-map", "[a]", "-c:v", "libx264", "-crf", "18", "-preset", "medium", "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", yt])
print(f"{os.path.basename(yt)}  {dur(yt):.1f}s  {os.path.getsize(yt) / 1048576:.1f} MB (ปกเฟรมแรก 0.5 วิ)")
fit(yt, os.path.join(d, f"{name}_youtube_hevc.mp4"))
fit(src, os.path.join(d, f"{name}_fb_hevc.mp4"))
