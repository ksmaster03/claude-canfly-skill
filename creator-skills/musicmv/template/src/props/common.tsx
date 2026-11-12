import React from 'react';
import { BRAND_GREEN, ORANGE, RED, STEEL, STEEL_DARK, WATER } from '../theme';

/**
 * Gradients shared by every prop and figure.
 *
 * These MUST be rendered inside every <svg> that paints a figure or prop. SVG
 * paint servers resolve document-wide, so it is easy to get away with one copy
 * until the element that hosts it unmounts — then everything painted with
 * url(#…) silently drops to no fill.
 */
export const PropDefs: React.FC = () => (
  <defs>
    <linearGradient id="steel" x1="0" y1="0" x2="0.2" y2="1">
      <stop offset="0%" stopColor="#C6C6CA" />
      <stop offset="60%" stopColor={STEEL} />
      <stop offset="100%" stopColor={STEEL_DARK} />
    </linearGradient>
    <linearGradient id="steelFlat" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%" stopColor="#9E9EA3" />
      <stop offset="100%" stopColor="#55555A" />
    </linearGradient>
    <linearGradient id="orangeGrad" x1="0" y1="0" x2="0.25" y2="1">
      <stop offset="0%" stopColor={ORANGE.light} />
      <stop offset="55%" stopColor={ORANGE.base} />
      <stop offset="100%" stopColor={ORANGE.deep} />
    </linearGradient>
    <linearGradient id="waterGrad" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%" stopColor={WATER.light} />
      <stop offset="55%" stopColor={WATER.base} />
      <stop offset="100%" stopColor={WATER.deep} />
    </linearGradient>
    <radialGradient id="orb">
      <stop offset="0%" stopColor="#FFF0DC" />
      <stop offset="35%" stopColor={ORANGE.light} />
      <stop offset="70%" stopColor={ORANGE.base} />
      <stop offset="100%" stopColor="rgba(255,122,26,0)" />
    </radialGradient>
    <radialGradient id="orbHalo">
      <stop offset="0%" stopColor="rgba(255,122,26,0.40)" />
      <stop offset="100%" stopColor="rgba(255,122,26,0)" />
    </radialGradient>
    {/* Red and green are the only other colours allowed on props, and only for
        state that is literally pass/fail — a red test, a bug, a risky clause.
        Using them decoratively would break the rule that colour means "alive". */}
    <linearGradient id="redGrad" x1="0" y1="0" x2="0.25" y2="1">
      <stop offset="0%" stopColor="#FF8A82" />
      <stop offset="55%" stopColor={RED} />
      <stop offset="100%" stopColor="#8E2820" />
    </linearGradient>
    <linearGradient id="greenGrad" x1="0" y1="0" x2="0.25" y2="1">
      <stop offset="0%" stopColor="#A8FFD8" />
      <stop offset="55%" stopColor={BRAND_GREEN} />
      <stop offset="100%" stopColor="#1E8F63" />
    </linearGradient>
  </defs>
);

/** The AI, whenever a clip needs it on screen: a core with two counter-rotating arcs. */
export const AiOrb: React.FC<{ x: number; y: number; t: number; r?: number }> = ({ x, y, t, r = 20 }) => (
  <g transform={`translate(${x}, ${y}) scale(${1 + 0.06 * Math.sin(t * Math.PI * 2)})`}>
    <circle r={r * 3.2} fill="url(#orbHalo)" />
    <circle r={r} fill="url(#orb)" />
    <circle
      r={r * 1.7} fill="none" stroke={ORANGE.base} strokeWidth={3} strokeLinecap="round"
      strokeDasharray={`${r * 2.4} ${r * 8}`} opacity={0.85} transform={`rotate(${t * 360})`}
    />
    <circle
      r={r * 2.3} fill="none" stroke={ORANGE.light} strokeWidth={2} strokeLinecap="round"
      strokeDasharray={`${r * 1.6} ${r * 12}`} opacity={0.55} transform={`rotate(${-t * 720})`}
    />
  </g>
);
