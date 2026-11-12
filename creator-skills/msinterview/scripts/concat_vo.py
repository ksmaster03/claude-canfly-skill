# -*- coding: utf-8 -*-
# ต่อเสียงทีละบรรทัด <proj>/vo/lines/NN_<who>.mp3 เป็น <proj>/vo/voice.wav
# ตัดเงียบหัวท้าย ปรับดังเท่ากันที่ -18 LUFS (เสียงโคลนคนละตัวดังไม่เท่ากัน)
# เว้น 0.4 วินาทีเมื่อเปลี่ยนคนพูด 0.25 วินาทีเมื่อคนเดิมพูดต่อ (เดิม 0.55/0.3)
# เร่งเสียงโกสินทร์ (K) 8% ด้วย atempo เสียงไม่แหลม ผู้ใช้เลือก 21 ต.ค. 2569 เพราะคนดูบ่นว่าพูดช้า
#   ปรับได้ด้วย env SPEED_K / SPEED_L (ค่าเริ่มต้น 1.08 / 1.0)
#   ช่องว่างปรับด้วย env GAP_SWITCH / GAP_SAME (ค่าเริ่มต้น 0.4 / 0.25) คลิปพูดเร็ว Claude 2.0 (29 ต.ค. 2569) ใช้ 0.22 / 0.12
# ใช้: python concat_vo.py <proj>
import glob, os, subprocess, sys
import numpy as np
import soundfile as sf
sys.stdout.reconfigure(encoding="utf-8")
D = os.path.abspath(sys.argv[1])
SR = 48000
GAP = (float(os.environ.get("GAP_SWITCH", "0.4")), float(os.environ.get("GAP_SAME", "0.25")))
SPEED = {"K": float(os.environ.get("SPEED_K", "1.08")), "L": float(os.environ.get("SPEED_L", "1.0")), "S": float(os.environ.get("SPEED_S", "1.0")), "M": float(os.environ.get("SPEED_M", "1.08"))}
# พี่ไมค์ (M, 30 ต.ค. 2569) ใช้เสียง Lumina "สมชาย" กดต่ำลง ~1.4 เซมิโทนให้อุ่น ตามที่ผู้ใช้ขอ "เสียงต่ำนิดหน่อย ฟังดูอบอุ่น"
VOICE_FX = {"M": "rubberband=pitch=" + os.environ.get("PITCH_M", "0.92") + ":formant=preserved,bass=g=2.5:f=150,treble=g=-1.5:f=6000"}
files = sorted(glob.glob(f"{D}/vo/lines/[0-9][0-9]_*.mp3"))
os.makedirs(f"{D}/vo/norm", exist_ok=True)
AF = ("silenceremove=start_periods=1:start_threshold=-45dB:start_silence=0.05,"
      "areverse,silenceremove=start_periods=1:start_threshold=-45dB:start_silence=0.12,areverse,"
      "loudnorm=I=-18:TP=-2:LRA=11")
out, prev, log = [], None, []
for f in files:
    b = os.path.basename(f)[:-4]
    who = b.split("_", 1)[1]
    n = f"{D}/vo/norm/{b}.wav"
    sp = SPEED.get(who, 1.0)
    af = AF + (f",atempo={sp}" if abs(sp - 1.0) > 1e-6 else "") + ("," + VOICE_FX[who] if who in VOICE_FX else "")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", f, "-af", af, "-ar", str(SR), "-ac", "1", n], check=True)
    x, _ = sf.read(n)
    if prev is not None:
        out.append(np.zeros(int((GAP[0] if who != prev else GAP[1]) * SR)))
    t0 = sum(len(a) for a in out) / SR
    out.append(x)
    log.append(f"{b}  start {t0:6.2f}  len {len(x)/SR:5.2f}")
    prev = who
y = np.concatenate(out)
sf.write(f"{D}/vo/voice.wav", y, SR, subtype="PCM_16")
print("\n".join(log))
print(f"ความเร็ว K x{SPEED['K']} L x{SPEED['L']} · รวม {len(files)} บรรทัด  ยาว {len(y)/SR:.1f} วินาที -> vo/voice.wav")
