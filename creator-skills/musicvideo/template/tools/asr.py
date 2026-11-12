"""Transcribe with word-level timestamps, as an independent clock for the lyrics.

    python tools/asr.py [audio] [out.json] [model]

The platform's own alignment was tried first and drifts against the vocal in
places. This does not care what the words are -- the real lyrics are known and
supplied separately -- it only needs honest onset times to align them to, so a
small model is enough and a wrong word here or there costs nothing.
"""
import json
import sys

from faster_whisper import WhisperModel

AUDIO = sys.argv[1] if len(sys.argv) > 1 else 'audio/master.wav'
OUT = sys.argv[2] if len(sys.argv) > 2 else 'src/asr_words.json'
NAME = sys.argv[3] if len(sys.argv) > 3 else 'small'

model = WhisperModel(NAME, device='cpu', compute_type='int8')
segments, info = model.transcribe(
    AUDIO,
    language='en',
    word_timestamps=True,
    vad_filter=False,          # a wall-of-sound mix trips the VAD into cutting vocal
    beam_size=5,
    condition_on_previous_text=False,   # stops a chant looping the decoder
)

words = []
for seg in segments:
    for w in (seg.words or []):
        words.append({'w': w.word.strip(), 's': round(w.start, 3), 'e': round(w.end, 3)})

json.dump(words, open(OUT, 'w', encoding='utf-8'), ensure_ascii=False)
print('model      :', NAME)
print('words      :', len(words))
if words:
    print('span       : %.2fs .. %.2fs' % (words[0]['s'], words[-1]['e']))
    gaps = [words[i + 1]['s'] - words[i]['e'] for i in range(len(words) - 1)]
    big = [g for g in gaps if g > 2.0]
    print('gaps > 2s  : %d  (real instrumental breaks show up here)' % len(big))
    print('max gap    : %.2fs' % max(gaps))
