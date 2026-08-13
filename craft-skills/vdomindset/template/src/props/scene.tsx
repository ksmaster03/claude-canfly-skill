import React from 'react';
import { ORANGE, SILVER, STEEL_DARK, WATER } from '../theme';

/**
 * Props for clips 2–8. Local coords: ground (or waterline) at y = 0, subject
 * centred on x = 0, facing +x.
 *
 * Everything animated here is driven by a phase in [0,1) so it returns to its
 * start exactly at the loop point — no Math.random anywhere, or the shape would
 * reshuffle every frame.
 */

/* ------------------------------------------------------------------ water */

/** Full-width water surface with a gentle travelling swell. */
export const WaterBand: React.FC<{ y: number; p: number; depth?: number }> = ({ y, p, depth = 240 }) => {
  const pts: string[] = [];
  for (let x = -120; x <= 1200; x += 30) {
    const wob = Math.sin((x / 300 + p) * Math.PI * 2) * 6 + Math.sin((x / 130 - p * 2) * Math.PI * 2) * 3;
    pts.push(`${x},${y + wob}`);
  }
  return (
    <g>
      <path d={`M -120,${y + 200} L ${pts.join(' L ')} L 1200,${y + 200} Z`} fill="url(#waterGrad)" opacity={0.92} />
      <polyline points={pts.join(' ')} fill="none" stroke={WATER.light} strokeWidth={4} opacity={0.8} />
      <rect x={-120} y={y + 40} width={1320} height={depth} fill={WATER.deep} opacity={0.35} />
    </g>
  );
};

/** Rowboat hull. The seat sits at y = -46 so a `sitting` figure lands in it. */
export const Hull: React.FC<{ tone: 'silver' | 'orange'; motor?: boolean }> = ({ tone, motor }) => {
  const paint = tone === 'orange' ? 'url(#orangeGrad)' : 'url(#steelFlat)';
  return (
    <g>
      <path d="M -108 -34 L 112 -34 L 88 10 L -84 10 Z" fill={paint} />
      <path d="M -108 -34 L 112 -34 L 108 -26 L -104 -26 Z" fill="#0E0E10" opacity={0.45} />
      {motor ? (
        <g transform="translate(-100, -44)">
          <rect x={-18} y={0} width={30} height={34} rx={6} fill="url(#steel)" />
          <rect x={-8} y={-14} width={12} height={16} rx={4} fill={STEEL_DARK} />
        </g>
      ) : null}
    </g>
  );
};

/** Oar, angled from the rower's hands out into the water. */
export const Oar: React.FC<{ x: number; angle: number }> = ({ x, angle }) => (
  <g transform={`translate(${x}, -60) rotate(${angle})`}>
    <rect x={-4} y={0} width={8} height={104} rx={4} fill="url(#steel)" />
    <ellipse cx={0} cy={112} rx={13} ry={22} fill="url(#steelFlat)" />
  </g>
);

/** Wake trailing behind a boat — length is the whole story of the shot. */
export const Wake: React.FC<{ x: number; y: number; len: number; p: number; strong?: boolean }> = ({ x, y, len, p, strong }) => (
  <g>
    {[0, 1, 2].map((i) => {
      const u = (p * (strong ? 3 : 1.2) + i / 3) % 1;
      return (
        <ellipse
          key={i}
          cx={x - u * len}
          cy={y + i * 5}
          rx={30 + u * len * 0.45}
          ry={5 + i}
          fill={WATER.light}
          opacity={(strong ? 0.5 : 0.25) * (1 - u)}
        />
      );
    })}
    {strong
      ? [0, 1, 2, 3].map((i) => {
          const u = (p * 4 + i / 4) % 1;
          return (
            <circle key={`s${i}`} cx={x - 20 - u * 90} cy={y - 20 - Math.sin(u * Math.PI) * 44} r={7 - u * 4}
              fill={WATER.light} opacity={0.65 * (1 - u)} />
          );
        })
      : null}
  </g>
);

/* ---------------------------------------------------------------- terrain */

/**
 * A route drawn as a polyline the "traveller" rides along.
 * `shape` returns a height (positive = up) for x in 0..1 across the lane.
 */
