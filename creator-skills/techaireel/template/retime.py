# -*- coding: utf-8 -*-
"""ยืด/ย่อวิดีโอที่อัดมาให้พอดีเสียงพากย์ทีละช่วง แล้วแปลงเวลาของ event ไปยังไทม์ไลน์ใหม่"""
import io, json, os, subprocess, glob, sys

ROOT = r"__ROOT__"
FPS = 30
WORK = os.path.join(ROOT, "rec/segs")
os.makedirs(WORK, exist_ok=True)

tl = json.load(io.open(os.path.join(ROOT, "script/timeline.json"), encoding="utf-8"))
ev = json.load(io.open(os.path.join(ROOT, "rec/events.json"), encoding="utf-8"))
OFF = tl["slateOffset"]
# ใช้ไฟล์ที่เบลอชื่อบัญชีกับรายการแชทแล้ว ห้ามกลับไปใช้ webm ดิบ
SRC = os.path.join(ROOT, "rec/private.mp4")

# ---------- 1. ตัดและยืดทีละ segment ----------
parts = []
for i, s in enumerate(tl["segments"]):
    out = os.path.join(WORK, "seg_%02d.mp4" % i)
    have = s["vTo"] - s["vFrom"]
    factor = s["outDur"] / have          # >1 คือยืดให้ช้าลง
    vf = "setpts=%.6f*PTS,fps=%d,scale=1440:900:flags=lanczos" % (factor, FPS)
    cmd = ["ffmpeg", "-v", "error", "-y",
           "-ss", "%.3f" % s["vFrom"], "-t", "%.3f" % have, "-i", SRC,
           "-vf", vf, "-an", "-c:v", "libx264", "-crf", "18", "-preset", "veryfast",
           "-pix_fmt", "yuv420p", out]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        print("FAIL seg", i, r.stderr[:300]); sys.exit(1)
    d = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                        "-of", "default=nw=1:nk=1", out], capture_output=True, text=True)
    got = float(d.stdout.strip())
    parts.append(out)
    print("seg %02d  ภาพ %6.2f-%6.2f -> ยาว %5.2f วิ (ต้องการ %5.2f)  x%.2f  บรรทัด %s"
          % (i, s["vFrom"], s["vTo"], got, s["outDur"], factor, s["lines"]))

# ---------- 2. ต่อกัน ----------
lst = os.path.join(WORK, "concat.txt")
io.open(lst, "w", encoding="utf-8").write(
    "".join("file '%s'\n" % p.replace("\\", "/") for p in parts))
merged = os.path.join(ROOT, "rec/screen_retimed.mp4")
r = subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0",
                    "-i", lst, "-c", "copy", merged], capture_output=True, text=True)
if r.returncode != 0:
    print("CONCAT FAIL", r.stderr[:400]); sys.exit(1)
d = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                    "-of", "default=nw=1:nk=1", merged], capture_output=True, text=True)
print("\nรวมภาพหน้าจอ %.2f วินาที (ไทม์ไลน์ต้องการ %.2f)" % (float(d.stdout), tl["screenDur"]))

# ---------- 3. แปลงเวลา event ไปยังไทม์ไลน์ใหม่ ----------
def to_out(v):
    """เวลาในวิดีโอต้นฉบับ -> เวลาในคลิปที่ยืดแล้ว"""
    for s in tl["segments"]:
        if s.get("events", True) and s["vFrom"] <= v <= s["vTo"]:
            have = s["vTo"] - s["vFrom"]
            return s["outStart"] + (v - s["vFrom"]) / have * s["outDur"]
    return None

marks = []
for e in ev["events"]:
    if e["type"] not in ("click", "focus", "type"):
        continue
    v_in = e["t"] - OFF
    v_out = e.get("tAfter", e["t"]) - OFF
    a, b = to_out(v_in), to_out(v_out)
    if a is None:
        continue
    marks.append({
        "type": e["type"], "label": e.get("label", ""),
        "start": round(a, 3), "end": round(b if b else a, 3),
        "x": e["x"], "y": e["y"], "w": e["w"], "h": e["h"],
        "cx": e["cx"], "cy": e["cy"],
    })

# พิกัดที่ selector ตอนอัดจับผิด แก้ไว้ตรงนี้ ไม่งั้นรัน retime ใหม่จะกลับไปผิดเหมือนเดิม
FIX = {
    # text=Inbox triage ไปจับชื่อแชทใน sidebar แทนการ์ดเทมเพลต
    "Inbox triage": dict(x=930.8, y=442.0, w=336.0, h=20.0, cx=1098.8, cy=452.0),
    # ให้กรอบคลุมการ์ดเทมเพลตทั้งกลุ่ม ไม่ใช่แค่ใบแรก
    # ช่วงภาพรวมเลื่อนกล้องเฉย ๆ ไม่วาดกรอบ กรอบใหญ่ขนาดนี้ทำให้มืดทั้งจอ (เจอตอนรีวิว v3)
    "เทมเพลตทั้งหมด": dict(type="cam", x=488.0, y=424.0, w=800.0, h=340.0, cx=888.0, cy=594.0),
    # ขยายให้เห็นหัวข้อหน้า Scheduled tasks ด้วย เดิมซูมแคบจนหัวข้อเหลือแค่ "tasks"
    "ยังไม่มีงาน": dict(type="cam", x=440.0, y=50.0, w=840.0, h=280.0, cx=860.0, cy=190.0),
}
for mk in marks:
    if mk["label"] in FIX:
        mk.update(FIX[mk["label"]])

# mark ที่เพิ่มเอง วางตามเวลาของประโยค ไม่ได้มาจาก event ตอนอัด
#   cam  = เลื่อนกล้องอย่างเดียว ไม่มีกรอบ ไม่มีเสียง
#   chip = ป้ายบอกที่มาของภาพ ตามระบบความซื่อตรงของ prom-design
SCHED_LINE = dict(x=500.0, y=507.0, w=170.0, h=24.0, cx=585.0, cy=519.0)   # "Weekdays at 8:00 AM" บนการ์ด Daily briefing
EXTRA = [
    dict(type="cam",   label="เปิดคลิปที่การ์ด Daily briefing", line=1,  offset=-0.7,
         x=440.0, y=420.0, w=440.0, h=120.0, cx=660.0, cy=480.0),
    dict(type="focus", label="Weekdays at 8:00 AM", line=1, offset=1.2, **SCHED_LINE),
    dict(type="focus", label="ช่อง Permissions", line=26, offset=0.35,
         x=384.0, y=588.4, w=128.0, h=20.0, cx=448.0, cy=598.4),
    dict(type="focus", label="เวลาบนการ์ดตัวอย่าง", line=28, offset=2.2,
         chip="ภาพจากแบบสำเร็จรูป ไม่ใช่งานที่เราสร้าง", **SCHED_LINE),
]
cue_at = {c["id"]: c for c in tl["cues"]}
for e in EXTRA:
    e = dict(e)
    line, off = e.pop("line"), e.pop("offset")
    t = round(max(0.0, cue_at[line]["start"] + off), 3)
    marks.append(dict(start=t, end=t, **e))
marks.sort(key=lambda m: m["start"])

tl["marks"] = marks
io.open(os.path.join(ROOT, "script/timeline.json"), "w", encoding="utf-8").write(
    json.dumps(tl, ensure_ascii=False, indent=2))
print("แปลงเวลา event แล้ว %d จุด" % len(marks))
for m in marks[:8]:
    print("  %6.2f-%6.2f  %-6s %s" % (m["start"], m["end"], m["type"], m["label"]))
