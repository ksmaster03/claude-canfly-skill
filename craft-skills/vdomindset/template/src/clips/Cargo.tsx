import React from 'react';
import { StickFigure } from '../Figure';
import { SplitStage, useLoop, saw, wave } from '../Stage';
import { carrying, sitting } from '../poses';
import { Box, BoxStack, Forklift } from '../props/scene';

/**
 * แบกทีละใบ vs ยกทีละชั้น — the same pile of work, moved two ways.
 *
 * Both sides show an identical stack so the comparison is about throughput, not
 * about one person having less to do.
 */
export const CargoClip: React.FC = () => {
  const u = useLoop();
  const stride = saw(u, 3);
  const left = carrying(stride);
  const right = sitting(saw(u, 1));
  const lift = 116 + 26 * wave(u, 2);

  return (
    <SplitStage
      goal="กองงานเท่ากัน"
      left={{
        label: 'แบกทีละใบ',
        children: (
          <g>
            <BoxStack x={168} n={6} />
            <g transform={`translate(${-70 + 26 * Math.sin(stride * Math.PI * 2)}, 0)`}>
              <StickFigure joints={left.joints} tone="silver" />
              <Box x={74} y={-118} w={54} />
            </g>
          </g>
        ),
      }}
      right={{
        label: 'ยกทีละชั้น',
        children: (
          <g>
            <BoxStack x={186} n={6} />
            <g transform="translate(-58, 0)">
              <Forklift lift={lift} />
              <g transform={`translate(${94}, ${-lift - 9})`}>
                <Box x={0} y={0} w={54} tone="orange" />
                <Box x={58} y={0} w={54} tone="orange" />
                <Box x={29} y={-46} w={54} tone="orange" />
              </g>
              <g transform="translate(-54, -104) scale(0.74)">
                <StickFigure joints={right.joints} tone="orange" />
              </g>
            </g>
          </g>
        ),
      }}
    />
  );
};
