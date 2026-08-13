import React from 'react';
import { StickFigure } from '../Figure';
import { SplitStage, useLoop, saw } from '../Stage';
import { standing, flying } from '../poses';

/**
 * หยุดเรียน vs เรียนต่อ — the series closer, and the only clip with a CTA.
 *
 * ONE climb per loop, fading in low and out high. An earlier version overlapped
 * two copies to hide the seam, but two half-opaque figures just read as two
 * people; a brief empty beat is the cleaner lie.
 */
const Kosin: React.FC<{ p: number }> = ({ p }) => {
  const { joints, rotate } = flying(p);
  const rise = p * 380;
  // Fully visible in the middle of the climb, gone at both ends.
  const o = Math.min(1, Math.min(p, 1 - p) / 0.16);
  return (
    <g opacity={o} transform={`translate(${-140 + rise * 0.5}, ${-rise})`}>
      <StickFigure joints={joints} tone="orange" rotate={rotate} />
    </g>
  );
};

export const CloserClip: React.FC = () => {
  const u = useLoop();
  const left = standing(saw(u, 1));
  const p = saw(u, 1);

  return (
    <SplitStage
      goal="ทางแยกอยู่ตรงนี้"
      cta="yourbrand.com"
      left={{
        label: 'หยุดเรียน',
        children: (
          <g transform="translate(0, 0)">
            <StickFigure joints={left.joints} tone="silver" />
          </g>
        ),
      }}
      right={{
        label: 'เรียนต่อ',
        children: (
          <g>
            <Kosin p={p} />
          </g>
        ),
      }}
    />
  );
};
