"""Turn word-level timings into subtitle lines the video can display.

    python tools/subtitles.py [src/lyrics_timed.json] [src/subtitles.json]

Input is one object per word with startS/endS. Three things have to happen
before that can go on screen:

  * Section markers such as [Chorus] are split ACROSS words -- the source emits
    the opening bracket on one word and the closing bracket on a later one, so
    no single word ever holds a matching pair. Scanning per word matches
    nothing at all and puts every section header on screen as a lyric. They are
    located in the joined text instead.
  * Writers line breaks ride along inside the word text and are better break
    points than any width rule. Width only splits what is still too long.
  * The source stretches every word until the next one starts -- the largest
    gap between consecutive words in the reference track was 0.16s even across
    instrumental passages, while single words ran as long as 10.4s against a
    median of 0.30s. Without a cap, a line sits through the whole break.

Deliberately no regex and no escape sequences in this file: both were rewritten
in transit twice while generating it, each time producing something that would
not parse.
"""
import json
import sys

SRC = sys.argv[1] if len(sys.argv) > 1 else "src/lyrics_timed.json"
DST = sys.argv[2] if len(sys.argv) > 2 else "src/subtitles.json"
MAX_CHARS = 42          # comfortable for a 1920-wide frame at the size used
MIN_HOLD = 0.9          # a line that flashes for a third of a second is noise
MAX_HOLD = 5.0          # nothing lingers longer, whatever the timings claim
GAP_NEW_LINE = 1.4      # a pause this long ends the line even mid-sentence
NEWLINE = chr(10)

words = json.load(open(SRC, encoding="utf-8"))

# --- locate section markers in the joined text, then flag the words they touch
joined, span = "", []
for w in words:
    span.append((len(joined), len(joined) + len(w["word"])))
    joined += w["word"]

marker = [False] * len(words)
n_section = 0
i = 0
while True:
    a = joined.find("[", i)
    if a < 0:
        break
    b = joined.find("]", a)
    if b < 0:
        break
    n_section += 1
    for k, (s0, s1) in enumerate(span):
        if s0 < b + 1 and s1 > a:
            marker[k] = True
    i = b + 1

lines = []
cur = []


def flush():
    if not cur:
        return
    text = " ".join(" ".join(x["t"] for x in cur).split())
    if text:
        lines.append({"text": text,
                      "start": round(cur[0]["s"], 3),
                      "end": round(cur[-1]["e"], 3)})
    del cur[:]


prev_end = None
for idx, w in enumerate(words):
    if marker[idx]:
        flush()                       # a header still ends the line before it
        prev_end = w["endS"]
        continue
    raw = w["word"]
    # NOT sentence punctuation. This track exclaims constantly, and
    # breaking on every "!" produced a median line of 12 characters with
    # 57 lines on screen for under a second -- unreadable strobing.
    # The writers own line breaks are the only reliable break.
    breaks_after = raw.count(NEWLINE) >= 2
    clean = " ".join(raw.replace("*", "").split())
    if not clean:
        prev_end = w["endS"]
        continue
    if prev_end is not None and w["startS"] - prev_end > GAP_NEW_LINE:
        flush()
    if cur and len(" ".join(x["t"] for x in cur)) + 1 + len(clean) > MAX_CHARS:
        flush()
    cur.append({"t": clean, "s": w["startS"], "e": w["endS"]})
    prev_end = w["endS"]
    if breaks_after:
        flush()
flush()


# Merge neighbours that still fit on one line and follow each other closely.
# Short fragments are a reading problem, not a timing one: the eye needs the
# line to sit still long enough to be read, and two half-lines a beat apart
# read as one thought anyway.
MERGE_GAP = 0.6
merged = []
for line in lines:
    if merged:
        prev = merged[-1]
        joined_len = len(prev["text"]) + 1 + len(line["text"])
        if joined_len <= MAX_CHARS and line["start"] - prev["end"] < MERGE_GAP:
            prev["text"] = prev["text"] + " " + line["text"]
            prev["end"] = line["end"]
            continue
    merged.append(line)
lines = merged

for n, line in enumerate(lines):
    if line["end"] - line["start"] < MIN_HOLD:
        nxt = lines[n + 1]["start"] if n + 1 < len(lines) else line["start"] + MIN_HOLD
        line["end"] = min(line["start"] + MIN_HOLD, max(nxt - 0.05, line["end"]))
    line["end"] = round(min(line["end"], line["start"] + MAX_HOLD), 3)

json.dump(lines, open(DST, "w", encoding="utf-8"), ensure_ascii=False)

leaked = sum(1 for x in lines if "[" in x["text"] or "]" in x["text"] or "*" in x["text"])
overlap = sum(1 for a, b in zip(lines, lines[1:]) if a["end"] > b["start"] + 1e-6)
held = sum(x["end"] - x["start"] for x in lines)
print("words in      : " + str(len(words)))
print("section marks : " + str(n_section) + " (dropped from display, kept as breaks)")
print("lines out     : " + str(len(lines)))
print("marker leaks  : " + str(leaked) + "  (must be 0)")
print("longest line  : " + str(max(len(x["text"]) for x in lines)) + " chars, cap " + str(MAX_CHARS))
print("overlaps      : " + str(overlap) + "  (must be 0)")
print("on screen     : " + str(round(held / lines[-1]["end"] * 100)) + "% of the sung span")
