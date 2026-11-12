import timeline from './timeline.json';
import { BAR_S, FPS, SONG_PHASE } from './theme';

/**
 * The song itself, as data.
 *
 * `timeline.json` is generated from Suno's word-level alignment of the rendered
 * take (tools/timeline.py), so section starts and lyric lines are the vocal's
 * real times — not an estimate off the lyric sheet. That matters because the
 * track is compressed nearly flat (loudest bar -13.7 dB, quietest -21.2), so
 * energy-based structure detection finds nothing to grab onto.
 */

export type Line = { text: string; start: number; end: number };
export type Section = { tag: string; start: number };

export const SECTIONS = timeline.sections as Section[];
export const LINES = timeline.lines as Line[];

/** Elapsed bars since the track's first downbeat — the clock every motion uses. */
export const barsAt = (seconds: number) => (seconds - SONG_PHASE) / BAR_S;

/**
 * Phase in [0,1) that completes `cyclesPerBar` cycles every bar.
 *
 * `offset` shifts the cycle without breaking the lock — used to put two figures
 * on the same beat but out of step with each other, which reads as two people
 * rather than one person mirrored.
 */
export const beatPhase = (bars: number, cyclesPerBar = 1, offset = 0) => {
  const v = (bars * cyclesPerBar + offset) % 1;
  return v < 0 ? v + 1 : v;
};

/** Eased 0..1 pulse that peaks on each downbeat — for hits that land with the snare. */
export const beatPulse = (bars: number, cyclesPerBar = 1) => {
  const p = beatPhase(bars, cyclesPerBar);
  return Math.pow(1 - p, 3);
};

/** The lyric line being sung at `seconds`, or null between lines. */
export const lineAt = (seconds: number): Line | null => {
  for (const l of LINES) {
    // Hold each line a beat past its last word so it does not flicker out
    // mid-phrase while the singer is still on the same thought.
    if (seconds >= l.start - 0.12 && seconds <= l.end + 0.35) return l;
  }
  return null;
};

export const frameToSec = (frame: number) => frame / FPS;
