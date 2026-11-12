import React from 'react';
import { Composition } from 'remotion';
import { W, H, FPS, SEC_F, SONG_S } from './theme';
import { Mv } from './Mv';

/**
 * One composition: the whole video, 1080x1920 at 30fps.
 *
 * Length is the full rendered take (224.6s) rather than the last sung word at
 * 219.7s, so the instrumental tail plays out instead of being clipped mid-bar.
 */
export const RemotionRoot: React.FC = () => (
  <Composition
    id="Mv"
    component={Mv}
    durationInFrames={SEC_F(SONG_S)}
    fps={FPS}
    width={W}
    height={H}
  />
);
