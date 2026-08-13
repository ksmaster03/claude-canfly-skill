# Tinglish respeller — แทนคำอังกฤษด้วยคำอ่านไทย ก่อนป้อน TTS ใดๆ
# ใช้กับ "เสียง" เท่านั้น (ไม่ใช่ซับ/ข้อความบนจอ)
# CLI:  python respell.py "ใช้ model ของ Anthropic"   ->  "ใช้ โมเดล ของ แอนโทรปิก"
import json, re, sys
from pathlib import Path

DICT_PATH = Path(__file__).resolve().parent / "tinglish_dict.json"

def load_dict():
    d = json.load(open(DICT_PATH, encoding="utf-8"))
    return {k: v for k, v in d.items() if not k.startswith("_")}

def make_respeller(extra=None):
    d = load_dict()
    if extra:
        d.update(extra)
    # เรียงคีย์ยาว->สั้น เพื่อให้วลี ("software engineering") ชนะคำเดี่ยว ("software")
    keys = sorted(d.keys(), key=len, reverse=True)
    pats = [(re.compile(rf"(?<![A-Za-z0-9]){re.escape(k)}(?![A-Za-z0-9])", re.IGNORECASE), d[k]) for k in keys]
    def respell(text):
        for pat, repl in pats:
            text = pat.sub(repl, text)
        return text
    return respell

if __name__ == "__main__":
    r = make_respeller()
    if len(sys.argv) > 1:
        print(r(" ".join(sys.argv[1:])))
    else:
        import fileinput
        for line in fileinput.input():
            print(r(line.rstrip("\n")))
