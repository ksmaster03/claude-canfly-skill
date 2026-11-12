# promotioncut

**English** · [ภาษาไทย](README.th.md)

![A framed promo clip beside a film strip whose cuts line up with the beat grid of a waveform](docs/promotioncut-hero.jpg)

A Claude Code skill that builds a square (1080x1080) promo clip for an event or a product. Fast-cut footage plays in a window that covers 52.5% of the frame, a static branded frame around it carries the headline, date, venue and call to action, and the soundtrack is instrumental music only.

Cut points are written in beats, not seconds. The assembler turns beats into frames, so every cut lands on the music grid by construction, and a checker then measures the finished file to prove it.

## What it does

- Measures the music: tempo, first downbeat, and a bar table that shows where the drops and breaks are.
- Renders the frame and the title cards from HTML templates with headless Chromium, so Thai text is shaped correctly.
- Assembles the clip from one `edit.json`: cuts the shots, composites the frame, grades the picture, lays the music, and normalises loudness in two passes to -14 LUFS.
- Checks its own output: frame count, loudness measured on the file, and whether each planned cut sits on its planned frame.
- Tests any clip, yours or someone else's, for beat sync, and compares the score with what random cutting would get.

## Requirements

- ffmpeg 8.1.1 and ffprobe on `PATH`
- Python 3.12 with `numpy`, `scipy` and `playwright` (Chromium installed)
- The Prompt font (the templates fall back to Leelawadee UI)
- No demucs or librosa needed

These versions were confirmed on the development machine on 8 October 2026.

This folder is a Claude Code skill. Kept at `~/.claude/skills/promotioncut`, it is triggered with `/promotioncut`. `SKILL.md` (written in Thai) is the full procedure, including the bar-by-bar plan and the target numbers.

## Quick start

Keep everything for one clip in a single job folder with ASCII file names. Put all on-screen text in UTF-8 JSON files, never on the command line: Git Bash turns non-ASCII arguments into `?????` and still exits 0.

```bash
SK="<path to this folder>"
```

1. Measure the grid of the music.

```bash
python "$SK/scripts/pc_beat.py" grid "<job>/music.wav" --fps 25 --out "<job>/grid.json"
```

2. Plan the clip in bars. The starting plan in `SKILL.md` is 21 bars (84 beats): opening card, build, logo flash run, title card, drop A, break, drop B, end card.

3. Pick shots from contact sheets, and note the start second of each one.

```bash
ffmpeg -hide_banner -v error -i "<footage.mp4>" -vf "fps=2,scale=270:-1,tile=6x4" -q:v 3 "<job>/sheets/NAME_%02d.jpg" -y
```

4. Render the frame and the cards. Look at every PNG before using it.

```bash
python "$SK/scripts/pc_card.py" "$SK/assets/frame.html" "<job>/frame.png" --data "<job>/frame.json" --size 1080x1080 --transparent
python "$SK/scripts/pc_card.py" "$SK/assets/card.html" "<job>/cards/title.png" --data "<job>/title.json" --size 1080x567
```

5. Copy `assets/edit.example.json` into the job folder and fill it in. Paths are relative to `edit.json`.

6. Build.

```bash
python "$SK/scripts/pc_build.py" "<job>/edit.json" -o "<job>/out.mp4"
```

7. Check the result.

```bash
python "$SK/scripts/pc_beat.py" check "<job>/out.mp4"
```

## Usage

| File | Job |
|---|---|
| `scripts/pc_beat.py` | `grid`: tempo, first downbeat and bar table. `check`: are the cuts on the beat, compared with random cutting |
| `scripts/pc_card.py` | Renders an HTML template to PNG with Chromium |
| `scripts/pc_build.py` | Assembles the clip from `edit.json`, composites the frame, grades, lays the music, sets loudness, then checks itself |
| `assets/frame.html` | 1080x1080 frame with a transparent 1080x567 video window at y=264 |
| `assets/card.html` | Opening card, title card and end card, the size of the video window |
| `assets/edit.example.json` | Skeleton `edit.json` for the 21-bar plan. It is incomplete on purpose: read its `_note` |
| `references/digitech-teardown.md` | The measured teardown of the reference clip (in Thai) |

Template keys (JSON passed with `--data`):

| Template | Keys |
|---|---|
| `frame.html` | `headline1`, `headline2`, `date`, `venue`, `cta`, `logos` (list of paths), `vars` |
| `card.html` | `kicker`, `title`, `sub`, `logos`, `vars` |

In text, `*word*` marks the accent colour, `\n` breaks the line, and an empty string hides that block. `vars` overrides CSS values such as `bg1`, `bg2` and `accent`.

Main `edit.json` fields:

