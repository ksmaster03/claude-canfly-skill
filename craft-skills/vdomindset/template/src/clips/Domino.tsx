import React from 'react';
import { StickFigure } from '../Figure';
import { SplitStage, useLoop, saw } from '../Stage';
import { placing, pointing } from '../poses';
import { Dominoes } from '../props/scene';

/**
 * ทำทีละงาน vs วางระบบแล้วปล่อย.
 *
 * The right side is a TRAVELLING wave, not a one-shot topple: each tile's angle
 * is a function of ((p - i/n) mod 1), so the chain rolls forever and the clip
 * loops with no reset to hide.
 */
export const DominoClip: React.FC = () => {
  const u = useLoop();
  const left = placing(saw(u, 4));
  const right = pointing(saw(u, 1));

  return (
    <SplitStage
      goal="แรงเท่ากัน"
      left={{
        label: 'ทำทีละงาน',
        children: (
          <g>
            <g transform="translate(30, 0)">
              <Dominoes n={5} gap={34} p={null} tone="silver" />
            </g>
            <g transform="translate(-88, 0)">
              <StickFigure joints={left.joints} tone="silver" />
            </g>
          </g>
        ),
      }}
      right={{
        label: 'วางระบบแล้วปล่อย',
        children: (
          <g>
            <g transform="translate(4, 0)">
              <Dominoes n={12} gap={30} p={saw(u, 2)} tone="orange" />
            </g>
            <g transform="translate(-108, 0)">
              <StickFigure joints={right.joints} tone="orange" />
            </g>
          </g>
        ),
      }}
    />
  );
};
