import React from 'react';
import { AbsoluteFill, Img, staticFile, useCurrentFrame, useVideoConfig } from 'remotion';
import {
  W, H, HORIZON, LEFT_X, RIGHT_X, LABEL_Y, GOAL_Y, LOGO_Y,
  ORANGE, SILVER, BRAND_GREEN, REFLECTION, SUBJECT_SCALE,
} from './theme';
import { THAI } from './fonts';
import { FigureDefs } from './Figure';
import { PropDefs } from './props/common';

/**
 * Shared shell for every clip in the series.
 *
 * Deliberately has NO fade in or out: these clips are built to loop, and a fade
 * puts a black seam at the join. Loop cleanliness instead comes from every
 * motion being periodic over the clip length — see useLoop below.
 */

/** Normalised 0..1 position within the clip. Build motions off this, not off frames. */
export const useLoop = () => {
  const frame = useCurrentFrame();
  const { durationInFrames } = useVideoConfig();
  return frame / durationInFrames;
};

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

const Mark: React.FC = () => (
  <Img
    src={staticFile('brand/logo.png')}
    style={{ position: 'absolute', left: W / 2 - 31, top: LOGO_Y - 31, width: 62, height: 62, opacity: 0.62 }}
  />
);

const Goal: React.FC<{ text: string }> = ({ text }) => (
  <div
    style={{
      position: 'absolute', left: 0, top: GOAL_Y, width: W, textAlign: 'center',
      fontFamily: THAI, fontWeight: 600, fontSize: 34, letterSpacing: 6,
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

/** Height of the drawing box above the horizon. Tall enough for a raised arm plus props. */
export const STAGE_H = 620;

const StageSvg: React.FC<{ children: React.ReactNode }> = ({ children }) => (
  <svg width={W} height={STAGE_H} viewBox={`0 0 ${W} ${STAGE_H}`} style={{ display: 'block' }}>
    <FigureDefs />
    <PropDefs />
    <g transform={`translate(0, ${STAGE_H})`}>{children}</g>
  </svg>
);

/**
 * Draws `children` once for real and once mirrored about the horizon.
 *
 * The mirror is `scaleY(-1)` with transformOrigin 'bottom', so it reflects
 * exactly about the ground line. CSS masks apply before transforms, so the fade
 * runs toward the TOP of the box — which lands furthest from the horizon once
 * flipped.
 */
const Floor: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const svg = <StageSvg>{children}</StageSvg>;
  const stop = (REFLECTION.fadeHeight / STAGE_H) * 100;
  const mask = `linear-gradient(to top, rgba(0,0,0,1) 0%, rgba(0,0,0,0) ${stop}%)`;
  return (
    <>
      <div style={{ position: 'absolute', left: 0, top: HORIZON - STAGE_H, width: W, height: STAGE_H }}>{svg}</div>
      <div
        style={{
          position: 'absolute', left: 0, top: HORIZON - STAGE_H, width: W, height: STAGE_H,
          transform: 'scaleY(-1)', transformOrigin: 'bottom',
          opacity: REFLECTION.opacity, filter: `blur(${REFLECTION.blurPx}px)`,
          maskImage: mask, WebkitMaskImage: mask,
        }}
      >
        {svg}
      </div>
    </>
  );
};

export type Side = { label: string; children: React.ReactNode };

/**
 * The series format: two sides on ONE ground line, labelled underneath.
 *
 * Left/right rather than top/bottom is not a style choice — on the reference
 * page the two highest-performing clips (12M and 11M views) are both left/right,
 * and the top/bottom one we originally copied did 210K.
 */
export const SplitStage: React.FC<{
  goal?: string;
  left: Side;
  right: Side;
  /** Full-width scenery behind both sides, in unscaled stage coords (ground at y=0). */
  back?: React.ReactNode;
  /** Some clips supply their own ground (water, terrain) and want the line off. */
  horizon?: boolean;
  /** Only the series closer carries one — the top clips on the reference page have no CTA at all. */
  cta?: string;
}> = ({ goal, left, right, back, horizon = true, cta }) => (
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
    <Label text={left.label} x={LEFT_X} tone="silver" />
    <Label text={right.label} x={RIGHT_X} tone="orange" />
    {cta ? (
      <div
        style={{
          position: 'absolute', left: 0, top: LABEL_Y + 120, width: W, textAlign: 'center',
          fontFamily: THAI, fontWeight: 400, fontSize: 32, letterSpacing: 2, color: BRAND_GREEN,
          textShadow: `0 0 30px ${BRAND_GREEN}33`,
        }}
      >
        {cta}
      </div>
    ) : null}
    <Mark />
  </AbsoluteFill>
);

/**
 * Top/bottom variant, for metaphors that are a PATH rather than two actors —
 * a route over terrain only reads left-to-right, so the two routes have to
 * stack. The reference page's 10M and 4.2M clips both use this shape.
 */
export const TwoLaneStage: React.FC<{
  goal?: string;
  top: { label: string; children: React.ReactNode };
  bottom: { label: string; children: React.ReactNode };
}> = ({ goal, top, bottom }) => {
  const TOP_Y = 700;
  const BOTTOM_Y = 1240;
  const lane = (y: number, node: React.ReactNode) => (
    <svg width={W} height={520} viewBox={`0 0 ${W} 520`} style={{ position: 'absolute', left: 0, top: y - 520 }}>
      <FigureDefs />
      <PropDefs />
      <g transform="translate(0, 520)">{node}</g>
    </svg>
  );
  const label = (y: number, text: string, tone: 'silver' | 'orange') => (
    <div
      style={{
        position: 'absolute', left: 0, top: y, width: W, textAlign: 'center',
        fontFamily: THAI, fontWeight: 600, fontSize: 36,
        color: tone === 'orange' ? ORANGE.text : SILVER.text,
        textShadow: tone === 'orange' ? `0 0 26px ${ORANGE.base}33` : '0 0 22px rgba(0,0,0,.85)',
      }}
    >
      {text}
    </div>
  );
  return (
    <AbsoluteFill style={{ backgroundColor: '#101010' }}>
      <Background />
      {lane(TOP_Y, top.children)}
      {label(TOP_Y + 18, top.label, 'silver')}
      {lane(BOTTOM_Y, bottom.children)}
      {label(BOTTOM_Y + 18, bottom.label, 'orange')}
      {goal ? <Goal text={goal} /> : null}
      <Mark />
    </AbsoluteFill>
  );
};

/**
 * Free-form variant for clips that are a diagram rather than two characters.
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
    <Mark />
  </AbsoluteFill>
);
