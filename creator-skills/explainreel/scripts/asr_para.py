# -*- coding: utf-8 -*-
# Kosin 17/10/2026 ถอดเสียงไฟล์รายย่อหน้า ใช้ตรวจว่าคำที่แก้ฟังตรงบทแล้ว
# ใช้: python asr_para.py <a.mp3> [b.mp3 ...]
import sys, subprocess
sys.stdout.reconfigure(encoding="utf-8")
from faster_whisper import WhisperModel
m = WhisperModel("mobiuslabsgmbh/faster-whisper-large-v3-turbo", device="cpu", compute_type="int8")
for f in sys.argv[1:]:
    dur = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", f], capture_output=True, text=True).stdout.strip()
    segs, _ = m.transcribe(f, language="th", vad_filter=False)
    print(f.replace("\\", "/").split("/")[-1], dur, "|", " ".join(s.text.strip() for s in segs), flush=True)
