import React from 'react';
import { AbsoluteFill, useCurrentFrame, interpolate, Easing } from 'remotion';
import { Backdrop } from './components/Backdrop';
import { Analyser } from './components/Analyser';
import { Driver } from './components/SpeakerRig';
import { Finish } from './components/Finish';
import { Subtitles } from './components/Subtitles';
import { OpeningCard, Lockup, ClosingCard } from './components/Titles';
import { envelope, sceneAt, SCENES } from './features';
import {
  TALL, INK, AMBER, CYAN, SMOKE, MONO,
  TOTAL_FRAMES, F_SEC, BPM,
} from './theme';

const { W, H } = TALL;

/* ------------------------------------------------------------- the grid

   Everything in this cut hangs off two horizontal lines.

   FLOOR_Y is the front edge of the stage: the photograph ends there, its
   reflection starts there, and the drivers stand on it. STAGE_Y is where the
   analyser stands, far enough up the frame that Facebook's caption strip
   (~250px) eats only the analyser's reflection, which is the one element in
   the frame designed to be half visible anyway.

   The photograph is laid in at its own 16:9 ratio (1080 x 607). Cropping it
   to 9:16 would throw away two thirds of every still, and these are wide
   compositions -- a turntable, a line array -- with nothing left once the
   sides are gone.                                                        */

const HERO_H = Math.round((W * 9) / 16); // 607
const HERO_TOP = 424;
const FLOOR_Y = HERO_TOP + HERO_H;       // 1031
const HERO_REFL_H = 268;

/* The analyser is tall and stands well clear of the bottom edge: its bars and
   its reflection both finish above 1640, which leaves the bottom ~280px --
   exactly the strip Facebook covers with the caption and action rail -- as
   nothing but floor falling off into the dark. Nothing is lost there because
   nothing was put there. */
const ANALYSER_H = 300;
const STAGE_Y = 1596;                    // analyser baseline
const ANALYSER_TOP = STAGE_Y - ANALYSER_H;

const ECHO_H = HERO_TOP + 26;            // upper band, bled under the hero

/** Right edge kept clear of Facebook's action rail. */
const SAFE_R = 128;
const PAD_L = 44;

const tc = (s: number) => {
  const m = Math.floor(Math.max(0, s) / 60);
  const r = Math.floor(Math.max(0, s) % 60);
  return `${m}:${String(r).padStart(2, '0')}`;
};

/**
 * A driver standing on FLOOR_Y, with the floor doing its job underneath.
 *
 * The reflection is not decoration. Without it the drivers hang in a black
 * band with no surface under them and the lower half of the frame reads as
 * an unfinished export. Reflecting them gives that dark area a reason to be
 * dark -- it is a polished stage -- and it is the same surface the analyser
 * stands on, so the two halves of the composition share a floor.
 *
 * The mirror is a second, independently rendered Driver rather than a CSS
 * clone of the first: the cone is moving, and a reflection that lags the
 * thing it reflects is worse than no reflection at all.
 */
const TallRig: React.FC<{
  frame: number;
  size: number;
  right: number;
  offset?: number;
  tint?: 'amber' | 'cyan';
  opacity?: number;
}> = ({ frame, size, right, offset = 0, tint = 'amber', opacity = 1 }) => {
  const fade =
    'linear-gradient(180deg, rgba(0,0,0,0.95), rgba(0,0,0,0.35) 42%, transparent 80%)';
  return (
    <>
      <div
        style={{
          position: 'absolute', right, top: FLOOR_Y - size,
          width: size, height: size, opacity,
        }}
      >
        <Driver frame={frame} size={size} offset={offset} tint={tint} />
      </div>
      <div
        style={{
          position: 'absolute', right, top: FLOOR_Y, width: size, height: size * 0.7,
          overflow: 'hidden', opacity: opacity * 0.45, filter: 'blur(3px)',
          maskImage: fade, WebkitMaskImage: fade,
        }}
      >
        <div style={{ width: size, height: size, transform: 'scaleY(-1)' }}>
          <Driver frame={frame} size={size} offset={offset} tint={tint} />
        </div>
      </div>
    </>
  );
};