export const Route: React.FC<{ shape: (t: number) => number; tone: 'silver' | 'orange' }> = ({ shape, tone }) => {
  const pts: string[] = [];
  for (let i = 0; i <= 100; i++) {
    const t = i / 100;
    pts.push(`${60 + t * 960},${-shape(t)}`);
  }
  return (
    <polyline
      points={pts.join(' ')}
      fill="none"
      stroke={tone === 'orange' ? ORANGE.deep : SILVER.deep}
      strokeWidth={7}
      strokeLinecap="round"
      opacity={0.9}
    />
  );
};

/** Position + slope angle at t along a route, so a boulder can sit on it properly. */
export const routeAt = (shape: (t: number) => number, t: number) => {
  const d = 0.004;
  const y0 = shape(Math.max(0, t - d));
  const y1 = shape(Math.min(1, t + d));
  return {
    x: 60 + t * 960,
    y: -shape(t),
    angle: (Math.atan2(-(y1 - y0), (2 * d) * 960) * 180) / Math.PI,
  };
};

export const Boulder: React.FC<{ r: number; tone: 'silver' | 'orange'; spin: number }> = ({ r, tone, spin }) => (
  <g transform={`rotate(${spin})`}>
    <circle r={r} fill={tone === 'orange' ? 'url(#orangeGrad)' : 'url(#steelFlat)'} />
    <path d={`M ${-r * 0.5} ${-r * 0.4} L ${r * 0.3} ${-r * 0.1}`} stroke="#00000055" strokeWidth={4} strokeLinecap="round" />
    <path d={`M ${-r * 0.2} ${r * 0.5} L ${r * 0.55} ${r * 0.2}`} stroke="#00000044" strokeWidth={3} strokeLinecap="round" />
  </g>
);

/* ------------------------------------------------------------------ cargo */

export const Box: React.FC<{ x: number; y: number; w?: number; tone?: 'steel' | 'orange' }> = ({
  x, y, w = 58, tone = 'steel',
}) => (
  <g transform={`translate(${x}, ${y})`}>
    <rect x={-w / 2} y={-w * 0.78} width={w} height={w * 0.78} rx={3}
      fill={tone === 'orange' ? 'url(#orangeGrad)' : 'url(#steelFlat)'} />
    <rect x={-w / 2} y={-w * 0.5} width={w} height={5} fill="#00000055" />
    <rect x={-4} y={-w * 0.78} width={8} height={w * 0.78} fill="#00000033" />
  </g>
);

/** A stack of boxes, `n` high. */
export const BoxStack: React.FC<{ x: number; n: number; w?: number }> = ({ x, n, w = 58 }) => (
  <g>
    {Array.from({ length: n }, (_, i) => (
      <Box key={i} x={x + (((i * 29) % 7) - 3)} y={-i * (w * 0.78 + 3)} w={w} />
    ))}
  </g>
);

/** Forklift, seen from the side, facing +x. The seat lands a `sitting` figure at (-16, -104). */
export const Forklift: React.FC<{ lift: number }> = ({ lift }) => (
  <g>
    <rect x={-92} y={-104} width={104} height={62} rx={8} fill="url(#orangeGrad)" />
    <rect x={-92} y={-148} width={26} height={48} rx={6} fill="url(#orangeGrad)" opacity={0.9} />
    <rect x={24} y={-206} width={11} height={206} fill="url(#steel)" />
    <rect x={48} y={-206} width={11} height={206} fill="url(#steel)" />
    <g transform={`translate(0, ${-lift})`}>
      <rect x={24} y={-24} width={38} height={12} rx={3} fill="url(#steel)" />
      <rect x={58} y={-18} width={72} height={9} rx={3} fill="url(#steel)" />
    </g>
    <circle cx={-58} cy={-26} r={26} fill="#141416" />
    <circle cx={-58} cy={-26} r={12} fill="url(#steel)" />
    <circle cx={2} cy={-20} r={20} fill="#141416" />
    <circle cx={2} cy={-20} r={9} fill="url(#steel)" />
  </g>
);

/* ---------------------------------------------------------------- dominoes */

/**
 * A row of dominoes with a travelling knock-down wave.
 *
 * The wave is a function of ((p - i/n) mod 1), so at p = 0 and p = 1 every tile
 * is in the same state — the chain reaction rolls forever without a reset.
 * `p = null` leaves the whole row standing.
 */
