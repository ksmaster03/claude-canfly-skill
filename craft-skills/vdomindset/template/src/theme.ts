/**
 * Shared look and timing for the whole series.
 *
 * The format is derived from measurement, not taste: across 623 reels on the
 * reference page, the top 50 (which carry 83% of all views) run a median of
 * 7.6s with zero cuts, while the mid-band runs 30.7s. So every clip here is
 * 3 or 4 musical bars long and loops.
 */

export const W = 1080;
export const H = 1920;
export const FPS = 30;

/** Bar grid. Everything times off this, never off raw frame numbers. */
export const BPM = 113.5;
export const BAR_S = (4 * 60) / BPM; // 2.1145s
export const BAR_F = (i: number) => Math.round(i * BAR_S * FPS);

/** The single ground line both sides stand on. */
export const HORIZON = 1010;
/** Where each side's content is centred. */
export const LEFT_X = W / 2 - 252;
export const RIGHT_X = W / 2 + 252;

export const LABEL_Y = HORIZON + 86;
export const GOAL_Y = 292;
export const LOGO_Y = 1648;

/** โกสินทร์ — the only warm thing in frame. */
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

/** One environment colour is allowed — the reference page uses blue water. */
export const WATER = {
  light: '#1E6E9E',
  base: '#124E74',
  deep: '#08243A',
};

/**
 * The floor is polished, not a mirror. Kept weaker than the 22s piece because
 * labels now sit inside the reflection band and have to stay legible.
 */
export const REFLECTION = {
  opacity: 0.2,
  blurPx: 3,
  fadeHeight: 150,
};

export const SUBJECT_SCALE = 1.35;
