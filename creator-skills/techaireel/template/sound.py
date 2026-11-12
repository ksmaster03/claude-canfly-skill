# -*- coding: utf-8 -*-
"""สร้างเสียงประกอบ วางตามจังหวะภาพ แล้วมิกซ์กับเสียงพากย์และเพลง

ชั้นเสียง
  VO   เสียงพากย์ Gemini ทีละประโยค วางตาม cue ใน timeline
  SFX  สังเคราะห์เอง (คลังมีแค่ whoosh 3 ตัว) วางตอนกราฟิกเข้า ไม่ใช่ตอนคัต
  BGM  Deep Space Sector 9 วนต่อตรงรอยบาร์ ดักลงใต้เสียงพูดอัตโนมัติ

ผลลัพธ์ out/mix.wav สเตอริโอ 48k ให้ master.py ยุบโมโนและคุมความดังต่อ
"""
import io, json, os, subprocess, wave
import numpy as np

ROOT = r"__ROOT__"
SR = 48000
BGM = r"$MEDIA/bgm/Deep Space Sector 9 - Ezra Lipp.mp3"
WHOOSH = r"$MEDIA/sfx/whoosh_01.wav"
BAR = 1.3937                  # จาก catalog.json วัดไว้ 172.2 BPM
rng = np.random.default_rng(7)

tl = json.load(io.open(os.path.join(ROOT, "script/timeline.json"), encoding="utf-8"))
END = tl["totalDur"] + tl.get("outro", 3.0)
N = int(END * SR) + SR


def decode(path, ch):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", path, "-f", "f32le", "-ac", str(ch),
                          "-ar", str(SR), "-"], capture_output=True).stdout
    x = np.frombuffer(raw, dtype=np.float32)
    return x.reshape(-1, ch) if ch > 1 else x


def db(v):
    return 10 ** (v / 20)


def place(track, clip, t, gain=1.0):
    i = int(t * SR)
    if i < 0:
        clip, i = clip[-i:], 0
    j = min(len(track), i + len(clip))
    if j > i:
        track[i:j] += clip[:j - i] * gain


# ---------------- สังเคราะห์ SFX ----------------
def env_exp(n, tau):
    return np.exp(-np.arange(n) / (tau * SR))


def sfx_click():
    """คลิกเมาส์: noise สั้นกรองสูง + tick 2.4 kHz"""
    n = int(0.03 * SR)
    noise = rng.standard_normal(n) * env_exp(n, 0.0025)
    noise = np.diff(np.concatenate([[0], noise]))           # high-pass แบบง่าย
    tick = np.sin(2 * np.pi * 2400 * np.arange(n) / SR) * env_exp(n, 0.004) * 0.6
    body = np.sin(2 * np.pi * 180 * np.arange(n) / SR) * env_exp(n, 0.006) * 0.5
    x = noise * 0.5 + tick + body
    return x / np.abs(x).max()


def sfx_key():
    n = int(0.022 * SR)
    f = rng.uniform(1800, 3200)
    x = rng.standard_normal(n) * env_exp(n, 0.0018)
    x = np.diff(np.concatenate([[0], x])) + 0.4 * np.sin(2 * np.pi * f * np.arange(n) / SR) * env_exp(n, 0.003)
    return x / np.abs(x).max()


def sfx_pop():
    """ป๊อปนุ่มตอนกรอบไฮไลต์ขึ้น: sine กวาดขึ้น 520 ไป 880 Hz"""
    n = int(0.11 * SR)
    t = np.arange(n) / SR
    f = 520 + 360 * (t / t[-1])
    ph = 2 * np.pi * np.cumsum(f) / SR
    x = np.sin(ph) * env_exp(n, 0.035) * np.minimum(1, t / 0.004)
    return x / np.abs(x).max()


def sfx_chime():
    """ระฆังเบา ๆ ปิดคลิป: สามฮาร์มอนิกของ E6"""
    n = int(1.6 * SR)
    t = np.arange(n) / SR
    x = sum(a * np.sin(2 * np.pi * f * t) * env_exp(n, d) for f, a, d in
            [(1318.5, 1.0, 0.55), (2637, 0.35, 0.25), (1975.5, 0.25, 0.4)])
    x *= np.minimum(1, t / 0.003)
    return x / np.abs(x).max()


