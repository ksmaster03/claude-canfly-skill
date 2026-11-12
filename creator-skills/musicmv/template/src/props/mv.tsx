import React from 'react';
import { BRAND_GREEN, ORANGE, RED, SILVER, STEEL, STEEL_DARK } from '../theme';

/**
 * Prop kit for the music video's scenes.
 *
 * Local coords match the rest of the project: ground at y = 0, subject centred
 * on x = 0, figure faces +x. Everything takes an explicit phase or progress
 * value rather than reading the frame itself, so a prop can be driven off the
 * bar grid in one scene and off a one-shot progress ramp in the next.
 *
 * No Math.random anywhere — any scatter is derived from the item index, or the
 * shape would reshuffle on every single frame.
 */

/** Deterministic jitter in [-half, half] from an index. */
const jit = (i: number, half: number, salt = 37) => (((i * salt) % (half * 2 + 1)) - half);

export type Paint = 'steel' | 'orange' | 'red' | 'green';

const FILL: Record<Paint, string> = {
  steel: 'url(#steelFlat)',
  orange: 'url(#orangeGrad)',
  red: 'url(#redGrad)',
  green: 'url(#greenGrad)',
};

/* -------------------------------------------------------------- base card */

/** The atom every document, file and code block is built from. */
export const Slab: React.FC<{
  x?: number; y?: number; w?: number; h?: number; paint?: Paint; opacity?: number; rot?: number;
}> = ({ x = 0, y = 0, w = 62, h = 44, paint = 'steel', opacity = 1, rot = 0 }) => (
  <g transform={`translate(${x}, ${y}) rotate(${rot})`} opacity={opacity}>
    <rect x={-w / 2} y={-h} width={w} height={h} rx={5} fill={FILL[paint]} />
    <rect x={-w / 2} y={-h} width={w} height={4} rx={2} fill="#FFFFFF18" />
  </g>
);

/** A card with code-ish rules across it — reads as "a file with code in it". */
export const CodeCard: React.FC<{
  x?: number; y?: number; w?: number; h?: number; paint?: Paint; lines?: number; lit?: number;
}> = ({ x = 0, y = 0, w = 108, h = 132, paint = 'steel', lines = 5, lit = -1 }) => (
  <g transform={`translate(${x}, ${y})`}>
    <rect x={-w / 2} y={-h} width={w} height={h} rx={7} fill={FILL[paint]} opacity={0.95} />
    {Array.from({ length: lines }, (_, i) => {
      const lw = w * (0.42 + ((i * 23) % 5) * 0.1);
      const on = i === lit;
      return (
        <rect
          key={i}
          x={-w / 2 + 12}
          y={-h + 18 + i * ((h - 26) / lines)}
          width={lw}
          height={6}
          rx={3}
          fill={on ? ORANGE.light : '#0D0D0F'}
          opacity={on ? 0.95 : 0.5}
        />
      );
    })}
  </g>
);

/* ------------------------------------------------------------------ heaps */

/**
 * A heap of slabs piled up against the figure — the "work you are buried under"
 * shape. `n` slabs stack in a rough pyramid; `paint` is red for bugs.
 */
export const Heap: React.FC<{ n: number; paint?: Paint; w?: number; x?: number; wobble?: number }> = ({
  n, paint = 'steel', w = 56, x = 0, wobble = 0,
}) => {
  const perRow = 3;
  return (
    <g transform={`translate(${x}, 0)`}>
      {Array.from({ length: n }, (_, i) => {
        const row = Math.floor(i / perRow);
        const col = i % perRow;
        const rowCount = Math.min(perRow, n - row * perRow);
        const spread = (col - (rowCount - 1) / 2) * (w + 6);
        return (
          <Slab
            key={i}
            x={spread + jit(i, 4)}
            y={-row * (w * 0.62)}
            w={w}
            h={w * 0.62}
            paint={paint}
            rot={jit(i, 3, 53) + wobble * Math.sin(i * 1.7)}
          />
        );
      })}
    </g>
  );
};

/** A stack of paper — `n` sheets, seen edge-on. Shrinks as `n` drops. */
export const PageStack: React.FC<{ n: number; x?: number; w?: number; paint?: Paint }> = ({
  n, x = 0, w = 96, paint = 'steel',
}) => (
  <g transform={`translate(${x}, 0)`}>
    {Array.from({ length: Math.max(0, Math.round(n)) }, (_, i) => (
      <rect
        key={i}
        x={-w / 2 + jit(i, 3)}
        y={-(i + 1) * 7}
        width={w}
        height={7}
        rx={2}
        fill={FILL[paint]}
        opacity={0.92}
      />
    ))}
  </g>
);

/* ------------------------------------------------------------- file grid */

/**
 * A grid of files with a scan sweep running through it.
 *
 * `sweep` is 0..1 across the grid; cards within a short distance of the sweep
 * line light up, and everything the sweep has already passed stays lit — which
 * is what makes "it read all of them" legible in a couple of seconds.
 */
