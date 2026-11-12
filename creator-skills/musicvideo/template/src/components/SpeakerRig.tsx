import React from 'react';
import { envelope } from '../features';
import { AMBER, CYAN, INK, PAPER } from '../theme';

/**
 * A cabinet, drawn the way the backdrops are drawn.
 *
 * The previous video's driver was built from radial gradients to sit against
 * photographs of real rigs. Dropped on top of flat cartoon art it reads as a
 * render pasted onto an illustration -- the gradients and the bold outlines
 * belong to different pictures. This one is flat fills and a heavy outline, so
 * it looks like it came out of the same pen.
 *
 * What carries over is the mechanic: the cone travels on the track's own
 * sub-band envelope, and the excursion stays small. A real driver moves a few
 * percent of its width; more than that stops reading as a speaker and starts
 * reading as a pulsing circle, which is what every stock visualiser does.
 */
export const Driver: React.FC<{
  frame: number;
  size: number;
  /** Phase offset in frames -- two cabinets dead in sync look like one mirrored. */
  offset?: number;
  tint?: 'amber' | 'cyan';
}> = ({ frame, size, offset = 0, tint = 'amber' }) => {
  const e = envelope(frame + offset, 'sub');
  const b = envelope(frame + offset, 'bass');
  const C = tint === 'amber' ? AMBER : CYAN;

  const travel = e * 0.05;
  const stroke = Math.max(3, size * 0.022);
  const r = size / 2;

  return (
    <svg width={size} height={size} viewBox="0 0 100 100" style={{ overflow: 'visible' }}>
      {/* glow, sized off the bass so the whole cabinet blooms on a hit */}
      <circle cx="50" cy="50" r={48} fill={C.glow} opacity={0.25 + b * 0.45}
              style={{ filter: `blur(${2 + b * 5}px)` }} />
      {/* basket */}
      <circle cx="50" cy="50" r={46} fill={INK} stroke={PAPER} strokeWidth={stroke / 2} />
      <circle cx="50" cy="50" r={40} fill="none" stroke={C.deep} strokeWidth={stroke / 2.4} />
      {/* surround: squashes as the cone comes forward */}
      <circle cx="50" cy="50" r={34 - e * 1.2} fill={C.deep} stroke={INK} strokeWidth={stroke / 3} />
      {/* cone */}
      <circle cx="50" cy="50" r={(26 + travel * 26)} fill={C.base}
              stroke={INK} strokeWidth={stroke / 2.6} />
      {/* dust cap, catching the key light */}
      <circle cx="50" cy="50" r={(11 + travel * 20)} fill={C.light}
              stroke={INK} strokeWidth={stroke / 3} />
      {/* highlight, offset up-left like every cartoon sphere */}
      <ellipse cx={44} cy={41} rx={9} ry={6} fill={PAPER} opacity={0.35 + e * 0.25}
               transform="rotate(-25 44 41)" />
      {/* mounting bolts */}
      {[0, 90, 180, 270].map((a) => (
        <circle key={a}
                cx={50 + 43 * Math.cos((a * Math.PI) / 180)}
                cy={50 + 43 * Math.sin((a * Math.PI) / 180)}
                r={2.4} fill={PAPER} opacity={0.75} />
      ))}
    </svg>
  );
};
