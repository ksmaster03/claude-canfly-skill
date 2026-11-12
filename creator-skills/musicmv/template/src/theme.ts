/**
 * Shared look and timing for the music video.
 *
 * Inherited from the vdomindset series, with one deliberate departure: the reel
 * format's "no cuts, must loop, under 10 seconds" rules exist because a 7-second
 * loop lives or dies on the seam. A full-length music video is a different
 * object — it cuts, on downbeats, and it ends. What carries over is the visual
 * language: one ground line, polished floor, steel props, and colour reserved
 * for the two things the viewer is meant to compare.
 */

export const W = 1080;
export const H = 1920;
export const FPS = 30;

/* ---------------------------------------------------------------- the song */
/* Fill these three in from the rendered take — measure, do not guess:
 *   python <vdomindset>/references/downbeat.py audio/<take>.mp3   -> BPM, phase
 *   ffprobe -v error -show_entries format=duration -of csv=p=0 …  -> length
 */

/** Bar grid — measured off the rendered track. */
export const BPM = 120;
export const BAR_S = (4 * 60) / BPM;
export const BAR_F = (i: number) => Math.round(i * BAR_S * FPS);

/** Where the track's bar grid actually starts (onset-flux phase). */
export const SONG_PHASE = 0;
/** Full length of the take, so the render covers the instrumental tail. */
export const SONG_S = 180;

/** Seconds -> frames, for cutting scenes onto the aligned vocal times. */
export const SEC_F = (s: number) => Math.round(s * FPS);

/** Snap a time to the nearest downbeat so cuts never land off the grid. */
export const snapBar = (s: number) => SONG_PHASE + Math.round((s - SONG_PHASE) / BAR_S) * BAR_S;

/**
 * Snap to the nearest half bar (beat 1 or beat 3).
 *
 * Used inside densely sung sections such as a rap, where lines land about two
 * bars apart: snapping those to whole bars can drag a cut most of a second
 * early, which puts the new picture up while the previous line is still being
 * delivered. Beat 3 is still on the grid.
 */
export const snapHalf = (s: number) =>
  SONG_PHASE + Math.round(((s - SONG_PHASE) / BAR_S) * 2) * (BAR_S / 2);

/* -------------------------------------------------------------- the layout */

/** The single ground line both sides stand on. */
export const HORIZON = 1010;
export const LEFT_X = W / 2 - 252;
export const RIGHT_X = W / 2 + 252;

export const LABEL_Y = HORIZON + 86;
/** Caption zone. Nothing else may occupy roughly y 292–340. */
export const GOAL_Y = 292;
/** Lyric band, kept well clear of the labels so the two never collide. */
export const LYRIC_Y = 1560;

/** The side that has help. */
export const ORANGE = {
  light: '#FFB259',
  base: '#FF7A1A',
  deep: '#B34E00',
  text: '#FF9440',
};

/** Everyone still doing it by hand. */
export const SILVER = {
  light: '#D8D8D8',
  base: '#A8A8A8',
  deep: '#6E6E6E',
  text: '#A6A6AB',
};

export const BRAND_GREEN = '#60FFBF';
export const STEEL = '#8A8A8E';
export const STEEL_DARK = '#4A4A4E';

/** Red only ever means "this is broken" — a failing test, a bug, a risky clause. */
export const RED = '#E0524A';

export const WATER = {
  light: '#1E6E9E',
  base: '#124E74',
  deep: '#08243A',
};

/** Polished, not a mirror — labels sit inside the reflection band. */
export const REFLECTION = {
  opacity: 0.2,
  blurPx: 3,
  fadeHeight: 150,
};

export const SUBJECT_SCALE = 1.35;