| Field | Meaning |
|---|---|
| `grid` | `bpm` and `first_downbeat` from step 1 |
| `music_offset` | Seconds into the music file where the clip starts |
| `end` | Beat where the clip ends |
| `at` | Start of a shot, in beats from the first downbeat of the music. Decimals are allowed (0.5 is half a beat). The first shot always starts at frame 0 |
| `run` + `until` | A set of stills spread evenly up to `until`, used for the logo flash run |
| `fit` | `"cover"` makes a still fill the window. By default it is fitted inside the window on `card_bg` |
| `grade` | `"navy"` is the look of the reference clip, `"none"` leaves the picture ungraded |
| `fx` | Optional effect on the first frames of the incoming shot |

| `fx` | Effect |
|---|---|
| `flash` | White bloom that fades in 3 frames |
| `punch` | Arrives zoomed in by 30% and settles in 6 frames |
| `rgb` | Colour channels split sideways for 5 frames |
| `blur` | 4 blurred frames, then sharp |

Verdicts printed by `pc_beat.py check`:

| Verdict | Meaning | What to do |
|---|---|---|
| `ON GRID` | The cuts follow the music | Done |
| `OFF BY A CONSTANT ... ms` | The cuts are regular but all shifted by the same amount | Fix `first_downbeat` or `music_offset`, not the shot list |
| `PARTLY ON GRID` | Some cuts follow the music, many do not | Look for shots whose `at` is not a beat |
| `NOT SYNCED` | Same as random cutting | The music and the grid do not belong together. Go back to step 1 |

The `PACE vs MUSIC` table at the end of the check shows cuts per second against the level of the music, two bars at a time.

## How it works

- **Music first, cuts counted in beats.** `edit.json` holds beat numbers and the assembler converts them to frames. At a tempo with a whole number of frames per beat (100 BPM at 25 fps, or 120 BPM at 30 fps, both 15 frames per beat) every beat is frame-exact.
- **Cut rate follows the energy of the music.** Loud sections cut fast, breaks are left to breathe.
- **Trust the checker, not the ear and not the exit code.** While this skill was being built, ffmpeg silently dropped 112 frames and still exited 0. Only measuring the output caught it.
- **Every segment is converted to BT.709 with identical colour tags before concatenation.** One segment tagged differently from the rest was the cause of those dropped frames.
- **The composite runs in packed `rgb24`.** On ffmpeg 8.1.1, converting yuv420p to planar `gbrp` left the last 8 columns of a 1080-wide picture black.
- **The video window is 567 px tall, an odd number that yuv420p cannot hold.** Segments are rendered 568 px tall and cropped to 567 in RGB.
- **The downbeat is found with linear RMS per beat.** Measured in dB, the riser before a drop wins over the drop itself.
- **Cuts inside a flash run (shots shorter than 5 frames) are left out of the sync test,** because they are off the grid on purpose.

## Results

Measured on 8 October 2026. Tolerance is one frame.

| Clip | Cuts on a beat | Verdict |
|---|---|---|
| Test clip built by this skill (48 s, 87 shots) | 97.2% (random cutting would score 14.0%, z = +20.2) | `ON GRID` |
| The same clip with the grid deliberately shifted by 143 ms | flagged as off by a constant +141 ms | `OFF BY A CONSTANT` |
| The reference clip the skill was derived from | 10.2% | `NOT SYNCED` |

Loudness of the test build, measured on the file: -13.9 LUFS, true peak -1.5 dBTP (target: -14 LUFS, true peak no higher than -1.5 dBTP).

To reproduce on your own clip:

```bash
python "$SK/scripts/pc_beat.py" check "<job>/out.mp4"
```

The test clip was made from synthetic footage and is not included in this repo.

## Known limitations

- Tested with synthetic footage only. On the first job with real footage, inspect a contact sheet of the result closely.
- Only 1:1 at 25 fps has been tested. Other sizes and frame rates can be set through `size`, `window`, `fps` and the frame `vars`, but they are untested.
- The heavy transitions of the reference clip are not implemented: glitch bands, light leaks, split screen, spin with zoom blur.
- No subtitles, no voice-over, no SFX.
- Bring your own licensed music. Do not take the music from someone else's clip.
- A cut between two shots that look alike is not detected, so the "planned cuts found" count can be slightly short with nothing wrong.

## About the reference clip

The recipe comes from a measured teardown of a publicly posted third-party event ad, analysed for study. The numbers are in `references/digitech-teardown.md`. The skill keeps the structure and the proportions of that clip and fixes its largest weakness: the reference was not cut to its music.

This project is not affiliated with that event or its organisers, and it contains none of their footage, music or logos.
