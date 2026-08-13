---
name: vdocut
description: ตัดต่อวิดีโอขั้นเทพด้วยการสนทนา (god-tier conversational video editing). Transcribe → strategy → confirm → cut → grade → overlays → Thai subtitles → loudnorm → render. Pre-loaded with every Windows + Thai production gotcha so edits are correct on the first run. Trigger when the user types /vdocut, or asks to edit / cut / ตัดต่อ / ทำคลิป / รวมคลิป / ใส่ซับ / ใส่เพลง / เร่งสปีด / ตัดวิดีโอ, or hands over video files to turn into a clip.
---

# /vdocut — ตัดต่อวิดีโอขั้นเทพ

This is the **god-tier wrapper** around the `video-use` toolchain, pre-loaded with the Windows + Thai gotchas this workflow has already paid for in blood. The base `video-use` SKILL.md is the canonical reference for craft; **this file overrides it wherever Windows/Thai correctness is at stake.** Read `video-use/SKILL.md` for deep craft (cut techniques, animation timing, grade theory) — read THIS for what actually works on Windows with Thai text.

> **External dependency** — `video-use` is a separate toolchain and is *not* bundled in this repo. Clone it yourself and point `$VIDEO_USE` at it. Everything below assumes it is available.

Communicate bilingually (สรุปไทย + technical EN) per the user's preference. Confirm strategy in plain Thai before touching any cut. Be autonomous once the plan is approved.

## 0. Environment (Windows — verified 2026-05-31)