def sfx_riser(dur=1.1):
    """noise กวาดขึ้นก่อนเข้าช่วงตัวอย่างใช้งาน: sub 70 Hz + noise 2 ถึง 8 kHz ตามสูตรที่วัดมา"""
    n = int(dur * SR)
    t = np.arange(n) / SR
    ramp = (t / dur) ** 2
    noise = rng.standard_normal(n)
    # กรองแบบ one-pole ที่ความถี่ตัดเลื่อนขึ้น
    out = np.zeros(n); y = 0.0
    for i in range(n):
        fc = 2000 + 6000 * ramp[i]
        a = np.exp(-2 * np.pi * fc / SR)
        y = (1 - a) * noise[i] + a * y
        out[i] = noise[i] - y
    sub = np.sin(2 * np.pi * 70 * t) * ramp * 0.8
    x = (out * 0.6 + sub) * ramp
    return x / np.abs(x).max()


def stereo(m):
    return np.stack([m, m], axis=1)


os.makedirs(os.path.join(ROOT, "sfx"), exist_ok=True)
CLICK, POP, CHIME, RISER = sfx_click(), sfx_pop(), sfx_chime(), sfx_riser()
whoosh = decode(WHOOSH, 1)

# ---------------- ชั้นเสียงพากย์ ----------------
vo = np.zeros(N, dtype=np.float64)
for c in tl["cues"]:
    x = decode(os.path.join(ROOT, "audio_gemini", c["audio"]), 1)
    place(vo, x, c["start"])


def compress(x, thr_db=-20.0, ratio=3.0, attack_ms=8, release_ms=140, win_ms=15):
    """คอมเพรสเซอร์แบบนุ่มตาม RMS ลด crest factor ของเสียงพูด Gemini ก่อนเข้าลิมิตเตอร์
    ไม่ทำตรงนี้ ลิมิตเตอร์ท้ายสายต้องกดเกนเฉลี่ย 4.4 dB จนเสียงพูดบี้ (วัดแล้ว)"""
    from scipy.ndimage import uniform_filter1d
    blk = int(SR / 1000)
    nb = len(x) // blk
    ms = uniform_filter1d((x[: nb * blk] ** 2).reshape(nb, blk).mean(axis=1), size=win_ms)
    lvl = 10 * np.log10(ms + 1e-12)
    over = np.maximum(0, lvl - thr_db)
    target = -over * (1 - 1 / ratio)
    g = np.empty(nb); y = 0.0
    a_at, a_rl = 1 - np.exp(-1 / attack_ms), 1 - np.exp(-1 / release_ms)
    for i in range(nb):
        y += (target[i] - y) * (a_at if target[i] < y else a_rl)
        g[i] = y
    gs = db(np.repeat(g, blk))
    gs = np.pad(gs, (0, len(x) - len(gs)), constant_values=1.0)
    return x * gs


vo /= np.abs(vo).max()
vo = compress(vo)                                                     # ชั้นแรก คุมความดังช่วงยาว
nz = vo[np.abs(vo) > 1e-4]
print("crest factor เสียงพูดหลังคอมเพรส %.1f dB" % (20 * np.log10(np.abs(vo).max() / np.sqrt(np.mean(nz ** 2)))))
vo *= db(-3) / np.abs(vo).max()                       # ให้พีคเสียงพูดอยู่ที่ -3 dBFS ก่อนมิกซ์

# ---------------- ชั้น SFX วางตามกราฟิกที่ขึ้นจอ ----------------
sfx = np.zeros(N, dtype=np.float64)
log = []
place(sfx, whoosh, 0.02, db(-16)); log.append((0.02, "whoosh เปิดคลิป"))
for m in tl["marks"]:
    if m["type"] == "focus":
        place(sfx, POP, m["start"] - 0.45, db(-21)); log.append((m["start"] - 0.45, "pop  " + m["label"]))
    elif m["type"] == "click":
        place(sfx, CLICK, m["start"], db(-12)); log.append((m["start"], "click " + m["label"]))
    elif m["type"] == "type":
        t, stop, k = m["start"], max(m["end"], m["start"] + 1.2), 0
        while t < stop:
            place(sfx, sfx_key(), t, db(-24 + rng.uniform(-3, 2))); k += 1
            t += rng.uniform(0.055, 0.12)
        log.append((m["start"], "typing %d ครั้ง %s" % (k, m["label"])))

cs = tl["cardsStart"]
place(sfx, RISER, cs - 1.15, db(-20)); log.append((cs - 1.15, "riser เข้าช่วงตัวอย่าง"))
place(sfx, whoosh, cs - 0.2, db(-12)); log.append((cs - 0.2, "whoosh การ์ด"))
for i in range(3):
    place(sfx, POP, cs - 0.2 + i * 0.18, db(-22)); log.append((cs - 0.2 + i * 0.18, "pop การ์ด %d" % (i + 1)))
