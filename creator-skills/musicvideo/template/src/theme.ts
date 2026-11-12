/**
 * Look and timing for the "AI HARD, BURN TOKEN HARD" music video.
 *
 * Every number under "the song" was measured off the audio, not guessed --
 * see tools/analyse.py output recorded in NOTES.md. The tempo matters more
 * than it looks: the track runs 297s, so a 1 BPM error walks the grid ~2.3s
 * off by the end, which is more than a full bar of drift on the last chorus.
 */

/* ------------------------------------------------------------- formats */

export type Format = {
  W: number;
  H: number;
  /** Rough share of the frame the photographic backdrop occupies. */
  backdropH: number;
};

export const WIDE: Format = { W: 1920, H: 1080, backdropH: 1080 };
export const TALL: Format = { W: 1080, H: 1920, backdropH: 1080 };

export const FPS = 30;

/* -------------------------------------------------------------- the song */

/**
 * The song, read from the file the measurements were written to.
 *
 * These were hand-copied constants once. Carrying the template to a second
 * song then meant a theme that still said 129.26 BPM and 297.04s while the
 * new track ran 132.62 and 299.96 -- a video 2.9s short of its own outro with
 * every beat-locked motion drifting. Importing the measurement removes the
 * copy step, so the two cannot disagree.
 *
 * Regenerate with: python tools/analyse.py
 */
import features from './features.json';

export const BPM = features.bpm;
export const BEAT_S = 60 / BPM;
export const BAR_S = 4 * BEAT_S;

/** First beat of the track. */
export const BEAT_PHASE = features.beatPhase;

/**
 * Which beat of four opens the bar is not always resolvable -- on a
 * four-on-the-floor groove the kick lands on all four and the candidates
 * score within noise of each other. Nothing here snaps to whole bars for that
 * reason; cuts snap to beats and half bars, which land on a kick either way.
 */
export const DURATION_S = features.duration;
export const TOTAL_FRAMES = features.frames;

export const SEC_F = (s: number) => Math.round(s * FPS);
export const F_SEC = (f: number) => f / FPS;

/** Elapsed beats since the first beat -- the clock every motion reads. */
export const beatsAt = (seconds: number) => (seconds - BEAT_PHASE) / BEAT_S;

/** Snap a time to the nearest beat so a cut never lands between kicks. */
export const snapBeat = (s: number) =>
  BEAT_PHASE + Math.round((s - BEAT_PHASE) / BEAT_S) * BEAT_S;

/** Snap to the nearest half bar (two beats) -- for scene-length cuts. */
export const snapHalfBar = (s: number) =>
  BEAT_PHASE + Math.round((s - BEAT_PHASE) / (2 * BEAT_S)) * (2 * BEAT_S);

/* -------------------------------------------------------------- palette */

/** Coral, the brand's own key colour and what the stills were lit with. */
export const AMBER = {
  light: '#FFB199',
  base: '#FF6B4A',
  deep: '#C33C22',
  glow: 'rgba(255,107,74,0.55)',
};

/** Violet rim. Cyan read as cold sci-fi against the cartoon stills; violet sits
 *  in the same family as the deep navy ground and keeps the frame warm. */
export const CYAN = {
  light: '#C9A7FF',
  base: '#8A5BFF',
  deep: '#3C2178',
  glow: 'rgba(138,91,255,0.45)',
};

export const INK = '#140B22';   // deep navy purple, not black -- the stills are lit warm
export const SMOKE = '#B9A8CE';
export const PAPER = '#FFF6EC';   // cream

/** Display face. Sarabun, embedded in src/fonts.ts.
 *
 *  The previous video used Arial Black, which has no Thai glyphs -- this song
 *  is in Thai, so that stack would render the entire lyric as tofu boxes.
 *  Sarabun ExtraBold carries Thai and English at a weight that holds up over
 *  a busy cartoon frame. */
export const DISPLAY = "'Sarabun', 'Leelawadee UI', 'Segoe UI', sans-serif";
/** Thai marks sit above and below the line; extra tracking pulls them off the
 *  glyph they belong to. Never letter-space Thai. */
export const THAI_TRACKING = 0;
export const MONO = "'Consolas', 'SF Mono', ui-monospace, monospace";

export const TITLE = 'myWeekend';
export const ARTIST = 'kosin_finsure';