export const FileGrid: React.FC<{
  cols: number; rows: number; sweep: number; cell?: number; y?: number;
}> = ({ cols, rows, sweep, cell = 34, y = 0 }) => {
  const gw = cols * cell;
  return (
    <g transform={`translate(${-gw / 2 + cell / 2}, ${y})`}>
      {Array.from({ length: cols * rows }, (_, i) => {
        const cx = (i % cols) * cell;
        const cy = -Math.floor(i / cols) * cell;
        const t = (i % cols) / Math.max(1, cols - 1);
        const d = sweep - t;
        const lit = d >= 0;
        const hot = lit && d < 0.12;
        return (
          <rect
            key={i}
            x={cx - cell * 0.38}
            y={cy - cell * 0.46}
            width={cell * 0.76}
            height={cell * 0.92}
            rx={3}
            fill={hot ? ORANGE.light : lit ? ORANGE.deep : '#3A3A3E'}
            opacity={hot ? 1 : lit ? 0.85 : 0.7}
          />
        );
      })}
    </g>
  );
};

/* ----------------------------------------------------------------- charts */

/** Bar chart. `heights` are 0..1 of `max`; `grow` scales them all in. */
export const Bars: React.FC<{ heights: number[]; max?: number; bw?: number; gap?: number; grow?: number }> = ({
  heights, max = 200, bw = 26, gap = 12, grow = 1,
}) => {
  const total = heights.length * bw + (heights.length - 1) * gap;
  return (
    <g transform={`translate(${-total / 2 + bw / 2}, 0)`}>
      <line x1={-bw} y1={0} x2={total} y2={0} stroke={STEEL_DARK} strokeWidth={3} />
      {heights.map((h, i) => (
        <rect
          key={i}
          x={i * (bw + gap) - bw / 2}
          y={-h * max * grow}
          width={bw}
          height={h * max * grow}
          rx={3}
          fill="url(#orangeGrad)"
        />
      ))}
    </g>
  );
};

/** A row of test results flipping from red to green as `done` advances 0..1. */
export const TestDots: React.FC<{ n: number; done: number; y?: number; r?: number; gap?: number }> = ({
  n, done, y = -140, r = 11, gap = 34,
}) => (
  <g transform={`translate(${(-(n - 1) * gap) / 2}, ${y})`}>
    {Array.from({ length: n }, (_, i) => {
      const pass = i / n < done;
      return (
        <circle
          key={i}
          cx={i * gap}
          cy={0}
          r={r}
          fill={pass ? BRAND_GREEN : RED}
          opacity={pass ? 0.95 : 0.9}
        />
      );
    })}
  </g>
);

/* ------------------------------------------------------------ connections */

/** A labelled steel chip — one external system the assistant is wired into. */
export const Chip: React.FC<{ x: number; y: number; text: string; lit?: number; w?: number }> = ({
  x, y, text, lit = 0, w = 132,
}) => (
  <g transform={`translate(${x}, ${y})`}>
    <rect x={-w / 2} y={-24} width={w} height={48} rx={10} fill="url(#steelFlat)" />
    <rect
      x={-w / 2} y={-24} width={w} height={48} rx={10}
      fill="none" stroke={ORANGE.base} strokeWidth={3} opacity={lit}
    />
    <text
      x={0} y={7} textAnchor="middle"
      fontFamily="'Sarabun', sans-serif" fontSize={22} fontWeight={600}
      fill={lit > 0.4 ? '#FFE9D2' : '#1A1A1C'}
    >
      {text}
    </text>
  </g>
);

/**
 * A line of energy from `a` to `b` with a packet travelling along it.
 * `p` is the packet's 0..1 position; `on` fades the whole link in and out.
 */
export const Beam: React.FC<{
  ax: number; ay: number; bx: number; by: number; p: number; on?: number; tone?: string;
}> = ({ ax, ay, bx, by, p, on = 1, tone = ORANGE.base }) => {
  const px = ax + (bx - ax) * p;
  const py = ay + (by - ay) * p;
  return (
    <g opacity={on}>
      <line x1={ax} y1={ay} x2={bx} y2={by} stroke={tone} strokeWidth={3} opacity={0.35} strokeLinecap="round" />
      <circle cx={px} cy={py} r={7} fill={ORANGE.light} opacity={0.95} />
    </g>
  );
};

/* --------------------------------------------------------------- devices */

