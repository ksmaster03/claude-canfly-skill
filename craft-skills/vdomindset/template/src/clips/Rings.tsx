import React from 'react';
import { FullStage, useLoop } from '../Stage';
import { W, ORANGE, SILVER } from '../theme';
import { THAI } from '../fonts';
import { ZoneRings, ZoneArrow } from '../props/scene';

/**
 * เขตปลอดภัย → กลัว AI → เริ่มลอง → ใช้จริง.
 *
 * A pure diagram — no rig at all, which makes it the cheapest clip in the series
 * to produce and, on the reference page, the shape that did 4.5M views.
 *
 * The arrow travels outward once per loop. Rather than snap back to the centre it
 * fades out at the rim and fades in again at the core, so the seam disappears.
 */

const CX = W / 2;
const CY = 1010;
const RADII = [160, 262, 364, 466];
const ZONES = ['เขตปลอดภัย', 'กลัว AI', 'เริ่มลอง', 'ใช้จริง'];

export const RingsClip: React.FC = () => {
  const u = useLoop();
  const r = 120 + u * 380;
  const fade = Math.min(1, Math.min(u, 1 - u) / 0.12);

  return (
    <FullStage goal="งานที่ AI แทนไม่ได้">
      <ZoneRings cx={CX} cy={CY} radii={RADII} glow={(1 - Math.cos(u * Math.PI * 4)) / 2} />

      {ZONES.map((z, i) => (
        <text
          key={z}
          x={CX}
          y={CY - RADII[i] + 42}
          textAnchor="middle"
          fontFamily={THAI}
          fontWeight={i === 0 ? 400 : 600}
          fontSize={i === 0 ? 30 : 32}
          fill={i === 0 ? SILVER.text : ORANGE.text}
          opacity={i === 0 ? 0.8 : 0.55 + i * 0.15}
        >
          {z}
        </text>
      ))}

      <ZoneArrow cx={CX} cy={CY} r={r} angle={46} opacity={fade} />
    </FullStage>
  );
};
