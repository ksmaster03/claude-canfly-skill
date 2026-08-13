import React from 'react';
import { StickFigure } from '../Figure';
import { SplitStage, useLoop, saw } from '../Stage';
import { scooping, celebrate } from '../poses';
import { Hourglass, BoxStack } from '../props/scene';

/**
 * หมดวัน งานยังอยู่ vs งานหมด วันยังเหลือ.
 *
 * Both hourglasses are held at a FIXED level rather than draining over the clip —
 * a level that empties has to jump back at the loop point. Only the trickle
 * moves, and it is periodic, so the shot is a steady state the eye can compare.
 */
export const HourglassClip: React.FC = () => {
  const u = useLoop();
  const left = scooping(saw(u, 4));
  const right = celebrate(saw(u, 1));

  return (
    <SplitStage
      goal="วันเดียวกัน"
      left={{
        label: 'หมดวัน งานยังอยู่',
        children: (
          <g>
            <g transform="translate(146, 0) scale(0.82)">
              <Hourglass top={0.07} p={u} tone="silver" />
            </g>
            <BoxStack x={38} n={5} w={48} />
            <g transform="translate(-118, 0)">
              <StickFigure joints={left.joints} tone="silver" />
            </g>
          </g>
        ),
      }}
      right={{
        label: 'งานหมด วันยังเหลือ',
        children: (
          <g>
            <g transform="translate(146, 0) scale(0.82)">
              <Hourglass top={0.64} p={u} tone="orange" />
            </g>
            <g transform="translate(-70, 0)">
              <StickFigure joints={right.joints} tone="orange" />
            </g>
          </g>
        ),
      }}
    />
  );
};