for cid in (30, 31, 32):
    c = next(q for q in tl["cues"] if q["id"] == cid)
    place(sfx, CLICK, c["start"] - 0.4, db(-20)); log.append((c["start"] - 0.4, "tick เน้นการ์ด %d" % (cid - 29)))
ct = tl["ctaStart"]
place(sfx, whoosh, ct - 0.35, db(-13)); log.append((ct - 0.35, "whoosh เข้าฉากปิด"))
place(sfx, POP, ct - 0.05, db(-20)); log.append((ct - 0.05, "pop ปุ่มติดตามขึ้น"))
place(sfx, CLICK, tl["ctaClick"], db(-11)); log.append((tl["ctaClick"], "click ปุ่มติดตาม"))
place(sfx, CHIME, tl["ctaClick"] + 0.12, db(-19)); log.append((tl["ctaClick"] + 0.12, "chime ติดตามแล้ว"))

# ---------------- ชั้นเพลง วนต่อตรงรอยบาร์ ----------------
music = decode(BGM, 2).astype(np.float64)
loop_from = int(round(6 * BAR * SR))                 # วนกลับไปที่บาร์ 6 หลังช่วงอินโทร
xf = int(2 * BAR * SR)                                # ครอสเฟดสองบาร์
bed = music.copy()
while len(bed) < N:
    seg_end = len(bed) - int(2 * BAR * SR)            # ตัดทิ้งสองบาร์ท้าย ไม่เอาช่วงเพลงจบ
    tail = bed[:seg_end]
    nxt = music[loop_from:]
    ramp = np.linspace(0, 1, xf)[:, None]
    joined = tail[-xf:] * np.cos(ramp * np.pi / 2) + nxt[:xf] * np.sin(ramp * np.pi / 2)
    bed = np.concatenate([tail[:-xf], joined, nxt[xf:]])
bed = bed[:N]

