import React from 'react';
import { Composition } from 'remotion';
import { Reel } from './Reel';
import tl from './timeline.json';

export const RemotionRoot: React.FC = () => (
  <Composition
    id="Reel"
    component={Reel}
    durationInFrames={Math.round((tl.totalDur + (tl as any).outro) * 30)}
    fps={30}
    width={720}
    height={1280}
  />
);
