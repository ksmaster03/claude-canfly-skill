"""Force-align the known lyrics to the vocal, and write the subtitle file.

    python tools/forced.py [vocal.wav] [lyrics.txt] [out.json]

This is the right shape of tool for the job. The words are already known -- the
lyric sheet is authoritative -- so nothing has to guess what is being sung, only
where each word sits in the waveform. Two earlier attempts did guess:

  * The platform's own alignment drifted against the vocal.
  * ASR plus fuzzy matching anchored 49% of lines against the full mix (a
    decoder loop emitted one filler word 198 times out of 417, which read as
    102% recall until the tokens were counted) and 58% against a vocal stem.

Audio is processed in chunks because a 5-minute forward pass does not fit
comfortably in memory on this machine. Chunk boundaries are placed inside
silences found in the vocal stem, and the lyric is split across chunks in
proportion to how much voiced audio each one holds, so a boundary never lands
mid-word.
"""
import json
import sys

import uroman
import torch
import torchaudio
from torchaudio.pipelines import MMS_FA as bundle

VOC = sys.argv[1] if len(sys.argv) > 1 else 'out/vocals_asr.wav'
LYR = sys.argv[2] if len(sys.argv) > 2 else 'src/lyrics_source.txt'
OUT = sys.argv[3] if len(sys.argv) > 3 else 'src/subtitles.json'

MIN_HOLD, MAX_HOLD, LEAD = 0.55, 5.0, 0.08


LANG = sys.argv[4] if len(sys.argv) > 4 else 'tha'

# MMS_FA's dictionary is 29 Latin symbols. Thai raises KeyError on its first
# character, so any non-Latin script has to be romanised first -- this is the
# path the model documents, not a workaround. English passes through unchanged.
_URO = uroman.Uroman()


def norm_word(w):
    r = _URO.romanize_string(w, lcode=LANG)
    return ''.join(c for c in r.lower() if 'a' <= c <= 'z')


raw = [l.strip() for l in open(LYR, encoding='utf-8').read().split(chr(10))]
lines = []
for l in raw:
    # Section markers come in more than one dress: Suno writes [Chorus] plain,
    # other sources wrap it as **[Chorus]**. Matching only the starred form let
    # ten headers through as if they were lyrics -- caught because the line
    # count came back 10 higher than the sheet actually has.
    bare = l.strip().strip('*').strip()
    if not l or (bare.startswith('[') and bare.endswith(']')):
        continue
    toks = [norm_word(w) for w in l.split()]
    toks = [t for t in toks if t]
    if toks:
        lines.append({'text': l, 'tok': toks})

words, owner = [], []
for i, ln in enumerate(lines):
    for t in ln['tok']:
        words.append(t)
        owner.append(i)
print('lines %d, words %d' % (len(lines), len(words)))

# Read the WAV directly rather than through torchaudio.load: 2.11 routes that
# through torchcodec, which is a separate install, and the file here is already
# the 16 kHz mono PCM the model wants.
import wave
import numpy as np

with wave.open(VOC, 'rb') as fh:
    sr = fh.getframerate()
    ch = fh.getnchannels()
    pcm = np.frombuffer(fh.readframes(fh.getnframes()), dtype=np.int16)
pcm = pcm.reshape(-1, ch).mean(1).astype(np.float32) / 32768.0
wav = torch.from_numpy(pcm).unsqueeze(0)
if sr != bundle.sample_rate:
    raise SystemExit('expected %d Hz, got %d -- resample with ffmpeg first'
                     % (bundle.sample_rate, sr))
total = wav.size(1)
print('audio %.1fs at %d Hz' % (total / sr, sr))

model = bundle.get_model()
tokenizer = bundle.get_tokenizer()
aligner = bundle.get_aligner()

# where the vocal actually sounds, at 20 ms resolution
FR = int(sr * 0.02)
frames = wav[0, :total // FR * FR].reshape(-1, FR)
energy = frames.pow(2).mean(1).sqrt()
thr = energy.max() * 0.02
voiced = (energy > thr)

CHUNK = int(45 * sr)
bounds = [0]
while bounds[-1] + CHUNK < total:
    target = bounds[-1] + CHUNK
    lo, hi = max(0, target - int(4 * sr)) // FR, min(total, target + int(4 * sr)) // FR
    win = energy[lo:hi]
    cut = (lo + int(torch.argmin(win))) * FR if len(win) else target
    bounds.append(int(cut))
bounds.append(total)
print('chunks %d' % (len(bounds) - 1))

# share the words out by voiced content, so a busy chunk gets more of them
share = []
for a, b in zip(bounds, bounds[1:]):
    share.append(float(voiced[a // FR:b // FR].sum()))
tot = sum(share) or 1.0
cuts, acc = [0], 0.0
for s in share[:-1]:
    acc += s
    cuts.append(min(len(words), max(cuts[-1], round(acc / tot * len(words)))))
cuts.append(len(words))

spans = {}
for k, (a, b) in enumerate(zip(bounds, bounds[1:])):
    w0, w1 = cuts[k], cuts[k + 1]
    if w1 <= w0:
        continue
    seg = wav[:, a:b]
    with torch.inference_mode():
        emission, _ = model(seg)
        try:
            ts = aligner(emission[0], tokenizer(words[w0:w1]))
        except Exception as exc:
            print('  chunk %d skipped: %s' % (k, exc))
            continue
    ratio = seg.size(1) / emission.size(1)
    for n, sp in enumerate(ts):
        s = (a + sp[0].start * ratio) / sr
        e = (a + sp[-1].end * ratio) / sr
        o = owner[w0 + n]
        spans[o] = (min(spans[o][0], s), max(spans[o][1], e)) if o in spans else (s, e)
    print('  chunk %d/%d  %.1f-%.1fs  words %d-%d' % (k + 1, len(bounds) - 1, a / sr, b / sr, w0, w1))

out, last = [], 0.0
for i, ln in enumerate(lines):
    if i in spans:
        s, e = spans[i]
    else:
        nxt = next((spans[k][0] for k in range(i + 1, len(lines)) if k in spans), last + 1.2)
        s = max(last + 0.05, min(last + 0.6, nxt - 0.3))
        e = s + MIN_HOLD
    s = max(s - LEAD, last + 0.02)
    e = min(max(e, s + MIN_HOLD), s + MAX_HOLD)
    out.append({'text': ln['text'], 'start': round(s, 3), 'end': round(e, 3)})
    last = e
for a, b in zip(out, out[1:]):
    if a['end'] > b['start'] - 0.02:
        a['end'] = round(max(a['start'] + 0.25, b['start'] - 0.05), 3)

json.dump(out, open(OUT, 'w', encoding='utf-8'), ensure_ascii=False)
print('aligned lines : %d/%d (%.0f%%)' % (len(spans), len(lines), len(spans) / len(lines) * 100))
print('overlaps      : %d' % sum(1 for a, b in zip(out, out[1:]) if a['end'] > b['start'] + 1e-6))
print('span          : %.2fs .. %.2fs' % (out[0]['start'], out[-1]['end']))
