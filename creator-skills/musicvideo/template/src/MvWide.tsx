import React from 'react';
import { AbsoluteFill, useCurrentFrame } from 'remotion';
import { Backdrop } from './components/Backdrop';
import { Analyser } from './components/Analyser';
import { Finish } from './components/Finish';
import { Fonts } from './components/Fonts';
import { Subtitles } from './components/Subtitles';
import { OpeningCard, Lockup, ClosingCard } from './components/Titles';
import { WIDE, INK } from './theme';

const { W, H } = WIDE;
const ANALYSER_H = 170;

/**
 * The 16:9 cut, for YouTube.
 *
 * There is no speaker rig in this one, unlike the video this project was
 * forked from. The backdrops here are illustrations that already contain
 * guitars, amps and drum kits; a drawn cone floating over them read as a
 * bullseye sticker pasted onto someone else's picture, and over the neon-alley
 * still it competed with the neon rings the artwork already had. The frame is
 * carried by the illustration, the lyric and the analyser.
 */
export const MvWide: React.FC = () => {
  const frame = useCurrentFrame();

  return (
    <AbsoluteFill style={{ backgroundColor: INK }}>
      <Backdrop frame={frame} W={W} H={H} />

      {/* Ground the analyser without burying the art. Shallower and lighter
          than the photographic version: these stills are bright, and the heavy
          gradient that settled night photography just looks like a smudge. */}
      <div
        style={{
          position: 'absolute', left: 0, right: 0, bottom: 0, height: 250,
          background:
            'linear-gradient(180deg, transparent, rgba(20,11,34,0.34) 55%, rgba(20,11,34,0.74))',
        }}
      />

      <div style={{ position: 'absolute', left: 0, bottom: 26 }}>
        <Analyser frame={frame} W={W} height={ANALYSER_H} />
      </div>

      <Subtitles frame={frame} W={W} bottom={ANALYSER_H + 72} />
      <Lockup frame={frame} wide W={W} H={H} />
      <OpeningCard frame={frame} W={W} wide />
      <ClosingCard frame={frame} W={W} wide />
      <Fonts />
      <Finish frame={frame} W={W} H={H} />
    </AbsoluteFill>
  );
};
