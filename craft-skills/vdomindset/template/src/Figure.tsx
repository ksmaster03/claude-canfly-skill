import React from 'react';
import { ORANGE, SILVER } from './theme';

/**
 * A rigged 2D stick figure drawn as round-capped capsules.
 *
 * Local coordinate space: feet at (0, 0), the figure stands UP (negative y) and
 * faces +x (screen right). One unit = one pixel at scale 1, so a figure is ~226px tall.
 *
 * Angle convention for every joint: degrees, 0 = pointing straight DOWN,
 * positive = rotating toward +x (the direction the figure faces).
 * Child joints (knee, elbow) are RELATIVE to their parent segment.
 */

const THIGH = 48;
const SHIN = 48;
const TORSO = 76;
const NECK = 28;
const UPPER_ARM = 40;
const FOREARM = 40;
const HEAD_R = 26;

export const FIGURE_HEIGHT = THIGH + SHIN + TORSO + NECK + HEAD_R; // 226

export type Joints = {
  /** Forward lean of the whole upper body about the hip. + = leaning forward. */
  torsoLean: number;
  headTilt: number;
  /** "near" = the limb closest to camera, drawn brighter and on top. */
  thighNear: number;
  kneeNear: number;
  thighFar: number;
  kneeFar: number;
  armNear: number;
  elbowNear: number;
  armFar: number;
  elbowFar: number;
  /** Vertical bob of the whole body (negative = up). */
  bob?: number;
  /** Horizontal drift of the whole body. */
  sway?: number;
  /** Hip height override, e.g. sitting or squatting (default THIGH + SHIN). */
  hipY?: number;
};

type Pt = { x: number; y: number };

const proj = (p: Pt, angleDeg: number, len: number): Pt => {
  const a = (angleDeg * Math.PI) / 180;
  return { x: p.x + len * Math.sin(a), y: p.y + len * Math.cos(a) };
};

export type Tone = 'orange' | 'silver';

const TONES = {
  orange: { light: ORANGE.light, base: ORANGE.base, far: ORANGE.deep },
  silver: { light: SILVER.light, base: SILVER.base, far: SILVER.deep },
} as const;

export const FigureDefs: React.FC = () => (
  <defs>
    {(['orange', 'silver'] as Tone[]).map((tone) => (
      <linearGradient key={tone} id={`limb-${tone}`} x1="0" y1="0" x2="0.35" y2="1">
        <stop offset="0%" stopColor={TONES[tone].light} />
        <stop offset="55%" stopColor={TONES[tone].base} />
        <stop offset="100%" stopColor={TONES[tone].far} />
      </linearGradient>
    ))}
  </defs>
);

export const StickFigure: React.FC<{
  joints: Joints;
  tone: Tone;
  /** Extra rotation of the entire figure about its feet, e.g. for lying down. */
  rotate?: number;
}> = ({ joints, tone, rotate = 0 }) => {
  const c = TONES[tone];
  const j = joints;
  const bob = j.bob ?? 0;
  const sway = j.sway ?? 0;
  const hipY = -(j.hipY ?? THIGH + SHIN);

  const hip: Pt = { x: 0, y: hipY };

  // Legs hang off the hip.
  const kneeN = proj(hip, j.thighNear, THIGH);
  const footN = proj(kneeN, j.thighNear + j.kneeNear, SHIN);
  const kneeF = proj(hip, j.thighFar, THIGH);
  const footF = proj(kneeF, j.thighFar + j.kneeFar, SHIN);

  // Spine: 180deg is straight up, so leaning forward subtracts.
  const spineAngle = 180 - j.torsoLean;
  const shoulder = proj(hip, spineAngle, TORSO);
  const head = proj(shoulder, spineAngle - j.headTilt, NECK);

  const elbowN = proj(shoulder, j.armNear, UPPER_ARM);
  const handN = proj(elbowN, j.armNear + j.elbowNear, FOREARM);
  const elbowF = proj(shoulder, j.armFar, UPPER_ARM);
  const handF = proj(elbowF, j.armFar + j.elbowFar, FOREARM);

  const limb = (a: Pt, b: Pt, stroke: string, width: number) => (
    <line x1={a.x} y1={a.y} x2={b.x} y2={b.y} stroke={stroke} strokeWidth={width} strokeLinecap="round" />
  );

  return (
    <g transform={`translate(${sway}, ${bob}) rotate(${rotate})`}>
      {/* Far side first, dimmed, so the body reads as having depth. */}
      <g opacity={0.62}>
        {limb(hip, kneeF, c.far, 20)}
        {limb(kneeF, footF, c.far, 18)}
        {limb(shoulder, elbowF, c.far, 18)}
        {limb(elbowF, handF, c.far, 16)}
      </g>

      {limb(hip, shoulder, `url(#limb-${tone})`, 26)}

      {limb(hip, kneeN, `url(#limb-${tone})`, 22)}
      {limb(kneeN, footN, `url(#limb-${tone})`, 20)}

      <circle cx={head.x} cy={head.y} r={HEAD_R} fill={`url(#limb-${tone})`} />

      {limb(shoulder, elbowN, `url(#limb-${tone})`, 20)}
      {limb(elbowN, handN, `url(#limb-${tone})`, 18)}
    </g>
  );
};