# ดักเพลงใต้เสียงพูด: envelope ของ VO แบบ attack เร็ว release ช้า
hop = int(0.01 * SR)
frames = np.abs(vo[: (len(vo) // hop) * hop]).reshape(-1, hop).max(axis=1)
active = (frames > db(-38)).astype(float)
envv = np.zeros_like(active); y = 0.0
for i, a in enumerate(active):
    y = y + (a - y) * (0.35 if a > y else 0.025)       # ขึ้นใน ~30 ms ลงใน ~400 ms
    envv[i] = y
duck = np.repeat(envv, hop)
duck = np.pad(duck, (0, N - len(duck)), constant_values=0)

# วัด RMS เพลงเพื่อวางระดับให้แน่นอน ไม่เดา
m_rms = np.sqrt(np.mean(bed[int(10 * SR):int(60 * SR)] ** 2))
mask = np.pad(np.repeat(active, hop), (0, N - len(active) * hop)).astype(bool)
speech = vo[mask] if active.any() else vo
v_rms = np.sqrt(np.mean(speech ** 2))
UNDER, OPEN = -21.0, -12.0                             # เพลงเบากว่าเสียงพูดเท่านี้ dB ตอนพูด / ตอนเงียบ
g_under = v_rms * db(UNDER) / m_rms
g_open = v_rms * db(OPEN) / m_rms
gain = g_open + (g_under - g_open) * duck

t = np.arange(N) / SR
fade_in = np.minimum(1, t / 0.6)
fade_out = np.clip((END - t) / 2.4, 0, 1)
gain = gain * fade_in * fade_out
bgm = bed * gain[:, None]

# ยุบเป็นโมโนตรงนี้เลย แชนเนลซ้ายขวาเหมือนกันเป๊ะ master จะได้ไม่มีปัญหาเกนตอน downmix
mono = vo + sfx + bgm.mean(axis=1)
mono = mono[: int(END * SR)]


def limit(x, ceiling_db=-2.6, look_ms=5, release_ms=80):
    """ลิมิตเตอร์แบบ lookahead เขียนเอง เพราะ alimiter บนเครื่องนี้ไม่จำกัดพีค (วัดแล้วชน 0 dB)"""
    from scipy.ndimage import minimum_filter1d
    from scipy.signal import resample_poly
    c = db(ceiling_db)
    # ตรวจพีคบนสัญญาณขยาย 4 เท่า เพื่อจับพีคระหว่างตัวอย่างเสียง ซึ่ง AAC ดันขึ้นมาได้ถึง +0.8 dB
    # รอบที่ตรวจแค่ตัวอย่างเสียงปกติ ผ่านใน wav แต่ไฟล์สุดท้ายตกเกณฑ์ที่ -1.2 dBTP
    up = np.abs(resample_poly(x, 4, 1))
    up = up[: (len(up) // 4) * 4].reshape(-1, 4).max(axis=1)
    up = np.pad(up, (0, len(x) - len(up)), constant_values=0)
    need = np.minimum(1.0, c / np.maximum(up, 1e-9))
    L = int(look_ms * SR / 1000)
    g = minimum_filter1d(need, size=2 * L + 1, mode="nearest")      # ลดเกนล่วงหน้าก่อนพีคมาถึง
    blk = int(SR / 1000)                                             # ทำ release ทีละ 1 ms ให้เร็ว
    nb = len(g) // blk
    gb = g[: nb * blk].reshape(nb, blk).min(axis=1)
    out = np.empty(nb); y = 1.0; rel = 1 - np.exp(-1.0 / release_ms)
    for i in range(nb):
        y = gb[i] if gb[i] < y else y + (gb[i] - y) * rel
        out[i] = y
    gs = np.repeat(out, blk)
    gs = np.pad(gs, (0, len(x) - len(gs)), constant_values=gs[-1])
    return x * np.minimum(gs, g)


def lufs(x):
    tmp = os.path.join(ROOT, "out/_probe.wav")
    with wave.open(tmp, "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes(np.clip(x * 32767, -32768, 32767).astype(np.int16).tobytes())
    txt = subprocess.run(["ffmpeg", "-hide_banner", "-i", tmp, "-af", "ebur128=peak=true", "-f", "null", "-"],
                         capture_output=True, text=True).stderr.split("Summary:")[-1]
    import re
    I = float(re.search(r"I:\s*(-?[\d.]+) LUFS", txt).group(1))
    TP = float(re.search(r"Peak:\s*(-?[\d.]+) dBFS", txt).group(1))
    return I, TP


TARGET = -14.0
g = 1.0
for it in range(9):                      # ไล่เกนก่อนลิมิต จนความดังหลังลิมิตเข้าเป้า
    y = limit(mono * g)
    I, TP = lufs(y)
    print("รอบ %d  เกน %+.2f dB  ได้ I=%.2f LUFS  TP=%.2f dBFS" % (it + 1, 20 * np.log10(g), I, TP))
    # หยุดทันทีที่เข้าเกณฑ์ ±1 LU ถ้าไล่ให้ถึง -14 เป๊ะ ลิมิตเตอร์จะบีบเสียงพูดหนักจนแตก
    # (วัดแล้ว: ดันเกนเพิ่ม 7 dB ได้ความดังเพิ่มแค่ 0.5 LU)
    if abs(I - TARGET) <= 1.0 and TP <= -2.0:
        break
    g *= db((TARGET - I) * 1.6)          # ลิมิตเตอร์กินเกนบางส่วน จึงดันเกินไปหน่อยต่อรอบ
pre = mono * g
gr = 20 * np.log10(np.maximum(np.abs(y), 1e-9) / np.maximum(np.abs(pre), 1e-9))
loud = np.abs(pre) > db(-20)
print("ลิมิตเตอร์กดเกน: เฉลี่ย %.2f dB  หนักสุด %.2f dB  สัดส่วนตัวอย่างที่ถูกกดเกิน 3 dB %.2f%%" % (
    gr[loud].mean(), gr.min(), (gr < -3).mean() * 100))
mix = np.stack([y, y], axis=1)

with wave.open(os.path.join(ROOT, "out/mix.wav"), "wb") as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
    w.writeframes(np.clip(mix * 32767, -32768, 32767).astype(np.int16).tobytes())

io.open(os.path.join(ROOT, "rec/sfx_log.txt"), "w", encoding="utf-8").write(
    "\n".join("%7.2f  %s" % r for r in sorted(log)))
print("ความยาวมิกซ์ %.2f วิ" % (len(mix) / SR))
print("เพลงตอนพูดเบากว่าเสียงพากย์ %.0f dB  ตอนเงียบ %.0f dB" % (UNDER, OPEN))
print("วนเพลงกลับที่ %.2f วิ ครอสเฟด %.2f วิ" % (loop_from / SR, xf / SR))
print("วาง SFX %d จุด" % len(log))
for r in sorted(log)[:12]:
    print("  %7.2f  %s" % r)
