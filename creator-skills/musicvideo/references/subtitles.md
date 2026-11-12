# Subtitles: getting the lyric on screen at the right moment

Use **forced alignment**. Everything else on this page is the record of what
was tried first and why it was not enough.

| method | lines anchored |
| --- | --- |
| the platform's own `timestampedLyrics` | drifted against the vocal; the listener caught it, no measurement did |
| ASR over the full mix, then fuzzy matching | 49% |
| ASR over a vocal stem, then fuzzy matching | 58% |
| **forced alignment against a lyric sheet** | **100%, on two songs in two languages** |

The reason the last one wins is not that it is a better model. It is that it
solves a smaller problem. ASR is asked *what is being sung*, which nobody needs
to know -- the lyric sheet already says so. Forced alignment is asked only
*where each known word sits in the waveform*. Every attempt that went through
ASR was paying for an answer it already had, and inheriting that answer's
errors.

## Get the lyric sheet from the person, first

Ask. Do not scrape, and do not transcribe. Both songs here had a sheet the
author could paste in seconds, and on the first one two rounds of work were
spent reconstructing line breaks from a word stream before anyone thought to
ask for it.

Sources that look authoritative and are not:

- **The mp3's own metadata.** Suno writes the lyric into a `lyrics-eng` tag.
  On the second song that tag was missing two whole sections that the author's
  own copy had.
- **The platform's web page.** It carries the lyric and sometimes word-level
  timing, but the timing drifts and the markup is a React Server Component
  payload that needs careful decoding (see the extraction note at the bottom).

## The pipeline

```bash
demucs --two-stems=vocals -n htdemucs -d cpu -o out/stems audio/source.wav
ffmpeg -y -i out/stems/htdemucs/source/vocals.wav \
  -af 'highpass=f=70,loudnorm=I=-16:TP=-1.5:LRA=11' -ar 16000 -ac 1 out/vocals_asr.wav
python tools/forced.py out/vocals_asr.wav src/lyrics_source.txt src/subtitles.json <lang>
```

Separate the vocal first. It is not optional politeness to the model: on a mix
mastered to -9 LUFS the alignment quality drops sharply, and an ASR pass over
the same audio emitted one filler word 198 times out of 417.

### Non-Latin scripts need romanising

MMS_FA's dictionary is **29 symbols**: a-z and a little punctuation. Thai does
not fail gracefully, it raises `KeyError` on the first character. Romanise with
`uroman` before tokenising -- this is the documented path for the model, not a
workaround:

```python
import uroman
_URO = uroman.Uroman()

def norm_word(w):
    r = _URO.romanize_string(w, lcode='tha')   # English passes through unchanged
    return ''.join(c for c in r.lower() if 'a' <= c <= 'z')
```

On the Thai song, 318 words romanised with only 8 coming back empty (all of
them punctuation-only tokens).

### Chunking

A five-minute forward pass does not fit in memory on this machine. Cut chunks
**inside silences** in the vocal stem, and split the lyric across them in
proportion to how much *voiced* audio each chunk holds -- not evenly by time.
An instrumental chunk given its even share of words drags every later word out
of place.

## Verify with something the aligner did not use

The aligner reports 100% because it placed every line somewhere. That is not
evidence. Measure the vocal stem's energy and ask what fraction of each line's
window actually contains singing:

| | English song | Thai song |
| --- | --- | --- |
| lines aligned | 158/158 | 111/111 |
| median voiced fraction of each line's window | 86% | 76% |
| lines landing on silence | 12 | 1 |

Below roughly 70% median, something is wrong regardless of what the percentage
says. Reject and investigate rather than render.

## Line structure comes from the sheet, never from a heuristic

Deriving lines from a word stream failed in both directions on the same song:
splitting on every `.` `!` `?` gave a median line of 12 characters with 57
lines on screen for under a second, and the merge pass that fixed that then
glued short chant lines the writer meant to stand alone. A lyric sheet already
knows where the lines are.

**Section markers wear more than one dress.** Suno writes `[Chorus]` plain;
other sources wrap it `**[Chorus]**`. Matching only the starred form let ten
headers through as if they were lyrics -- and it was caught only because the
line count came back 10 higher than the sheet has:

```python
bare = line.strip().strip('*').strip()
if bare.startswith('[') and bare.endswith(']'):
    continue     # structure, never displayed
```

Always compare the aligner's line count against the sheet's before trusting it.

## On screen

- **A scrim, not just a text shadow.** Backdrops cut every few bars and some
  are bright in exactly the band the text occupies; a shadow alone loses the
  line for a whole scene.
- **Fade, do not cut.** Lines can land a tenth of a second apart.
- **Cap how long a line holds** (about 5s). Aligners pad word durations to meet
  the next word, so a line before an instrumental otherwise sits through the
  whole break.
- **Thai** needs `line-height` around 1.34 for the marks above and below the
  line, and `letter-spacing: 0` -- tracking visibly detaches a mark from the
  glyph it belongs to.
- Putting lyrics along the bottom means the credit lockup has to move.

## Fonts

The template's inherited stack was Arial Black, which has **no Thai glyphs**.
A Thai song rendered with it is tofu boxes end to end, and it reads as a
font-weight problem rather than a missing script. Run `tools/embed-fonts.py` to
inline a Thai-capable face (Sarabun) as base64 and mount `<Fonts/>` in every
composition. Embedding also avoids a webfont fetch inside each render chunk,
which is one less thing that can hold a `delayRender()` open.

## If you must read the platform's own timing

It lives in a React Server Component payload, not the HTML, and the song record
holds only a reference such as `"timestampedLyrics":"$c0"`:

```python
chunks = re.findall(r'self\.__next_f\.push\(\[1,"(.*?)"\]\)', html, re.S)
blob = ''.join(json.loads('"' + c + '"') for c in chunks)   # NOT unicode_escape
i = blob.find('c0:T')
start = i + re.match(r'c0:T([0-9a-f]+),', blob[i:]).end()
data, _ = json.JSONDecoder().raw_decode(blob[start:])        # NOT a byte-length slice
```

`unicode_escape` corrupts multi-byte characters, and the hex prefix counts
**bytes** while the string is indexed in **characters**. Useful as a
cross-check. Not good enough to ship on its own -- that is what started all of
this.
