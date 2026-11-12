"""Turn Suno's word-level alignment into a section + line timeline for the MV.

    python timeline.py <aligned.json> [--bpm 169.4] [--phase 0.30]

Suno aligns the section tags themselves ("[Chorus]\n..."), so the tag's start_s is the
real downbeat-ish moment the section begins. Everything the MV needs — which scene runs
when, and which lyric line sits under the figures — comes from this file.
"""
import json
import re
import sys

BPM = 169.4
PHASE = 0.30


def load_words(path):
    d = json.load(open(path, encoding="utf-8"))
    return d["data"][0]


def sections(words):
    """(tag, start_s) for every [Section] marker, in order."""
    out = []
    for w in words:
        m = re.search(r"\[([^\]]+)\]", w["word"])
        if m:
            out.append((m.group(1), w["start_s"]))
    return out


def lines(words):
    """Rebuild lyric lines with their start/end, dropping the section tags."""
    out, cur, start = [], "", None
    for w in words:
        txt = w["word"]
        clean = re.sub(r"\[[^\]]*\]", "", txt)
        if start is None and clean.strip():
            start = w["start_s"]
        cur += clean
        while "\n" in cur:
            head, cur = cur.split("\n", 1)
            if head.strip():
                out.append({"text": head.strip(), "start": start, "end": w["end_s"]})
            start = None
        if start is None and cur.strip():
            start = w["start_s"]
    if cur.strip():
        out.append({"text": cur.strip(), "start": start, "end": words[-1]["end_s"]})
    return out


def main():
    path = sys.argv[1]
    bpm = float(sys.argv[sys.argv.index("--bpm") + 1]) if "--bpm" in sys.argv else BPM
    phase = float(sys.argv[sys.argv.index("--phase") + 1]) if "--phase" in sys.argv else PHASE
    bar = 4 * 60.0 / bpm

    words = load_words(path)
    secs = sections(words)
    ls = lines(words)

    print(f"bar = {bar:.4f}s   phase = {phase}s   words = {len(words)}   lines = {len(ls)}\n")
    print("SECTIONS  (tag, start, bar#, length)")
    for i, (tag, t) in enumerate(secs):
        end = secs[i + 1][1] if i + 1 < len(secs) else ls[-1]["end"]
        print(f"  {tag:<12} {t:8.3f}s  bar {(t - phase) / bar:7.2f}  len {end - t:6.2f}s  ({(end - t) / bar:5.2f} bars)")

    out = {
        "bpm": bpm, "bar": bar, "phase": phase,
        "sections": [{"tag": t, "start": s} for t, s in secs],
        "lines": ls,
    }
    with open("timeline.json", "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=1)
    print("\n-> timeline.json")


if __name__ == "__main__":
    main()
