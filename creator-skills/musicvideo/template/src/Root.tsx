import React from 'react';
import { Composition } from 'remotion';
import { MvWide } from './MvWide';
import { MvTall } from './MvTall';
import { WIDE, TALL, FPS, TOTAL_FRAMES } from './theme';

/**
 * Two cuts of the same song, same data, same components.
 *
 * Audio is not mounted here on purpose: the render goes out silent in chunks
 * and the mastered track is muxed on afterwards. Decoding a 5-minute WAV in
 * every one of the nine chunk browsers costs minutes and buys nothing, since
 * nothing in the picture reads the audio element -- it reads features.json.
 */
export const RemotionRoot: React.FC = () => (
  <>
    <Composition
      id="MvWide"
      component={MvWide}
      durationInFrames={TOTAL_FRAMES}
      fps={FPS}
      width={WIDE.W}
      height={WIDE.H}
    />
    <Composition
      id="MvTall"
      component={MvTall}
      durationInFrames={TOTAL_FRAMES}
      fps={FPS}
      width={TALL.W}
      height={TALL.H}
    />
  </>
);
