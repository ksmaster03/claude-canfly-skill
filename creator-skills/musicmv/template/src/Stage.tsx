import React from 'react';
import { AbsoluteFill } from 'remotion';
import {
  W, H, HORIZON, LEFT_X, RIGHT_X, LABEL_Y, GOAL_Y,
  ORANGE, SILVER, REFLECTION, SUBJECT_SCALE,
} from './theme';
import { THAI } from './fonts';
import { FigureDefs } from './Figure';
import { PropDefs } from './props/common';

/**
 * Shared shell for every scene in the video.
 *
 * The series version of this file carried a brand mark and had no fades because
 * its clips looped. Here the shell is plain: the video cuts between scenes on
 * downbeats, and the only persistent overlay is the lyric band, which the
 * top-level composition draws above every scene so it never blinks at a cut.
 */

/** A motion that returns to its start exactly at the loop point. `cycles` must be an integer. */
export const wave = (u: number, cycles: number, phase = 0) => Math.sin((u * cycles + phase) * Math.PI * 2);
/** Sawtooth 0..1 repeated `cycles` times — for anything that resets rather than reverses. */
export const saw = (u: number, cycles: number, phase = 0) => (u * cycles + phase) % 1;

export const Background: React.FC = () => (
  <>
    <AbsoluteFill style={{ background: '#101010' }} />
    <AbsoluteFill
      style={{
        background:
          'radial-gradient(ellipse 118% 36% at 50% 44%, rgba(58,58,58,0.32) 0%, rgba(30,30,30,0.13) 45%, rgba(16,16,16,0) 100%)',
      }}
    />
  </>
);

export const Horizon: React.FC<{ y?: number }> = ({ y = HORIZON }) => (
  <div
    style={{
      position: 'absolute', left: 0, top: y - 1, width: W, height: 2,
      background:
        'linear-gradient(90deg, rgba(255,255,255,0) 0%, rgba(255,255,255,0.10) 14%, rgba(255,255,255,0.58) 50%, rgba(255,255,255,0.10) 86%, rgba(255,255,255,0) 100%)',
      boxShadow: '0 0 30px rgba(255,255,255,0.12)',
    }}
  />
);

/** The one word floating at the top — the idea the scene is about. */
const Goal: React.FC<{ text: string }> = ({ text }) => (
  <div
    style={{
      position: 'absolute', left: 0, top: GOAL_Y, width: W, textAlign: 'center',
      fontFamily: THAI, fontWeight: 600, fontSize: 38, letterSpacing: 6,
      color: ORANGE.text, opacity: 0.92, textShadow: `0 0 30px ${ORANGE.base}33`,
    }}
  >
    {text}
  </div>
);

const Label: React.FC<{ text: string; x: number; tone: 'silver' | 'orange' }> = ({ text, x, tone }) => (
  <div
    style={{
      position: 'absolute', left: x - 300, top: LABEL_Y, width: 600, textAlign: 'center',
      fontFamily: THAI, fontWeight: 600, fontSize: 36, letterSpacing: 0.5,
      color: tone === 'orange' ? ORANGE.text : SILVER.text,
      textShadow: tone === 'orange' ? `0 0 26px ${ORANGE.base}33` : '0 0 22px rgba(0,0,0,.85)',
    }}
  >
    {text}
  </div>
);

/**
 * Height of the drawing box above the horizon.
 *
 * The series used 620, which is plenty for a figure with a raised arm. This
 * video hangs orbs, grids and clocks well above head height, and anything past
 * the box was being silently clipped by the svg viewport — an orb simply would
 * not be in the frame, with no error anywhere.
 *
 * Size it to the frame, not to the tallest prop. Trimming it to 850 to save
 * render cost looked safe until the arithmetic was done: an orb's halo is 3.2x
 * its radius, then multiplied by the stage scale, so the chorus orb's core
 * alone reached -898 and would have been sliced in half. The render cost is
 * dealt with by rendering in chunks (tools/render-mv.mjs), not by shaving this.
 *
 * REFLECTION.fadeHeight stays in pixels, so the mask stop below rescales with
 * this and the reflection still fades 150px past the horizon.
 */
export const STAGE_H = HORIZON;

/**
 * `height` and `viewBox` are separate so the reflection can draw the same scene
 * through a much shorter window without moving anything.
 *
 * Both defs blocks belong in EVERY svg that paints a figure or prop: SVG paint
 * servers resolve document-wide, so a single shared copy keeps working right up
 * until the scene holding it unmounts at a cut — and then every url(#…) fill in
 * the new scene silently renders as nothing.
 */
const StageSvg: React.FC<{ children: React.ReactNode; top?: number; height?: number }> = ({
  children, top = 0, height = STAGE_H,
}) => (
  <svg width={W} height={height} viewBox={`0 ${top} ${W} ${height}`} style={{ display: 'block' }}>
    <FigureDefs />
    <PropDefs />
    <g transform={`translate(0, ${STAGE_H})`}>{children}</g>
  </svg>
);

