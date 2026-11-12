import React from 'react';
import { AbsoluteFill, useCurrentFrame } from 'remotion';
import { LYRIC_Y, SONG_S, W, snapBar, snapHalf } from './theme';
import { THAI } from './fonts';
import { barsAt, frameToSec, lineAt } from './song';
import { ExampleSoloScene, ExampleSplitScene, SceneProps } from './scenes';

/**
 * The video's running order.
 *
 * Times come from the section and line starts in timeline.json — the aligner's
 * own view of the take that was rendered — and are then snapped to the grid.
 * Snapping matters more than hitting the vocal exactly: a cut that lands a
 * sixteenth off the grid reads as sloppy even to someone who cannot say why,
 * while a cut on the downbeat just before a line reads as intentional.
 *
 * Two rules learned the hard way:
 *  - Do NOT divide a section into equal parts. Take each scene's start from the
 *    line it illustrates. A rap that delivers 16 lines over 32 bars will leave
 *    an evenly-split schedule two scenes behind the vocal by the end.
 *  - Mark densely sung scenes `half: true` so they snap to beat 1 or beat 3.
 */
const SCHEDULE: Array<{ at: number; scene: React.FC<SceneProps>; half?: boolean }> = [
  { at: 0, scene: ExampleSoloScene },
  { at: 16, scene: ExampleSplitScene },
];

/** Cut points, on the grid. The first one stays at 0 so the video starts clean. */
const CUTS = SCHEDULE.map((s, i) => ({
  ...s,
  at: i === 0 ? 0 : s.half ? snapHalf(s.at) : snapBar(s.at),
}));

const activeAt = (sec: number) => {
  let i = 0;
  for (let k = 0; k < CUTS.length; k++) if (sec >= CUTS[k].at) i = k;
  const start = CUTS[i].at;
  const end = i + 1 < CUTS.length ? CUTS[i + 1].at : SONG_S;
  return { Scene: CUTS[i].scene, start, end };
};

/**
 * The sung line, held on screen for as long as it is being sung.
 *
 * Drawn by the composition rather than by each scene so it survives a cut
 * without blinking, and so no scene can accidentally cover it. It is also the
 * best bug-catcher you have: in a contact sheet, a line that does not match the
 * picture above it means the schedule is out of step with the vocal.
 */
const LyricBand: React.FC<{ sec: number }> = ({ sec }) => {
  const line = lineAt(sec);
  if (!line) return null;
  // Fade in over about a beat so a new line does not pop against the music.
  const inT = Math.min(1, (sec - line.start + 0.12) / 0.22);
  return (
    <div
      style={{
        position: 'absolute', left: 60, top: LYRIC_Y, width: W - 120, textAlign: 'center',
        fontFamily: THAI, fontWeight: 600, fontSize: 46, lineHeight: 1.25,
        color: '#F2F2F4', opacity: 0.92 * inT,
        textShadow: '0 0 26px rgba(0,0,0,.95), 0 2px 10px rgba(0,0,0,.9)',
      }}
    >
      {line.text}
    </div>
  );
};

export const Mv: React.FC = () => {
  const frame = useCurrentFrame();
  const sec = frameToSec(frame);
  const { Scene, start, end } = activeAt(sec);
  const t = sec - start;
  const u = Math.min(1, Math.max(0, t / Math.max(0.001, end - start)));
  return (
    <AbsoluteFill style={{ backgroundColor: '#101010' }}>
      <Scene t={t} u={u} bars={barsAt(sec)} />
      <LyricBand sec={sec} />
    </AbsoluteFill>
  );
};
