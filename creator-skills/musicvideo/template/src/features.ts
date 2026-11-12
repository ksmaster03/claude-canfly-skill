/**
 * The track, sampled once per video frame.
 *
 * features.json is built by tools/analyse.py off the MASTERED audio -- the
 * mix the viewer actually hears -- so a cone that looks like it is moving on
 * the bass really is moving on the bass they hear, not on a different render.
 * Bands are normalised 5th..99th percentile, so 0 is "quiet for this track"
 * and 1 is "about as loud as this track gets", not an absolute dB.
 */
import data from './features.json';

export type BandName = 'sub' | 'bass' | 'lowmid' | 'mid' | 'high';

export type Scene = {
  img: string;
  start: number;
  end: number;
  bars: number;
  dir: number;
};

const BANDS = data.bands as Record<BandName, number[]>;
const RMS = data.rms as number[];
const SPEC = data.spectrum as number[][];
export const NBINS = SPEC[0]?.length ?? 0;
export const SCENES = data.scenes as Scene[];
export const FRAMES = data.frames as number;

const at = (arr: number[], frame: number) =>
  arr[Math.max(0, Math.min(arr.length - 1, frame))] ?? 0;

export const band = (frame: number, name: BandName) => at(BANDS[name], frame);
export const rms = (frame: number) => at(RMS, frame);

/** One frame of the 48-bin log-spaced analyser, 30 Hz .. 11 kHz. */
export const spectrum = (frame: number): number[] =>
  SPEC[Math.max(0, Math.min(SPEC.length - 1, frame))] ?? [];

/**
 * Envelope follower: snaps up, eases down.
 *
 * Raw per-frame band energy jitters enough to make a speaker cone buzz rather
 * than pump. A fast attack keeps the hit on the kick; a slow release is what
 * reads as a cone travelling back out rather than teleporting.
 */
export const envelope = (
  frame: number,
  name: BandName,
  attack = 0.55,
  release = 0.10,
) => {
  const look = 8; // frames of history is plenty at 30fps
  let v = band(Math.max(0, frame - look), name);
  for (let f = frame - look + 1; f <= frame; f++) {
    const x = band(f, name);
    v += (x - v) * (x > v ? attack : release);
  }
  return v;
};

/** The scene covering `seconds`, and how far through it we are (0..1). */
export const sceneAt = (seconds: number) => {
  for (let i = 0; i < SCENES.length; i++) {
    const s = SCENES[i];
    if (seconds >= s.start && seconds < s.end) {
      return { scene: s, index: i, t: (seconds - s.start) / (s.end - s.start) };
    }
  }
  const last = SCENES[SCENES.length - 1];
  return { scene: last, index: SCENES.length - 1, t: 1 };
};