export const Dominoes: React.FC<{ n: number; gap: number; p: number | null; tone: 'silver' | 'orange' }> = ({
  n, gap, p, tone,
}) => (
  <g>
    {Array.from({ length: n }, (_, i) => {
      let a = 0;
      if (p !== null) {
        const local = (((p - i / n) % 1) + 1) % 1;
        // fall fast over the first 12% of the cycle, stand back up slowly after
        a = local < 0.12 ? (local / 0.12) * 78 : 78 * Math.max(0, 1 - (local - 0.12) / 0.5);
      }
      return (
        <g key={i} transform={`translate(${i * gap}, 0) rotate(${a})`}>
          <rect x={-9} y={-72} width={18} height={72} rx={3}
            fill={tone === 'orange' ? 'url(#orangeGrad)' : 'url(#steelFlat)'} />
          <circle cx={0} cy={-52} r={4} fill="#00000055" />
          <circle cx={0} cy={-24} r={4} fill="#00000055" />
        </g>
      );
    })}
  </g>
);

/* ------------------------------------------------------------------- rings */

/** Concentric zone rings, drawn in full-frame coords around (cx, cy). */
export const ZoneRings: React.FC<{ cx: number; cy: number; radii: number[]; glow: number }> = ({
  cx, cy, radii, glow,
}) => (
  <g>
    {radii.map((r, i) => (
      <circle
        key={r}
        cx={cx} cy={cy} r={r}
        fill="none"
        stroke={i === 0 ? '#E0524A' : ORANGE.base}
        strokeWidth={i === 0 ? 5 : 3}
        opacity={i === 0 ? 0.55 + 0.3 * glow : 0.5 + 0.1 * i}
      />
    ))}
  </g>
);

/** The arrow that travels out through the rings. */
export const ZoneArrow: React.FC<{ cx: number; cy: number; r: number; angle: number; opacity: number }> = ({
  cx, cy, r, angle, opacity,
}) => (
  // Travels along a diagonal so it never crosses the zone labels, which are
  // stacked up the vertical centre line.
  <g transform={`translate(${cx}, ${cy}) rotate(${angle}) translate(0, ${-r})`} opacity={opacity}>
    <rect x={-6} y={0} width={12} height={54} rx={6} fill="url(#orangeGrad)" />
    <path d="M -21 4 L 0 -28 L 21 4 Z" fill="url(#orangeGrad)" />
  </g>
);

/* --------------------------------------------------------------- hourglass */

/** Hourglass. `top` is 0..1 of sand still in the upper bulb. */
export const Hourglass: React.FC<{ top: number; p: number; tone: 'silver' | 'orange' }> = ({ top, p, tone }) => {
  const sand = tone === 'orange' ? ORANGE.base : '#C7C7CC';
  const glass = 'url(#steelFlat)';
  return (
    <g>
      <rect x={-52} y={-212} width={104} height={12} rx={5} fill={glass} />
      <rect x={-52} y={-12} width={104} height={12} rx={5} fill={glass} />
      <path d="M -42 -200 L 42 -200 L 6 -106 L 42 -12 L -42 -12 L -6 -106 Z" fill="#17171B" opacity={0.6} />
      <path d="M -42 -200 L 42 -200 L 6 -106 L 42 -12 L -42 -12 L -6 -106 Z"
        fill="none" stroke={glass} strokeWidth={5} strokeLinejoin="round" />
      {/* upper sand: a wedge whose height tracks `top` */}
      <path
        d={`M ${-42 + 36 * (1 - top)} ${-200 + 94 * (1 - top)} L ${42 - 36 * (1 - top)} ${-200 + 94 * (1 - top)} L 4 -108 L -4 -108 Z`}
        fill={sand} opacity={0.9}
      />
      {/* lower pile: the complement */}
      <path
        d={`M ${-42 + 30 * top} -12 L ${42 - 30 * top} -12 L ${18 - 12 * top} ${-12 - 62 * (1 - top)} L ${-18 + 12 * top} ${-12 - 62 * (1 - top)} Z`}
        fill={sand} opacity={0.9}
      />
      {/* the trickle */}
      {[0, 1, 2].map((i) => {
        const u = (p * 3 + i / 3) % 1;
        return <rect key={i} x={-2} y={-104 + u * 78} width={4} height={12} rx={2} fill={sand} opacity={0.85} />;
      })}
    </g>
  );
};
