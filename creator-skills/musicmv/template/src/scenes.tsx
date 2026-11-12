import React from 'react';
import { StickFigure } from './Figure';
import { SoloStage, SplitStage } from './Stage';
import { celebrate, pointing, scooping, standing } from './poses';
import { AiOrb } from './props/common';
import { FileGrid, Heap, PageStack, Slab } from './props/mv';
import { beatPhase, beatPulse } from './song';

/**
 * Every scene in the video. Replace these two examples with your own.
 *
 * A scene gets three clocks and picks whichever suits it:
 *   `u`    0..1 across the scene — for one-shot builds (a chart growing in)
 *   `bars` elapsed bars since the track's first downbeat — for anything that
 *          must stay locked to the beat ACROSS a cut, which per-scene time can't do
 *   `t`    seconds since the scene started, for plain easing
 *
 * The reel format forbids progressions because a 7-second loop has to return to
 * its start. A music video cuts, so progressions are allowed here and are the
 * main way a scene says "and then this happened".
 *
 * Keep props clear of y 292–340 on screen — that band belongs to the caption.
 * Remember an orb's halo is 3.2x its radius, then multiplied by the stage scale.
 */
export type SceneProps = { t: number; u: number; bars: number };

/** Ease that starts fast and settles — for things that snap in on a downbeat. */
export const settle = (x: number) => 1 - Math.pow(1 - Math.min(1, Math.max(0, x)), 3);

/** One subject, centred. Use when the beat is about a single actor. */
export const ExampleSoloScene: React.FC<SceneProps> = ({ u, bars }) => {
  const fig = standing(beatPhase(bars, 1));
  const grow = settle(u * 1.6);
  return (
    <SoloStage goal="คำเดียวบนสุด" label="ป้ายใต้ตัวละคร">
      <g>
        <Slab x={170} y={-40} w={150} h={110} paint="orange" opacity={grow} />
        <g transform={`scale(${1 + 0.08 * beatPulse(bars, 1)})`}>
          <AiOrb x={170} y={-360} t={beatPhase(bars, 1)} r={28} />
        </g>
        <g transform="translate(-190, 0)">
          <StickFigure joints={fig.joints} tone="orange" />
        </g>
      </g>
    </SoloStage>
  );
};

/** Two sides on one ground line — the workhorse shape. */
export const ExampleSplitScene: React.FC<SceneProps> = ({ bars }) => {
  const l = scooping(beatPhase(bars, 1));
  const r = pointing(beatPhase(bars, 0.5));
  return (
    <SplitStage
      goal="เป้าหมายเดียวกัน"
      left={{
        label: 'ทำเองทั้งกอง',
        children: (
          <g>
            <Heap n={9} paint="steel" x={92} />
            <g transform="translate(-96, 0)">
              <StickFigure joints={l.joints} tone="silver" />
            </g>
          </g>
        ),
      }}
      right={{
        label: 'สั่งทีเดียว',
        children: (
          <g>
            <PageStack n={4} x={96} />
            <AiOrb x={96} y={-330} t={beatPhase(bars, 1)} r={26} />
            <g transform="translate(-96, 0)">
              <StickFigure joints={r.joints} tone="orange" />
            </g>
          </g>
        ),
      }}
      back={
        // Full-width scenery sits in unscaled stage coords, ground at y = 0.
        // Hang it high enough to clear both the figures and the caption.
        <g transform="translate(540, -560)">
          <FileGrid cols={16} rows={6} sweep={beatPhase(bars, 0.25)} cell={40} y={0} />
        </g>
      }
    />
  );
};

/** Kept so the import list above shows the celebrate pose exists. */
export const ExampleFinalScene: React.FC<SceneProps> = ({ bars }) => {
  const fig = celebrate(beatPhase(bars, 1));
  return (
    <SoloStage>
      <StickFigure joints={fig.joints} tone="orange" />
    </SoloStage>
  );
};