/** A screen on a stand — used when the output is a page someone can look at. */
export const Screen: React.FC<{ x?: number; y?: number; w?: number; h?: number; fill?: number }> = ({
  x = 0, y = 0, w = 190, h = 130, fill = 1,
}) => (
  <g transform={`translate(${x}, ${y})`}>
    <rect x={-10} y={-46} width={20} height={46} fill="url(#steel)" />
    <rect x={-52} y={-8} width={104} height={10} rx={5} fill="url(#steelFlat)" />
    <rect x={-w / 2} y={-46 - h} width={w} height={h} rx={9} fill="#17171B" stroke={STEEL} strokeWidth={4} />
    <g opacity={fill}>
      <rect x={-w / 2 + 14} y={-46 - h + 18} width={w * 0.52} height={9} rx={4} fill={ORANGE.light} />
      <rect x={-w / 2 + 14} y={-46 - h + 38} width={w * 0.74} height={7} rx={3} fill="#6A6A70" />
      <rect x={-w / 2 + 14} y={-46 - h + 54} width={w * 0.64} height={7} rx={3} fill="#6A6A70" />
      <rect x={-w / 2 + 14} y={-46 - h + 76} width={w * 0.34} height={20} rx={6} fill={ORANGE.base} />
    </g>
  </g>
);

/** A plug sliding into a socket — a skill being fitted to the assistant. */
export const Plug: React.FC<{ x?: number; y?: number; insert?: number }> = ({ x = 0, y = 0, insert = 0 }) => (
  <g transform={`translate(${x}, ${y})`}>
    <rect x={0} y={-34} width={44} height={68} rx={8} fill="url(#steelFlat)" />
    <rect x={-6} y={-20} width={10} height={14} rx={3} fill="#0D0D0F" />
    <rect x={-6} y={8} width={10} height={14} rx={3} fill="#0D0D0F" />
    <g transform={`translate(${-92 + insert * 84}, 0)`}>
      <rect x={-52} y={-30} width={56} height={60} rx={8} fill="url(#orangeGrad)" />
      <rect x={0} y={-19} width={16} height={9} rx={3} fill={ORANGE.light} />
      <rect x={0} y={9} width={16} height={9} rx={3} fill={ORANGE.light} />
    </g>
  </g>
);

/** A magnifier — looking something up rather than guessing at it. */
export const Magnifier: React.FC<{ x?: number; y?: number; r?: number; tilt?: number }> = ({
  x = 0, y = 0, r = 34, tilt = -20,
}) => (
  <g transform={`translate(${x}, ${y}) rotate(${tilt})`}>
    <circle r={r} fill="none" stroke="url(#steel)" strokeWidth={9} />
    <circle r={r} fill={ORANGE.base} opacity={0.14} />
    <rect x={-7} y={r} width={14} height={r * 0.95} rx={7} fill="url(#steel)" />
  </g>
);

/** A clock face, for anything that is about elapsed time. */
export const Clock: React.FC<{ x?: number; y?: number; r?: number; p?: number }> = ({
  x = 0, y = 0, r = 44, p = 0,
}) => (
  <g transform={`translate(${x}, ${y})`}>
    <circle r={r} fill="#17171B" stroke="url(#steel)" strokeWidth={7} />
    <line x1={0} y1={0} x2={0} y2={-r * 0.62} stroke={SILVER.light} strokeWidth={5} strokeLinecap="round"
      transform={`rotate(${p * 360})`} />
    <line x1={0} y1={0} x2={0} y2={-r * 0.42} stroke={ORANGE.base} strokeWidth={6} strokeLinecap="round"
      transform={`rotate(${p * 30})`} />
    <circle r={4} fill={ORANGE.light} />
  </g>
);

/** A camera, for the "photograph the whiteboard and it still reads it" beat. */
export const Camera: React.FC<{ x?: number; y?: number; flash?: number }> = ({ x = 0, y = 0, flash = 0 }) => (
  <g transform={`translate(${x}, ${y})`}>
    <rect x={-46} y={-34} width={92} height={62} rx={9} fill="url(#steelFlat)" />
    <rect x={-16} y={-44} width={34} height={12} rx={4} fill="url(#steel)" />
    <circle cx={4} cy={-3} r={20} fill="#0D0D0F" stroke={STEEL} strokeWidth={4} />
    <circle cx={4} cy={-3} r={9} fill={ORANGE.deep} opacity={0.8} />
    <circle cx={-30} cy={-20} r={6} fill={ORANGE.light} opacity={flash} />
  </g>
);

/** A tilted, blurred-looking photo of a chart — what a phone snap actually is. */
export const PhotoChart: React.FC<{ x?: number; y?: number; tilt?: number; scale?: number }> = ({
  x = 0, y = 0, tilt = -8, scale = 1,
}) => (
  <g transform={`translate(${x}, ${y}) rotate(${tilt}) scale(${scale})`}>
    <rect x={-70} y={-100} width={140} height={100} rx={6} fill="#1E1E22" stroke={STEEL_DARK} strokeWidth={4} />
    {[0.35, 0.6, 0.45, 0.85, 0.7].map((h, i) => (
      <rect key={i} x={-56 + i * 24} y={-14 - h * 70} width={16} height={h * 70} rx={2} fill={SILVER.deep} />
    ))}
  </g>
);