/**
 * Draws `children` once for real and once mirrored about the horizon.
 *
 * The mirror only ever shows REFLECTION.fadeHeight pixels — the mask kills
 * everything past that — so it draws a slice that tall rather than a second full
 * copy of the stage. That is not a micro-optimisation: the mirrored layer runs
 * through a CSS blur, and blurring a full 1080x1010 layer on every frame put the
 * render tab out of memory partway through the run. Remotion surfaced that as a
 * delayRender timeout on the font loader, which sent the first two days of
 * debugging in entirely the wrong direction.
 *
 * The slice sits directly below the horizon and is flipped about its own centre,
 * so ground-level content lands against the horizon. CSS masks apply before
 * transforms, hence the gradient is written bottom-opaque and ends up
 * top-opaque — densest at the horizon — once flipped.
 */
const Floor: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const FH = REFLECTION.fadeHeight;
  const mask = 'linear-gradient(to top, rgba(0,0,0,1) 0%, rgba(0,0,0,0) 100%)';
  return (
    <>
      <div style={{ position: 'absolute', left: 0, top: HORIZON - STAGE_H, width: W, height: STAGE_H }}>
        <StageSvg>{children}</StageSvg>
      </div>
      <div
        style={{
          position: 'absolute', left: 0, top: HORIZON, width: W, height: FH,
          transform: 'scaleY(-1)',
          opacity: REFLECTION.opacity, filter: `blur(${REFLECTION.blurPx}px)`,
          maskImage: mask, WebkitMaskImage: mask,
        }}
      >
        <StageSvg top={STAGE_H - FH} height={FH}>{children}</StageSvg>
      </div>
    </>
  );
};

export type Side = { label?: string; children: React.ReactNode };

/**
 * Two sides on ONE ground line, labelled underneath.
 *
 * Left/right rather than top/bottom is not a style choice — on the reference
 * page the two highest-performing clips are both left/right, and the top/bottom
 * one we originally copied did a fraction of the views.
 */
export const SplitStage: React.FC<{
  goal?: string;
  left: Side;
  right: Side;
  /** Full-width scenery behind both sides, in unscaled stage coords (ground at y=0). */
  back?: React.ReactNode;
  horizon?: boolean;
}> = ({ goal, left, right, back, horizon = true }) => (
  <AbsoluteFill style={{ backgroundColor: '#101010' }}>
    <Background />
    {horizon ? <Horizon /> : null}
    <Floor>
      {back}
      {/* Each side scales about its own point on the ground, so SUBJECT_SCALE
          changes how big the subjects are without moving them apart or off the
          labels underneath them. */}
      <g transform={`translate(${LEFT_X}, 0) scale(${SUBJECT_SCALE})`}>{left.children}</g>
      <g transform={`translate(${RIGHT_X}, 0) scale(${SUBJECT_SCALE})`}>{right.children}</g>
    </Floor>
    {goal ? <Goal text={goal} /> : null}
    {left.label ? <Label text={left.label} x={LEFT_X} tone="silver" /> : null}
    {right.label ? <Label text={right.label} x={RIGHT_X} tone="orange" /> : null}
  </AbsoluteFill>
);

/**
 * One subject centred on the ground line, for scenes that are about a single
 * actor rather than a comparison — the title, the bridge, the last chorus.
 */
export const SoloStage: React.FC<{
  goal?: string;
  label?: string;
  children: React.ReactNode;
  back?: React.ReactNode;
  horizon?: boolean;
  scale?: number;
}> = ({ goal, label, children, back, horizon = true, scale = SUBJECT_SCALE }) => (
  <AbsoluteFill style={{ backgroundColor: '#101010' }}>
    <Background />
    {horizon ? <Horizon /> : null}
    <Floor>
      {back}
      <g transform={`translate(${W / 2}, 0) scale(${scale})`}>{children}</g>
    </Floor>
    {goal ? <Goal text={goal} /> : null}
    {label ? <Label text={label} x={W / 2} tone="orange" /> : null}
  </AbsoluteFill>
);

/**
 * Free-form variant for scenes that are a diagram rather than characters.
 * `children` are drawn in full-frame coordinates (0,0 = top-left of 1080x1920).
 */
export const FullStage: React.FC<{ goal?: string; children: React.ReactNode; horizon?: boolean }> = ({
  goal, children, horizon = false,
}) => (
  <AbsoluteFill style={{ backgroundColor: '#101010' }}>
    <Background />
    {horizon ? <Horizon /> : null}
    <svg width={W} height={H} viewBox={`0 0 ${W} ${H}`} style={{ position: 'absolute', inset: 0 }}>
      <FigureDefs />
      <PropDefs />
      {children}
    </svg>
    {goal ? <Goal text={goal} /> : null}
  </AbsoluteFill>
);
