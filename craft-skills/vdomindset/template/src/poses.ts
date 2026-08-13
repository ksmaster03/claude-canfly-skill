import type { Joints } from './Figure';

/**
 * Poses for the series.
 *
 * Every pose is a function of a PHASE p in [0,1) — one full cycle of the action.
 * The clip decides how many cycles fit its length via `saw(u, cycles)` with an
 * integer cycle count, which is what makes each clip loop without a seam.
 *
 * Angle convention (see Figure.tsx): 0 = straight down, positive = toward the
 * direction the figure faces (+x). Knees bend backwards, so knee angles stay
 * negative.
 */

export type PoseState = { joints: Joints; rotate?: number; x?: number; y?: number };

const TAU = Math.PI * 2;
/** 0 at p=0, 1 at p=0.5, back to 0 at p=1 — a there-and-back with no seam. */
const swing = (p: number) => (1 - Math.cos(p * TAU)) / 2;

/** Idle, chest up, breathing. */
export const standing = (p: number): PoseState => ({
  joints: {
    torsoLean: -4, headTilt: -5,
    thighNear: 5, kneeNear: -6, thighFar: -5, kneeFar: -5,
    armNear: 8, elbowNear: -10, armFar: -9, elbowFar: -8,
    bob: 2.2 * Math.sin(p * TAU),
  },
});

/** Standing, near arm out toward whatever the clip wants him looking at. */
export const pointing = (p: number): PoseState => ({
  joints: {
    torsoLean: -3, headTilt: 2,
    thighNear: 6, kneeNear: -8, thighFar: -6, kneeFar: -6,
    armNear: 58 + 3 * Math.sin(p * TAU), elbowNear: 42 + 4 * Math.sin(p * TAU),
    armFar: -12, elbowFar: -14,
    bob: 1.8 * Math.sin(p * TAU),
  },
});

/** Both arms up — the clip's "done, and it wasn't even hard" beat. */
export const celebrate = (p: number): PoseState => ({
  joints: {
    torsoLean: -8, headTilt: -14,
    thighNear: 7, kneeNear: -8, thighFar: -7, kneeFar: -7,
    armNear: 168, elbowNear: 8, armFar: 172, elbowFar: 6,
    bob: -3 + 3 * Math.sin(p * TAU),
  },
});

/** Bend down, scoop, lift, tip. Used for anything repetitive and manual. */
export const scooping = (p: number): PoseState => {
  const b = swing(p);
  return {
    joints: {
      torsoLean: 12 + 52 * b, headTilt: 8 + 16 * b,
      hipY: 96 - 20 * b,
      thighNear: 10 + 28 * b, kneeNear: -12 - 44 * b,
      thighFar: -8 + 24 * b, kneeFar: -10 - 40 * b,
      armNear: 26 + 44 * b, elbowNear: -16 + 22 * b,
      armFar: 22 + 40 * b, elbowFar: -14 + 20 * b,
      bob: 0,
    },
  };
};

/** Bend forward and reach down to set something on the ground, then straighten. */
export const placing = (p: number): PoseState => {
  const b = swing(p);
  return {
    joints: {
      torsoLean: 8 + 46 * b, headTilt: 6 + 20 * b,
      hipY: 96 - 14 * b,
      thighNear: 8 + 20 * b, kneeNear: -10 - 34 * b,
      thighFar: -6 + 16 * b, kneeFar: -8 - 30 * b,
      armNear: 30 + 52 * b, elbowNear: -10 + 16 * b,
      armFar: -10, elbowFar: -12,
      bob: 0,
    },
  };
};

/** A walk: same structure as a run, smaller swing and a straighter support leg. */
export const walking = (p: number): PoseState => {
  const a = p * TAU;
  return {
    joints: {
      torsoLean: 6, headTilt: -3,
      thighNear: 26 * Math.sin(a), kneeNear: -30 + 24 * Math.cos(a),
      thighFar: 26 * Math.sin(a + Math.PI), kneeFar: -30 + 24 * Math.cos(a + Math.PI),
      armNear: -22 * Math.sin(a), elbowNear: 26,
      armFar: -22 * Math.sin(a + Math.PI), elbowFar: 26,
      bob: -1 + 2.5 * Math.cos(2 * a),
    },
  };
};

/** Walking while holding something out in front with both hands. */
export const carrying = (p: number): PoseState => {
  const a = p * TAU;
  return {
    joints: {
      torsoLean: 12, headTilt: 4,
      thighNear: 22 * Math.sin(a), kneeNear: -32 + 22 * Math.cos(a),
      thighFar: 22 * Math.sin(a + Math.PI), kneeFar: -32 + 22 * Math.cos(a + Math.PI),
      armNear: 68, elbowNear: 22, armFar: 64, elbowFar: 24,
      bob: -1 + 2.5 * Math.cos(2 * a),
    },
  };
};

/** Leaning hard into something heavy, legs grinding. */
export const pushing = (p: number): PoseState => {
  const a = p * TAU;
  return {
    joints: {
      torsoLean: 30, headTilt: -10,
      thighNear: 22 + 16 * Math.sin(a), kneeNear: -34 + 18 * Math.cos(a),
      thighFar: -18 + 16 * Math.sin(a + Math.PI), kneeFar: -24 + 18 * Math.cos(a + Math.PI),
      armNear: 68, elbowNear: 14, armFar: 64, elbowFar: 16,
      bob: 1.5 * Math.cos(2 * a),
    },
  };
};

/** Seated, feet forward — the base for a boat, a chair or a forklift cab. */
export const sitting = (p: number): PoseState => ({
  joints: {
    torsoLean: -4, headTilt: 2,
    hipY: 52,
    thighNear: 92, kneeNear: -88, thighFar: 88, kneeFar: -80,
    armNear: 46, elbowNear: 30, armFar: 42, elbowFar: 34,
    bob: 1.6 * Math.sin(p * TAU),
  },
});

/** Seated and hauling on a pair of oars. */
export const rowing = (p: number): PoseState => {
  const s = Math.sin(p * TAU);
  return {
    joints: {
      torsoLean: 10 + 20 * s, headTilt: 4,
      hipY: 52,
      thighNear: 92, kneeNear: -86, thighFar: 88, kneeFar: -80,
      armNear: 52 + 34 * s, elbowNear: 26 - 22 * s,
      armFar: 48 + 34 * s, elbowFar: 30 - 22 * s,
      bob: 0,
    },
  };
};

/**
 * โกสินทร์ flies — the signature shot.
 *
 * Do not straighten this out: leading arm along the body axis plus straight legs
 * puts every segment on one line and the figure renders as a rod. The legs are
 * split and one knee trails to keep the silhouette a person.
 */
export const flying = (p: number): PoseState => ({
  joints: {
    torsoLean: -10, headTilt: -16,
    thighNear: 22 + 5 * Math.sin(p * TAU), kneeNear: -58,
    thighFar: -16 + 5 * Math.sin(p * TAU + 1), kneeFar: -10,
    armNear: 168, elbowNear: 10, armFar: -42, elbowFar: -30,
    bob: 0,
  },
  rotate: 40,
});
