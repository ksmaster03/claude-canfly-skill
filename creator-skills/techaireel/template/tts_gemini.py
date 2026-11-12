# -*- coding: utf-8 -*-
"""พากย์ด้วย Gemini TTS แบบยิงเป็นก้อน แล้วตัดแยกกลับเป็นรายประโยคด้วยช่องเงียบ

ทำไมต้องยิงเป็นก้อน: free tier ได้ราว 10 คำขอต่อวันต่อคีย์ แต่บทมี 35 ประโยค
ยิงก้อนละ 6 ประโยคใช้แค่ 6 คำขอ แล้วหาช่องเงียบที่ยาวที่สุด N-1 ช่องมาเป็นรอยตัด

คีย์อ่านจากไฟล์ในหน่วยความจำเท่านั้น ไม่พิมพ์ค่าออกมา
"""
import base64, io, json, os, subprocess, sys, time, urllib.error, urllib.request, wave
import numpy as np

ROOT = r"__ROOT__"
OUT = os.path.join(ROOT, "audio_gemini")
RAW = os.path.join(OUT, "_chunks")
MODEL = "gemini-2.5-flash-preview-tts"
VOICE = "Charon"
CHUNK = 6
SR = 24000
STYLE = ("อ่านด้วยน้ำเสียงผู้ชายที่เป็นกันเอง เหมือนพี่กำลังสอนน้องใช้โปรแกรมอย่างใจเย็น "
         "ชัดถ้อยชัดคำ จังหวะสบาย ๆ เว้นช่วงหายใจชัดเจนหลังจบแต่ละบรรทัด:\n\n")

os.makedirs(RAW, exist_ok=True)


def load_keys():
    """ดึงคีย์ Google จากไฟล์ คืนเป็นรายการ (ป้าย, ค่า) ไม่แสดงค่า"""
    found = []
    for line in io.open(os.environ.get("GEMINI_KEY_FILE", "api-key.txt"), encoding="utf-8"):
        if ":" in line:
            lab, val = line.split(":", 1)
            if val.strip().startswith("AIza"):
                found.append((lab.strip(), val.strip()))
    return found


def synth(text, path, keys):
    if os.path.exists(path) and os.path.getsize(path) > 4000:
        return
    body = {"contents": [{"parts": [{"text": STYLE + text}]}],
            "generationConfig": {"responseModalities": ["AUDIO"],
                                 "speechConfig": {"voiceConfig": {"prebuiltVoiceConfig": {"voiceName": VOICE}}}}}
    url = "https://generativelanguage.googleapis.com/v1beta/models/%s:generateContent?key=" % MODEL
    for attempt in range(8):
        lab, val = keys[attempt % len(keys)]
        try:
            req = urllib.request.Request(url + val, data=json.dumps(body).encode(),
                                         headers={"content-type": "application/json"})
            with urllib.request.urlopen(req, timeout=240) as r:
                j = json.load(r)
            parts = j["candidates"][0].get("content", {}).get("parts", [])
            if not parts or "inlineData" not in parts[0]:
                print("   ไม่มีเสียงกลับมา ลองใหม่"); time.sleep(6); continue
            pcm = base64.b64decode(parts[0]["inlineData"]["data"])
            with wave.open(path, "wb") as w:     # Gemini คืน PCM ดิบ ต้องห่อ header เอง
                w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes(pcm)
            return
        except urllib.error.HTTPError as e:
            wait = 60 if e.code == 429 else 8
            print("   %s HTTP %d รอ %d วิ" % (lab, e.code, wait)); time.sleep(wait)
        except Exception as e:
            print("   %s" % type(e).__name__); time.sleep(8)
    sys.exit("พากย์ไม่สำเร็จ: " + path)


def read_wav(path):
    with wave.open(path, "rb") as w:
        return np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float32) / 32768


def write_wav(path, x):
    y = np.clip(x * 32768, -32768, 32767).astype(np.int16)
    with wave.open(path, "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes(y.tobytes())


def split_by_silence(x, n):
    """หาช่องเงียบที่ยาวที่สุด n-1 ช่อง แล้วตัดตรงกลางช่องนั้น"""
    hop = int(SR * 0.01)
    env = np.array([np.sqrt(np.mean(x[i:i + hop] ** 2)) + 1e-9 for i in range(0, len(x) - hop, hop)])
    db = 20 * np.log10(env)
    quiet = db < (np.percentile(db, 60) - 22)
    runs, start = [], None
    for i, q in enumerate(quiet):
        if q and start is None:
            start = i
        elif not q and start is not None:
            runs.append((start, i)); start = None
    # ไม่เอาช่องเงียบหัวและท้ายไฟล์
    speech = np.where(~quiet)[0]
    first, last = speech[0], speech[-1]
    runs = [r for r in runs if r[0] > first and r[1] < last]
    runs.sort(key=lambda r: r[1] - r[0], reverse=True)
    cuts = sorted(runs[:n - 1])
    if len(cuts) < n - 1:
        return None, cuts
    bounds, prev = [], first
    for a, b in cuts:
        bounds.append((prev, a)); prev = b
    bounds.append((prev, last + 1))
    pad = int(0.04 * SR)
    pieces = [x[max(0, s * hop - pad): min(len(x), e * hop + pad)] for s, e in bounds]
    gaps = [(b - a) * 0.01 for a, b in cuts]
    return pieces, gaps


data = json.load(io.open(os.path.join(ROOT, "script/script.json"), encoding="utf-8"))
lines = data["lines"]
keys = load_keys()
print("คีย์ที่ใช้ได้ %d ตัว" % len(keys))

for c in range(0, len(lines), CHUNK):
    group = lines[c:c + CHUNK]
    raw = os.path.join(RAW, "chunk_%02d.wav" % (c // CHUNK))
    text = "\n\n".join(ln["vo"] for ln in group)
    print("ก้อน %d  ประโยค %d-%d" % (c // CHUNK + 1, group[0]["id"], group[-1]["id"]))
    synth(text, raw, keys)
    x = read_wav(raw)
    pieces, gaps = split_by_silence(x, len(group))
    if pieces is None:
        sys.exit("   ตัดแยกไม่ครบ เจอช่องเงียบ %d ช่อง ต้องการ %d" % (len(gaps), len(group) - 1))
    print("   ยาว %.2f วิ  ช่องเงียบที่ใช้ตัด %s" % (len(x) / SR, ", ".join("%.2f" % g for g in gaps)))
    for ln, p in zip(group, pieces):
        f = os.path.join(OUT, "line_%02d.wav" % ln["id"])
        write_wav(f, p)
        ln["audio"] = os.path.basename(f)
        ln["dur"] = round(len(p) / SR, 3)
    time.sleep(4)

total = sum(ln["dur"] for ln in lines)
data["voice"] = "gemini:" + VOICE
io.open(os.path.join(ROOT, "script/script.json"), "w", encoding="utf-8").write(
    json.dumps(data, ensure_ascii=False, indent=2))
print("\nรวมเสียงพูด %.2f วิ  เฉลี่ยประโยคละ %.2f วิ" % (total, total / len(lines)))
for ln in lines:
    print("%2d %5.2f  %s" % (ln["id"], ln["dur"], ln["text"][:40]))
