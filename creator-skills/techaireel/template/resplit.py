# -*- coding: utf-8 -*-
"""ตัดเสียง Gemini ที่ยิงเป็นก้อนกลับเป็นรายประโยค โดยไม่ยิง API ซ้ำ

สองวิธีที่ลองแล้วพัง (วัดมาจริง)
1. เลือกช่องเงียบที่ยาวที่สุด: Gemini หยุดกลางประโยคได้นานถึง 2.9 วิ ยาวกว่ารอยต่อจริง
2. ทำนายรอยต่อจากสัดส่วนความยาวรอบ edge-tts: จังหวะของสองเสียงต่างกันเกินไป ก้อนแรกผิด 4 ประโยค

วิธีนี้: ถอดเสียงทั้งก้อนด้วย whisper ได้ช่วงข้อความพร้อมเวลา แล้วเทียบจำนวนตัวอักษรสะสม
กับบท หารอยจบของ segment ที่ตรงกับรอยจบประโยคที่สุด แล้วตัดกลางช่องเงียบตรงนั้น
จากนั้นย่อช่องเงียบกลางประโยคที่ยาวเกินให้เหลือช่วงหายใจปกติ
"""
import io, json, os, re, wave
import numpy as np
from faster_whisper import WhisperModel

ROOT = r"__ROOT__"
OUT = os.path.join(ROOT, "audio_gemini")
RAW = os.path.join(OUT, "_chunks")
SR, CHUNK = 24000, 6
INNER_MAX, INNER_TO = 0.45, 0.30     # ช่องเงียบกลางประโยคที่ยาวกว่า 0.45 วิ ย่อเหลือ 0.30 วิ


def read_wav(p):
    with wave.open(p, "rb") as w:
        return np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float32) / 32768


def write_wav(p, x):
    with wave.open(p, "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes(np.clip(x * 32768, -32768, 32767).astype(np.int16).tobytes())


def quiet_mask(x):
    hop = int(SR * 0.01)
    env = np.array([np.sqrt(np.mean(x[i:i + hop] ** 2)) + 1e-9 for i in range(0, len(x) - hop, hop)])
    db = 20 * np.log10(env)
    return db < (np.percentile(db, 70) - 24)


def silence_runs(q, min_len=0.15):
    runs, s = [], None
    for i, v in enumerate(q):
        if v and s is None: s = i
        elif not v and s is not None:
            if (i - s) * 0.01 >= min_len: runs.append((s * 0.01, i * 0.01))
            s = None
    return runs


def nchars(t):
    return len(re.sub(r"[\s.,!?]", "", t))


def collapse_inner(x):
    """ย่อช่องเงียบกลางประโยคที่ยาวเกิน ให้จังหวะไม่ยืด"""
    q = quiet_mask(x)
    runs = silence_runs(q, INNER_MAX)
    out, pos = [], 0
    for a, b in runs:
        ia, ib = int(a * SR), int(b * SR)
        if ia <= int(0.1 * SR) or ib >= len(x) - int(0.1 * SR):
            continue                               # เงียบหัวท้ายปล่อยไว้ ตัดทีหลัง
        keep = int(INNER_TO * SR / 2)
        out.append(x[pos:ia + keep]); pos = ib - keep
    out.append(x[pos:])
    return np.concatenate(out), len(runs)


def trim(x, pad=0.06):
    q = quiet_mask(x)
    sp = np.where(~q)[0]
    if len(sp) == 0:
        return x
    a = max(0, int((sp[0] * 0.01 - pad) * SR))
    b = min(len(x), int(((sp[-1] + 1) * 0.01 + pad) * SR))
    return x[a:b]


model = WhisperModel("small", device="cpu", compute_type="int8")
data = json.load(io.open(os.path.join(ROOT, "script/script.json"), encoding="utf-8"))
lines = data["lines"]
rows = []

for c in range(0, len(lines), CHUNK):
    group = lines[c:c + CHUNK]
    path = os.path.join(RAW, "chunk_%02d.wav" % (c // CHUNK))
    x = read_wav(path)
    segs = [(s.start, s.end, s.text) for s in model.transcribe(path, language="th", vad_filter=False)[0]]

    # ตัวอักษรสะสมของ segment กับของบท ในหน่วยสัดส่วน
    seg_c = np.cumsum([nchars(t) for _, _, t in segs]); seg_c = seg_c / seg_c[-1]
    line_c = np.cumsum([nchars(ln["text"]) for ln in group]); line_c = line_c / line_c[-1]

    # เลือกรอยจบ segment สำหรับแต่ละรอยจบประโยค เรียงลำดับ ไม่ซ้ำ ใช้ DP
    K, M = len(group) - 1, len(segs) - 1
    INF = 1e9
    cost = np.full((K, M), INF); back = np.full((K, M), -1)
    for j in range(M):
        cost[0, j] = abs(seg_c[j] - line_c[0])
    for k in range(1, K):
        best, arg = INF, -1
        for j in range(M):
            if j >= 1 and cost[k - 1, j - 1] < best:
                best, arg = cost[k - 1, j - 1], j - 1
            if arg >= 0:
                cost[k, j] = best + abs(seg_c[j] - line_c[k]); back[k, j] = arg
    j = int(np.argmin(cost[K - 1])); picks = []
    for k in range(K - 1, -1, -1):
        picks.append(j); j = back[k, j]
    picks.reverse()

    # เวลาตัด = กลางช่องเงียบที่ครอบรอยต่อระหว่าง segment picks[k] กับ picks[k]+1
    runs = silence_runs(quiet_mask(x))
    cuts = []
    for p in picks:
        t_end, t_next = segs[p][1], segs[p + 1][0]
        mid_guess = (t_end + t_next) / 2
        near = min(runs, key=lambda r: abs((r[0] + r[1]) / 2 - mid_guess))
        cuts.append((near[0] + near[1]) / 2)

    edges = [0.0] + cuts + [len(x) / SR]
    for ln, a, b in zip(group, edges[:-1], edges[1:]):
        piece = trim(x[int(a * SR):int(b * SR)])
        piece, n_in = collapse_inner(piece)
        piece = trim(piece)
        f = os.path.join(OUT, "line_%02d.wav" % ln["id"])
        write_wav(f, piece)
        ln["audio"] = os.path.basename(f)
        ln["dur"] = round(len(piece) / SR, 3)
        heard = " ".join(t for s0, s1, t in segs if s0 >= a - 0.2 and s1 <= b + 0.2)
        rows.append((ln["id"], ln["dur"], n_in, ln["text"], heard.strip()))
    print("ก้อน %d ตัดที่ %s" % (c // CHUNK + 1, ", ".join("%.2f" % t for t in cuts)))

io.open(os.path.join(ROOT, "script/script.json"), "w", encoding="utf-8").write(
    json.dumps(data, ensure_ascii=False, indent=2))

io.open(os.path.join(ROOT, "rec/resplit_check.txt"), "w", encoding="utf-8").write(
    "\n".join("%2d %5.2f ย่อ%d\n   บท : %s\n   ได้ยิน: %s" % r for r in rows))
print("\nรวมเสียงพูด %.2f วิ" % sum(r[1] for r in rows))
for r in rows:
    print("%2d %5.2f  ย่อ %d  | %s" % (r[0], r[1], r[2], r[4][:48]))
