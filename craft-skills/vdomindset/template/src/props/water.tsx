import React from 'react';
import { ORANGE, WATER } from '../theme';

/** Bucket geometry, shared by the fill clip so the water can never draw outside it. */
const TOP_W = 58;
const BOT_W = 43;
export const BUCKET_H = 118;
const BODY = `M ${-TOP_W},${-BUCKET_H} L ${TOP_W},${-BUCKET_H} L ${BOT_W},0 L ${-BOT_W},0 Z`;

/**
 * A bucket with a water level.
 *
 * `level` is 0..1 of the internal height. `hole` puts a gap in the left wall,
 * `patch` covers that same spot in orange — the two sides of the clip differ by
 * exactly one prop, which is the whole point of the shot.
 */
export const Bucket: React.FC<{
  id: string;
  x: number;
  level: number;
  hole?: boolean;
  patch?: boolean;
  overflow?: number;
}> = ({ id, x, level, hole, patch, overflow = 0 }) => {
  const surface = -BUCKET_H * Math.max(0, Math.min(1, level));
  return (
    <g transform={`translate(${x}, 0)`}>
      <clipPath id={`bucket-${id}`}>
        <path d={BODY} />
      </clipPath>

      {/* handle, behind the pail */}
      <path
        d={`M ${-TOP_W + 6} ${-BUCKET_H - 2} q 0 -44 ${TOP_W - 6} -44 q ${TOP_W - 6} 0 ${TOP_W - 6} 44`}
        fill="none" stroke="url(#steel)" strokeWidth={6} strokeLinecap="round"
      />

      {/* dark interior, so the pail reads as a container even when nearly empty */}
      <path d={BODY} fill="#17171B" />

      <g clipPath={`url(#bucket-${id})`}>
        <rect x={-TOP_W} y={surface} width={TOP_W * 2} height={BUCKET_H + 4} fill="url(#waterGrad)" />
        <rect x={-TOP_W} y={surface} width={TOP_W * 2} height={5} fill={WATER.light} opacity={0.95} />
      </g>

      <path d={BODY} fill="none" stroke="url(#steelFlat)" strokeWidth={8} strokeLinejoin="round" />
      <rect x={-TOP_W - 6} y={-BUCKET_H - 9} width={(TOP_W + 6) * 2} height={10} rx={5} fill="url(#steel)" />

      {hole ? (
        <g>
          <circle cx={-BOT_W - 6} cy={-52} r={10} fill="#0C0C0C" />
          <circle cx={-BOT_W - 6} cy={-52} r={10} fill="none" stroke="#2A2A2E" strokeWidth={3} />
        </g>
      ) : null}
      {patch ? (
        <g>
          <rect x={-BOT_W - 15} y={-40} width={26} height={28} rx={5} fill="url(#orangeGrad)" />
          <rect x={-BOT_W - 11} y={-35} width={18} height={4} rx={2} fill={ORANGE.light} opacity={0.7} />
        </g>
      ) : null}

      {/* Spilling over the rim — drawn last so it sits on top of the pail wall. */}
      {overflow > 0 ? (
        <g opacity={overflow}>
          <path
            d={`M ${TOP_W - 6} ${-BUCKET_H + 5} q 20 6 24 34 q 4 32 -2 ${BUCKET_H - 34}`}
            stroke={WATER.light} strokeWidth={6} fill="none" strokeLinecap="round" opacity={0.7}
          />
        </g>
      ) : null}
    </g>
  );
};

/** Water that got away. */
export const Puddle: React.FC<{ x: number; w: number }> = ({ x, w }) => (
  <ellipse cx={x} cy={-3} rx={w} ry={9} fill="url(#waterGrad)" opacity={0.55} />
);

/**
 * Drips falling out of the hole. `p` is the loop phase; drops are spaced by index
 * so the stream is continuous and reaches the same state at p = 0 and p = 1.
 */
export const Drips: React.FC<{ x: number; y: number; p: number; n?: number }> = ({ x, y, p, n = 4 }) => (
  <g>
    {Array.from({ length: n }, (_, i) => {
      const u = (p * 2 + i / n) % 1;
      return (
        <ellipse
          key={i}
          cx={x - u * 5}
          cy={y + u * (Math.abs(y) - 6)}
          rx={5} ry={7 + u * 3}
          fill={WATER.light}
          opacity={0.85 * (1 - u * 0.5)}
        />
      );
    })}
  </g>
);

/** A steady pour from a source down into a bucket. */
export const Stream: React.FC<{ x: number; from: number; to: number; p: number }> = ({ x, from, to, p }) => (
  <g>
    <rect x={x - 6} y={from} width={12} height={to - from} rx={6} fill="url(#waterGrad)" opacity={0.65} />
    {[0, 1, 2].map((i) => {
      const u = (p * 3 + i / 3) % 1;
      return (
        <ellipse key={i} cx={x} cy={from + u * (to - from)} rx={7} ry={11} fill={WATER.light} opacity={0.5} />
      );
    })}
  </g>
);

/** The small pail the manual side keeps carrying. Drawn into the figure's hand. */
export const Pail: React.FC<{ x: number; y: number; rot: number }> = ({ x, y, rot }) => (
  <g transform={`translate(${x}, ${y}) rotate(${rot})`}>
    <path d="M -20 -22 L 20 -22 L 15 6 L -15 6 Z" fill="url(#steelFlat)" />
    <path d="M -20 -22 q 20 -18 40 0" stroke="url(#steel)" strokeWidth={4} fill="none" />
    <rect x={-18} y={-18} width={36} height={9} fill={WATER.base} opacity={0.85} />
  </g>
);