- **ffmpeg / ffprobe**: install via `winget install Gyan.FFmpeg` and confirm plain `ffmpeg`/`ffprobe` resolve on PATH. If a fresh shell can't find them, call the WinGet install path directly.
- **uv**: `winget install astral-sh.uv` (Python runner used for every helper below).
- **video-use repo**: `$VIDEO_USE` (helpers in `helpers\`). Symlink/junction it into `~/.claude/skills/video-use` so the base craft doc loads too.
- **Run helpers** from the repo with uv: `uv run python helpers\render.py ...` (cwd = `$VIDEO_USE`).
- **ElevenLabs Scribe key**: put `ELEVENLABS_API_KEY` in `$VIDEO_USE\.env` (free tier ~2.5h/month — don't waste quota re-transcribing). Never write the key into the user's videos dir.
- **Always set `PYTHONIOENCODING=utf-8`** before running any helper, or `print("→ ...")` crashes the Windows console. In PowerShell: `$env:PYTHONIOENCODING="utf-8"`.

## 1. First decision — which path? (เลือกเส้นทางก่อน)

Ask one question of yourself before anything else: **does this job need cuts, transcript, grade, overlays, or subtitles?**

- **NO → REMIX SHORTCUT (§2).** Pure speed-change / crop / scale / audio-replace / BGM. One ffmpeg command, ~10× faster than the pipeline. Don't transcribe, don't build an EDL.
- **YES → FULL PIPELINE (§3).** Anything that needs decisions about *what to keep* or *how it looks*.

When unsure, ask the user in one Thai sentence: "งานนี้แค่เร่งสปีด/ครอป/ใส่เพลง หรือ ต้องตัดเลือกช่วง+ใส่ซับ+เกรดสีด้วย?"

## 2. REMIX SHORTCUT — speed / crop / BGM (no cuts)

Tested working on this machine. Fill the bracketed values:

```
ffmpeg -y -i <src.mp4> -stream_loop -1 -i <bgm.mp3> \
  -filter_complex "[0:v]scale=1920:1080:force_original_aspect_ratio=increase,crop=1920:1080,setpts=PTS/1.5,fps=30[v];[1:a]atrim=0:<out_secs>,afade=t=in:st=0:d=2,afade=t=out:st=<out_secs-3>:d=3,volume=0.85[a]" \
  -map "[v]" -map "[a]" -c:v libx264 -preset medium -crf 22 -pix_fmt yuv420p \
  -c:a aac -b:a 192k -ar 48000 -movflags +faststart -t <out_secs> <out.mp4>
```

Reusable building blocks:
- **Fill any aspect into 16:9 with no letterbox/distortion**: `scale=W:H:force_original_aspect_ratio=increase,crop=W:H`
- **Clean Nx speed**: `setpts=PTS/N` on video + `-t <src_dur/N>` on output (drop the audio or `atempo=N` it).
- **Loop BGM to exact length**: `-stream_loop -1 -i bgm.mp3` + `atrim=0:<out_secs>`.
- **Audio fades**: `afade=t=in:st=0:d=2,afade=t=out:st=<dur-3>:d=3`.
- **Vertical social** (TikTok/Reels): swap to `scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920`.

Always finish with loudnorm for social (see §6).

## 3. FULL PIPELINE — the process

Follow video-use's process, but with the overrides below. Order:

1. **Normalize filenames FIRST (§4)** — before transcribe or ffprobe touches them.
2. **Inventory**: `ffprobe` each source; `transcribe_batch.py` the dir (cached); `pack_transcripts.py` → `takes_packed.md`. For Thai, see §5 — don't trust pack output.
3. **Pre-scan** `takes_packed.md` for slips/mis-speaks. For Thai with mixed audio, sample real audio with `ffplay -ss <t> -t 10 <src>` — Scribe captures background bleed and produces misleading transcripts (§5).
4. **Converse**: describe what you see in plain Thai; ask material-shaped questions (content type, ความยาว/aspect, ฟีล, must-keep, must-cut, ซับ/เพลง/เกรด).
5. **Propose strategy (4–8 ประโยค ภาษาไทย) and WAIT for confirmation.** Never cut before "เอาตามนี้".
6. **Execute**: build `edl.json` (§7) with absolute forward-slash source paths. Drill `timeline_view` at ambiguous moments. Build animations in **parallel** sub-agents. Grade per-segment.
7. **Render** via `render.py` (§7). `--preview` first.
8. **Self-eval** on the *rendered output* (cut boundaries ±1.5s, first/last 2s, mid-points). Cap 3 passes, then flag remaining issues.
9. **Iterate + persist**: append to `<videos_dir>\edit\project.md`. Never re-transcribe.

All outputs go to **`<videos_dir>\edit\`** — never inside `$VIDEO_USE`.

## 4. Windows filename normalization (DO THIS FIRST)

Source filenames with **Thai chars / spaces / `#`** break ffmpeg's filter graphs silently. Before processing:

```
cmd /c mklink /H "EP84.mp4" "<original-with-thai-or-spaces.mp4>"
```

Hardlink (`/H`) needs no admin (NTFS, same volume only). Then **copy/rename the cached transcript JSON** to match the new ASCII name so the cache still hits. Use the ASCII name everywhere downstream (EDL `sources`, render).

## 5. Thai transcript reality (Scribe gotchas — non-negotiable)

- **Scribe returns Thai at CHARACTER level** (one entry per Thai char), with NO `spacing` ≥0.5s. So `pack_transcripts.py` collapses each take into one giant phrase. **Don't trust pack output for Thai** — read the raw `transcripts/<name>.json` for word timestamps and reason from those.
- **`--build-subtitles` is unusable for Thai** (chunks at 2 "words" = 2 Thai chars per cue). **Build a custom SRT instead** (§5.1), set EDL `subtitles: "master.srt"`, and run render WITHOUT `--build-subtitles`.
- **Mixed-audio sources** (screen recording with TV/family in background) make Scribe hallucinate topic jumps. If the transcript narrative lurches between unrelated topics, the audio is mixed — verify with `ffplay -ss <t> -t 10 <src>` before burning TTS/cut decisions or more quota.
- **Never re-transcribe** a cached source. Never run Whisper locally. Never cut inside a Thai word — snap to Scribe word boundaries, pad 30–200ms.

### 5.1 Custom Thai SRT chunker (heuristic that worked)

Accumulate ~28 chars per cue; break at a clause word (`ครับ` / `นะครับ` / `แล้วก็` / `และ` / `หรือ`) if one appears within the last 12 chars; hard-cap 36 chars. Write SRT cues on the **output timeline** (§7 offset rule). Cues may still break mid-word occasionally — true word-aware chunking needs `pythainlp` (only install if the user wants perfect breaks).

## 6. Loudnorm for social (always, on final)

Two-pass `loudnorm` to **-14 LUFS / -1 dBTP / LRA 11** (YT/IG/TT-ready). Pass 1 measures, pass 2 applies the measured values. Apply on the final mux. For the remix shortcut, append loudnorm as a second ffmpeg pass on the output.

## 7. render.py + EDL on Windows (the four patches)

Run: `$env:PYTHONIOENCODING="utf-8"; uv run python helpers\render.py <edl.json> -o <out.mp4> --preview` (from `$VIDEO_USE`).

**Before the first render of a fresh session, verify these local patches are still in `helpers\render.py`** (they're not upstream — a `git pull` wipes them):

1. Every `Path.read_text()` / `write_text()` passes `encoding="utf-8"` (Windows cp1252 can't encode `≥ → ` etc.).
2. `SUB_FORCE_STYLE` uses **Tahoma** not Helvetica (Helvetica missing on Windows; Tahoma supports Thai). Tuned values: `FontSize=22, MarginV=70, Outline=3, Shadow=1` for readable Thai burn-in.
3. Subtitle path (~line 523) does `.replace("\\", "/")` before the colon-escape, so `D:\edit\master.srt` → `D\:/edit/master.srt` for ffmpeg's filter syntax. Without it the filter chain fails.
4. (If missing, re-apply 1–3 with Edit before rendering, then note it.)

**EDL rules on this machine:**
- `sources` paths must be **absolute forward-slash** (`D:/edit/EP84.mp4`) or relative to `edit/`. `resolve_path()` joins relatives against `edit_dir`, NOT the videos dir.
- **Overlays have no x/y** — each overlay must be a **full 1920×1080 transparent canvas** (yuva420p WebM via libvpx-vp9; PIL→PNG→WebM with alpha). Position content inside the canvas.
- **Overlay sync**: `start_in_output` is on the OUTPUT timeline = `payoff_word_time - segment_source_start + cumulative_segment_offset`, minus ~1s so the reveal lands before the spoken payoff.
- Keep `clips_preview/` between renders — clips don't change unless EDL ranges or grade change. Re-running just the composite step is much faster.

EDL shape (see video-use SKILL.md §EDL format for the full schema): `version, sources{}, ranges[], grade, overlays[], subtitles, total_duration_s`.

## 8. Hard rules inherited from video-use (production correctness)

Memorize — deviation = silent failure:

1. **Subtitles applied LAST** in the filter chain (after every overlay).
2. **Per-segment extract → lossless `-c copy` concat** (not single-pass filtergraph) when overlays exist.
3. **30ms audio fades at every segment boundary**: `afade=t=in:st=0:d=0.03,afade=t=out:st={dur-0.03}:d=0.03`.
4. **Overlays use `setpts=PTS-STARTPTS+T/TB`** to shift frame 0 to window start.
5. **Master SRT on output-timeline offsets** (§7).
6. **Never cut inside a word**; pad 30–200ms (Scribe drifts 50–100ms).
7. **Word-level verbatim ASR only**; cache per source.
8. **Parallel sub-agents** for multiple animations (spawn N at once via Agent tool).
9. **Confirm strategy before execution.** Always.
10. **All outputs in `<videos_dir>\edit\`.**

## 9. Workflow on cold start

1. If `<videos_dir>\edit\project.md` exists, read it and summarize last session in one Thai sentence; ask whether to continue.
2. Verify `.env` has the Scribe key and ffmpeg is callable.
3. §4 normalize filenames → §1 pick the path → go.

## 10. Anti-patterns (เพิ่มจาก video-use)

- ❌ Running render.py on a Thai/space filename without hardlinking to ASCII first.
- ❌ Trusting `pack_transcripts.py` / `--build-subtitles` output for Thai.
- ❌ Forgetting `PYTHONIOENCODING=utf-8` → console crash.
- ❌ Relative EDL source paths that aren't relative to `edit/`.
- ❌ Re-transcribing cached sources / running Whisper locally.
- ❌ Editing before the user confirmed the plan in plain Thai.
- ❌ Full pipeline for a job that's just speed+crop+BGM (use §2 remix).
- ❌ Skipping loudnorm on social deliverables.
- ❌ edge-tts on punctuation-only text (e.g. "...") → exit 1, crashes a `check=True` loop. Guard + retry (§11).
- ❌ Burning subs from raw Scribe Thai (§5) — only the clean *translated* sentence SRT (§11.2) chunks well.

## 11. YouTube source + Thai DUB/SUB workflow (verified 2026-06-06)

Proven end-to-end on the 6-clip "The Problem Solvers" job (download EN talking-heads → full Thai dub **and** Netflix-style Thai-sub episodes). Outputs in `<videos_dir>\edit\` (`yt/`, `dub/`, `dubbed/`, `episodes/`, `scripts/`). Reusable scripts live in that job's `edit\scripts\` (`build_segments.py`, `make_dub.py`, `assemble.sh`, `build_srt.py`, `build_srt_per.py`, `burn_episodes.sh`) — copy them as a starting point.

### 11.0 Tools (install once via uv tool; land in `~\.local\bin\`, NOT on PATH — call by full path)
- `uv tool install yt-dlp` → `~/.local/bin/yt-dlp.exe`
- `uv tool install edge-tts` → `~/.local/bin/edge-tts.exe` (FREE Thai neural TTS, no quota/key). Thai voices: `th-TH-NiwatNeural` (male), `th-TH-PremwadeeNeural` (female).
- `uv pip install pydub` into the video-use venv (for overlay-by-ms assembly).

### 11.1 Download
`yt-dlp -f "bv*[height<=1080][ext=mp4]+ba[ext=m4a]/b[height<=1080]/b" --merge-output-format mp4 -o "<edit>/yt/NN_name.%(ext)s" <url>`. YouTube ships **AV1** video — always re-encode to H.264 (`libx264 crf 20`) for editing/concat. Get `duration`/`title` cheaply first with `--print "%(duration)s | %(title)s | %(id)s"` to scope quota/length before committing.

### 11.2 DUB pipeline (talking-head EN → Thai voice-over, per-sentence A/V sync)
1. Transcribe EN word-level (Scribe, `--language en`, cached).
2. `build_segments.py`: group Scribe `words` (type==word) into sentences — break on sentence punctuation OR gap ≥0.75s OR ~160 chars. Emit `dub/<name>.segments.json` = `[{idx,start,end,dur,en,th}]`.
3. Translate `en`→`th` with **parallel subagents** (one per video). Brief them: natural *spoken* Thai, polite ครับ where natural, keep brand/tech terms in English, and **length-match the `dur`** (terse EN → terse TH) so time-fit doesn't over-compress.
4. `make_dub.py`: per sentence → edge-tts (Niwat) mp3 → if natural dur > slot, `atempo` speed up (cap **1.5×**; never slow down — pad silence instead) → overlay onto a silent bed at `start*1000` ms via pydub → export `<name>.dub.wav`. **Guard:** skip `th` with no letters (`[\wก-๙]` regex — kills the "..." crash) and **retry edge-tts 3× w/ sleep** (transient network 1s failures are common).
5. `assemble.sh`: per clip `ffmpeg -map 0:v -map 1:a` (mute original, lay dub) + re-encode H.264 + `scale=...:force_original_aspect_ratio=decrease,pad=1920:1080,setsar=1` → concat demuxer `-c copy` → **2-pass loudnorm** -14 LUFS.
   - Expect ~90% of sentences to fit; a handful (fast/dense speakers) overflow ~0.3s into the next slot — acceptable, report the count honestly. Verify with a volumedetect sweep across the timeline (consistent ~-17dB = dub present throughout) + a frame grab.

### 11.3 SUB pipeline (keep original audio, burn clean Thai subs)
- Reuse the **translated `th`** (NOT raw Scribe Thai — §5 char-level is unusable; clean sentence Thai chunks fine). `build_srt.py` (combined, cumulative offsets = sum of source durations) or `build_srt_per.py` (per-episode, offset 0). Chunk ≤~56 chars, split on spaces at phrase edges, distribute the segment's [start,end] **proportionally by char count**, min 0.9s/cue, push overlaps down.
- Burn in one pass: `subtitles='<srt esc>':force_style='...'` — escape the path's colon (`sed 's/:/\\:/g'`), forward slashes, single ffmpeg pass also does concat (demuxer)+re-encode+loudnorm.
- **Default burn style** (readable on any bg): `FontName=Tahoma,FontSize=22,Outline=3,Shadow=1,MarginV=70`.
- **Netflix-style** (user asked "แบบ Netflix / ลงล่าง"): lower it + lighter — `FontName=Tahoma,FontSize=21,Outline=1.2,Shadow=1,MarginV=22`. MarginV is distance from bottom: smaller = lower. Watch for the source video's own lower-third name cards near the bottom; offer MarginV~40 to dodge them.
- Tahoma is the Thai-safe font on this machine (Helvetica missing). Always verify with a frame grab (Read the PNG) — don't trust that subs rendered.

### 11.4 Split into per-person episodes
Burn each original clip with its own per-episode SRT (offset 0) → `episodes/EPn_Company_Person.mp4`. Same single-pass burn as §11.3. Cheap to add a combined version too.