/**
 * The stage floor, drawn as light rather than as a grid.
 *
 * Nine specular streaks, spaced so they crowd toward the back and open out
 * toward the camera, which is what a wet stage does to a row of overheads.
 * They are here for a structural reason: below the photograph the frame is
 * one long dark area, and darkness with texture reads as a surface while
 * darkness without it reads as an unfinished export. Opacity rides the bass
 * so the floor breathes with the track instead of sitting there.
 */
const FloorLight: React.FC<{ frame: number }> = ({ frame }) => {
  const e = envelope(frame, 'bass');
  const ROWS = 9;
  return (
    <>
      {Array.from({ length: ROWS }).map((_, i) => {
        const t = (i + 1) / ROWS;
        const y = FLOOR_Y + (H - FLOOR_Y) * Math.pow(t, 1.75);
        const op = (0.075 + t * 0.055) * (0.65 + e * 0.7);
        return (
          <div
            key={i}
            style={{
              position: 'absolute', left: 0, right: 0, top: y, height: 1 + t * 4,
              filter: `blur(${0.5 + t * 4.5}px)`,
              background: `linear-gradient(90deg, transparent, rgba(255,196,107,${op}) 16%, rgba(255,196,107,${op * 1.35}) 54%, rgba(143,232,255,${op * 0.55}) 86%, transparent)`,
            }}
          />
        );
      })}
    </>
  );
};

/**
 * The 9:16 cut, for Facebook.
 *
 * Read top to bottom: title over an out-of-focus band of the room, the
 * photograph laid in sharp as a card with a shadow under it, then the stage --
 * reflection, drivers, floor light, analyser. Three zones, each carrying
 * weight, so the eye has somewhere to go on a phone at arm's length.
 *
 * The upper band is the picture from fifteen seconds ago, blurred down. That
 * is cheaper and more coherent than inventing a graphic for the top third:
 * every still was lit under the same amber key, so any two of them sit
 * together, and using an older one means the top of the frame changes on a
 * different cut from the middle, which stops the two zones reading as one
 * flat slab.
 */
