# build_prompts.py <PROJ> — สร้าง prompts.json จาก script.json (สำหรับ chatgpt-batch.mjs)
import json, sys
from pathlib import Path
PROJ = Path(sys.argv[1])
cfg = {}
if (PROJ/"config.json").exists(): cfg = json.load(open(PROJ/"config.json", encoding="utf-8"))
STYLE = cfg.get("img_style",
    " — ภาพสไตล์สารคดี โทนสว่างสะอาด แนวตั้ง 9:16 (portrait) ความละเอียดสูงมาก สมจริง ไม่มีข้อความหรือตัวอักษรใดๆ ในภาพ")
segs = json.load(open(PROJ/"script.json", encoding="utf-8"))
out = [{"id": s["id"], "prompt": s["img"] + STYLE} for s in segs]
json.dump(out, open(PROJ/"prompts.json", "w", encoding="utf-8"), ensure_ascii=False, indent=2)
print("wrote", PROJ/"prompts.json", len(out), "prompts")
