import React from 'react';
import { StickFigure } from '../Figure';
import { TwoLaneStage, useLoop, saw } from '../Stage';
import { pushing, walking } from '../poses';
import { Route, routeAt, Boulder } from '../props/scene';

/**
 * สบายตอนนี้ เหนื่อยยาว vs เหนื่อยตอนนี้ สบายยาว.
 *
 * This is the one clip in the series that is top/bottom rather than left/right:
 * a route only reads left-to-right, so two routes have to stack. Same shape as
 * the reference page's 10M and 4.2M clips.
 *
 * The traveller crosses the route once per loop, which would jump at the seam,
 * so both lanes fade in and out over the first and last 8% together — the fade
 * reads as a deliberate wipe rather than a glitch.
 */

/** Gentle dip, then a climb that never ends. */
const easyFirst = (t: number) => (t < 0.32 ? 62 - 46 * (t / 0.32) : 16 + 330 * Math.pow((t - 0.32) / 0.68, 1.7));
/** One hard climb, then downhill the rest of the way. */
const hardFirst = (t: number) => (t < 0.3 ? 40 + 300 * Math.pow(t / 0.3, 1.35) : 340 - 292 * Math.pow((t - 0.3) / 0.7, 0.85));

const edgeFade = (u: number) => Math.min(1, Math.min(u, 1 - u) / 0.08);

const Traveller: React.FC<{
  shape: (t: number) => number;
  t: number;
  tone: 'silver' | 'orange';
  pose: { joints: React.ComponentProps<typeof StickFigure>['joints'] };
  spin: number;
}> = ({ shape, t, tone, pose, spin }) => {
  const at = routeAt(shape, t);
  return (
    <g transform={`translate(${at.x}, ${at.y}) rotate(${-at.angle})`}>
      <g transform="translate(58, -46)">
        <Boulder r={46} tone={tone} spin={spin} />
      </g>
      <g transform="translate(-62, 0) scale(0.95)">
        <StickFigure joints={pose.joints} tone={tone} />
      </g>
    </g>
  );
};

export const HillClip: React.FC = () => {
  const u = useLoop();
  const o = edgeFade(u);
  const step = saw(u, 8);

  return (
    <TwoLaneStage
      goal="เวลาเท่ากัน"
      top={{
        label: 'สบายตอนนี้ เหนื่อยยาว',
        children: (
          <g opacity={o}>
            <Route shape={easyFirst} tone="silver" />
            <Traveller shape={easyFirst} t={u} tone="silver" pose={pushing(step)} spin={u * 900} />
          </g>
        ),
      }}
      bottom={{
        label: 'เหนื่อยตอนนี้ สบายยาว',
        children: (
          <g opacity={o}>
            <Route shape={hardFirst} tone="orange" />
            <Traveller shape={hardFirst} t={u} tone="orange" pose={u < 0.3 ? pushing(step) : walking(step)} spin={u * 900} />
          </g>
        ),
      }}
    />
  );
};
