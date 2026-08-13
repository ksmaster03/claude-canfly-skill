import React from 'react';
import { StickFigure } from '../Figure';
import { SplitStage, useLoop, saw, wave } from '../Stage';
import { rowing, sitting } from '../poses';
import { WaterBand, Hull, Oar, Wake } from '../props/scene';

/** Waterline, high enough inside the stage box that some water body shows below it. */
const WL = -54;

/**
 * พายเรือ vs ติดเครื่องยนต์ — same water, same time, different distance.
 *
 * Distance can't be shown directly in a left/right split without one boat
 * leaving its half, so speed is carried by the WAKE: a churn on the left, a long
 * planing wake with spray on the right.
 */
export const BoatClip: React.FC = () => {
  const u = useLoop();
  const stroke = saw(u, 3); // three oar strokes, one per bar
  const left = rowing(stroke);
  const right = sitting(saw(u, 1));

  return (
    <SplitStage
      goal="เวลาเท่ากัน"
      horizon={false}
      back={<WaterBand y={WL} p={u} />}
      left={{
        label: 'พายเอง',
        children: (
          <g>
            <Wake x={-96} y={WL} len={130} p={u} />
            <g transform={`translate(-6, ${WL + 18}) scale(0.85)`}>
              <StickFigure joints={left.joints} tone="silver" />
            </g>
            <g transform={`translate(0, ${WL})`}>
              <Hull tone="silver" />
            </g>
            <Oar x={30} angle={-66 + 46 * Math.sin(stroke * Math.PI * 2)} />
          </g>
        ),
      }}
      right={{
        label: 'ติดเครื่องยนต์',
        children: (
          <g>
            <Wake x={-104} y={WL} len={280} p={u} strong />
            <g transform={`translate(-6, ${WL + 18 + 2 * wave(u, 4)}) scale(0.85)`}>
              <StickFigure joints={right.joints} tone="orange" />
            </g>
            <g transform={`translate(0, ${WL + 2 * wave(u, 4)}) rotate(-5)`}>
              <Hull tone="orange" motor />
            </g>
          </g>
        ),
      }}
    />
  );
};