export const MvTall: React.FC = () => {
  const frame = useCurrentFrame();
  const sec = F_SEC(frame);
  const sub = envelope(frame, 'sub');
  const bass = envelope(frame, 'bass');
  const high = envelope(frame, 'high', 0.6, 0.13);

  // Fifteen seconds back is two scene cuts on this grid; wrapped so the very
  // start of the track still shows a picture rather than the fallback ground.
  const echoFrame = (frame - 450 + TOTAL_FRAMES) % TOTAL_FRAMES;
  const { index } = sceneAt(sec);
  const progress = frame / TOTAL_FRAMES;

  const heroGlow = 0.2 + bass * 0.35;

  // The rig steps in only once the opening card has fully cleared. A 352px
  // driver sitting under the title was the one real collision in the layout,
  // and crossfading the two just made it a translucent collision.
  const rigIn = interpolate(sec, [13.6, 17.2], [0, 1], {
    extrapolateLeft: 'clamp', extrapolateRight: 'clamp', easing: Easing.out(Easing.cubic),
  });

  return (
    <AbsoluteFill style={{ backgroundColor: INK }}>
      {/* The room: a bled, defocused copy of the current still, so no part of
          the frame is ever flat black -- including behind the type. */}
      <AbsoluteFill
        style={{
          filter: 'blur(64px) brightness(0.46) saturate(1.15)',
          transform: 'scale(1.4)',
        }}
      >
        <Backdrop frame={frame} W={W} H={H} />
      </AbsoluteFill>

      {/* Upper band: the previous picture, soft, riding the hats. */}
      <div style={{ position: 'absolute', top: 0, left: 0, width: W, height: ECHO_H, overflow: 'hidden' }}>
        <div
          style={{
            position: 'absolute', inset: 0,
            filter: `blur(7px) brightness(${1.55 + high * 0.45}) contrast(1.02) saturate(1.05)`,
          }}
        >
          <Backdrop frame={echoFrame} W={W} H={ECHO_H} />
        </div>
        <div
          style={{
            position: 'absolute', inset: 0,
            background:
              'linear-gradient(180deg, rgba(5,7,10,0.6) 0%, rgba(5,7,10,0.24) 34%, rgba(5,7,10,0.52) 74%, rgba(5,7,10,0.94) 100%)',
          }}
        />
        <div
          style={{
            position: 'absolute', inset: 0, mixBlendMode: 'screen',
            background: `radial-gradient(ellipse 900px 460px at 44% -8%, rgba(255,138,31,${0.2 + high * 0.13}) 0%, rgba(177,74,0,0.07) 44%, transparent 78%),
                         radial-gradient(ellipse 460px 300px at 97% 6%, rgba(40,196,232,${0.11 + high * 0.08}) 0%, transparent 72%)`,
          }}
        />
      </div>

      {/* Stage floor: the plane everything below FLOOR_Y stands on. */}
      <div
        style={{
          position: 'absolute', left: 0, right: 0, top: FLOOR_Y, height: H - FLOOR_Y,
          background: `linear-gradient(180deg, rgba(255,138,31,${0.055 + sub * 0.055}) 0%, rgba(255,138,31,0.022) 30%, rgba(5,7,10,0) 62%)`,
        }}
      />

      <FloorLight frame={frame} />

      {/* The photograph's reflection, mirrored in that floor. */}
      <div
        style={{
          position: 'absolute', top: FLOOR_Y, left: 0, width: W, height: HERO_REFL_H,
          overflow: 'hidden', opacity: 0.55, filter: 'blur(2px)',
          maskImage:
            'linear-gradient(180deg, rgba(0,0,0,0.95), rgba(0,0,0,0.4) 58%, transparent 96%)',
          WebkitMaskImage:
            'linear-gradient(180deg, rgba(0,0,0,0.95), rgba(0,0,0,0.4) 58%, transparent 96%)',
        }}
      >
        <div
          style={{
            position: 'absolute', top: 0, left: 0, width: W, height: HERO_H,
            transform: 'scaleY(-1)',
          }}
        >
          <Backdrop frame={frame} W={W} H={HERO_H} />
        </div>
      </div>

      {/* Key light pooling on the floor under the rig, on the sub band. */}
      <div
        style={{
          position: 'absolute', left: 0, right: 0, top: FLOOR_Y - 20, height: 560,
          mixBlendMode: 'screen', pointerEvents: 'none',
          background: `radial-gradient(ellipse 520px 210px at 70% 0%, rgba(255,138,31,${0.13 + sub * 0.15}) 0%, rgba(255,138,31,0.045) 42%, transparent 72%)`,
        }}
      />

      {/* The photograph, at its own ratio, proud of the band behind it. */}
      <div
        style={{
          position: 'absolute', top: HERO_TOP, left: 0, width: W, height: HERO_H,
          overflow: 'hidden',
          boxShadow: '0 26px 70px rgba(0,0,0,0.92), 0 -18px 48px rgba(0,0,0,0.75)',
        }}
      >
        <Backdrop frame={frame} W={W} H={HERO_H} />
      </div>

      {/* Hairlines top and bottom -- the edge of the card, lit on the bass. */}
      <div
        style={{
          position: 'absolute', left: 0, right: 0, top: HERO_TOP, height: 2,
          background: `linear-gradient(90deg, transparent, rgba(255,196,107,${heroGlow}) 22%, rgba(255,196,107,${heroGlow}) 78%, transparent)`,
        }}
      />
      <div
        style={{
          position: 'absolute', left: 0, right: 0, top: FLOOR_Y - 2, height: 2,
          background: `linear-gradient(90deg, transparent, rgba(255,196,107,${heroGlow + 0.14}) 26%, rgba(143,232,255,${heroGlow * 0.6}) 82%, transparent)`,
          boxShadow: `0 0 ${14 + bass * 26}px ${AMBER.glow}`,
        }}
      />

      <TallRig frame={frame} size={352} right={104} tint="amber" opacity={rigIn} />
      <TallRig frame={frame} size={182} right={432} offset={-3} tint="cyan" opacity={0.8 * rigIn} />


      {/* Front of stage. The analyser stands on this line and its light spills
          forward, so the strip under it recedes instead of ending. */}
      <div
        style={{
          position: 'absolute', left: -120, right: -120, top: STAGE_Y - 190, height: 500,
          mixBlendMode: 'screen', pointerEvents: 'none',
          background: `radial-gradient(ellipse 760px 300px at 50% 40%, rgba(255,138,31,${0.10 + sub * 0.12}) 0%, rgba(40,196,232,0.035) 46%, transparent 76%)`,
        }}
      />
      <div
        style={{
          position: 'absolute', left: 0, right: 0, top: STAGE_Y, height: H - STAGE_Y,
          background: `linear-gradient(180deg, rgba(255,196,107,${0.05 + bass * 0.05}) 0%, rgba(255,138,31,0.028) 28%, rgba(5,7,10,0) 78%)`,
          pointerEvents: 'none',
        }}
      />

      <div style={{ position: 'absolute', left: 0, top: ANALYSER_TOP }}>
        <Analyser frame={frame} W={W} height={ANALYSER_H} />
      </div>

      {/* Stage lip -- the analyser's bars fade out at their base, so without
          this the row has nothing to stand on. */}
      <div
        style={{
          position: 'absolute', left: 0, right: 0, top: STAGE_Y, height: 2,
          background: `linear-gradient(90deg, transparent, rgba(255,196,107,${0.16 + bass * 0.3}) 14%, rgba(255,196,107,${0.2 + bass * 0.34}) 52%, rgba(143,232,255,${0.13 + bass * 0.2}) 88%, transparent)`,
          boxShadow: `0 0 ${16 + bass * 30}px rgba(255,138,31,0.35)`,
        }}
      />

      {/* Top rail: where we are in the track, and what it is. */}
      <div style={{ position: 'absolute', top: 0, left: 0, width: W, height: 3, background: 'rgba(255,255,255,0.09)' }} />
      <div
        style={{
          position: 'absolute', top: 0, left: 0, height: 3, width: W * progress,
          background: `linear-gradient(90deg, ${AMBER.deep}, ${AMBER.base})`,
          boxShadow: `0 0 ${10 + sub * 16}px ${AMBER.glow}`,
        }}
      />
      <div
        style={{
          position: 'absolute', top: 30, left: PAD_L, right: SAFE_R,
          display: 'flex', justifyContent: 'space-between',
          fontFamily: MONO, fontSize: 19, letterSpacing: 3.2, color: SMOKE, opacity: 0.72,
        }}
      >
        <span>{Math.round(BPM)} BPM / BASS HEAVY</span>
        <span>
          {String(index + 1).padStart(2, '0')}/{SCENES.length}&nbsp;&nbsp;{tc(sec)}
        </span>
      </div>

      {/* Lockup anchors itself to the bottom-left of whatever box contains it,
          so the box is how it gets moved: here it lands just above the card. */}
      <div style={{ position: 'absolute', top: 0, left: 0, width: W, height: HERO_TOP - 34 + 344 }}>
        <Lockup frame={frame} wide={false} W={W} H={H} />
      </div>

      {/* Spill off the front edge of the stage. Finish's vignette crushes the
          last 200px hard, so the light has to be put in before it. */}
      <div
        style={{
          position: 'absolute', left: 0, right: 0, bottom: 0, height: 330,
          pointerEvents: 'none',
          background: `linear-gradient(0deg, rgba(255,138,31,${0.075 + sub * 0.05}) 0%, rgba(255,138,31,0.028) 42%, transparent 88%)`,
        }}
      />

      {/* Both cards centre themselves in whatever box they are given, and the
          middle of a 1920px frame is exactly where the rig stands. Boxing them
          lands the type on the photograph instead, which is where it belongs:
          the opening title in the middle of the picture, the closing figure a
          little higher so it clears the drivers without having to hide them. */}
      <div style={{ position: 'absolute', top: 0, left: 0, width: W, height: 1454 }}>
        <OpeningCard frame={frame} W={W} wide={false} />
      </div>
      <div style={{ position: 'absolute', top: 0, left: 0, width: W, height: 1200 }}>
        <ClosingCard frame={frame} W={W} wide={false} />
      </div>
      <Subtitles frame={frame} W={W} bottom={H - ANALYSER_TOP + 26} size={34} widthPct={0.9} />
      <Finish frame={frame} W={W} H={H} />
    </AbsoluteFill>
  );
};
