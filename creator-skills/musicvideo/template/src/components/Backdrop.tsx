import React from 'react';
import { AbsoluteFill, Img, staticFile, interpolate, Easing } from 'remotion';
import { sceneAt, envelope, SCENES } from '../features';
import { F_SEC, INK } from '../theme';
import available from '../available.json';

const HAVE: string[] = (available as { images: string[] }).images;

/**
 * The photographic layer: one still per scene, cut on the beat grid.
 *
 * Cuts are hard. A crossfade would smear the one thing the cut is for -- the
 * picture changing exactly when the kick lands -- into a half-second of mush,
 * and on a 129 BPM four-on-the-floor track that reads as a slideshow rather
 * than an edit.
 *
 * Stills are addressed by name but resolved against what is actually on disk,
 * so a missing file falls back to the procedural ground instead of failing the
 * whole render.
 */
export const Backdrop: React.FC<{ frame: number; W: number; H: number }> = ({
  frame,
  W,
  H,
}) => {
  const seconds = F_SEC(frame);
  const { scene, index, t } = sceneAt(seconds);

  // Resolve this scene's still; if the bridge has not delivered it yet, walk
  // the available list so the video still cuts between real pictures.
  const wanted = `${scene.img}.png`;
  const file = HAVE.includes(wanted)
    ? wanted
    : HAVE.length
      ? HAVE[index % HAVE.length]
      : null;

  // Sub-band envelope drives a scale punch: the picture leans into the frame
  // on every kick. Kept under 2% -- past that it reads as a wobble, not weight.
  const punch = envelope(frame, 'sub') * 0.022;

  // Ken Burns. Four directions, cycled by scene, so a still that comes back
  // later never repeats the same move.
  const ease = Easing.inOut(Easing.ease);
  const zoom = interpolate(t, [0, 1], [1.06, 1.16], { easing: ease });
  const zoomOut = interpolate(t, [0, 1], [1.16, 1.06], { easing: ease });
  const pan = interpolate(t, [0, 1], [-3.2, 3.2], { easing: ease });

  const moves = [
    { scale: zoom, x: 0, y: 0 },
    { scale: zoomOut, x: 0, y: 0 },
    { scale: 1.12, x: pan, y: 0 },
    { scale: 1.12, x: -pan, y: 0 },
  ];
  const m = moves[scene.dir % 4];

  return (
    <AbsoluteFill style={{ backgroundColor: INK, overflow: 'hidden' }}>
      {file ? (
        <Img
          src={staticFile(`img/${file}`)}
          style={{
            width: '100%',
            height: '100%',
            objectFit: 'cover',
            transform: `scale(${m.scale + punch}) translate(${m.x}%, ${m.y}%)`,
            // Cartoon art, not photographs. The previous grade dropped
            // brightness to 0.62 and pulled saturation to make night
            // photography sit back; doing that here turns flat colour muddy
            // and throws away the thing the illustration is made of. Barely
            // touch it, and let the vignette do the settling instead.
            filter: 'brightness(0.94) contrast(1.06) saturate(1.06)',
          }}
        />
      ) : (
        <ProceduralGround frame={frame} W={W} H={H} />
      )}
    </AbsoluteFill>
  );
};

/**
 * What plays when there is no still: a lit floor and a horizon, drawn.
 *
 * Not a placeholder colour -- if the bridge never delivers, this has to hold
 * the frame on its own for the whole song.
 */
const ProceduralGround: React.FC<{ frame: number; W: number; H: number }> = ({
  frame,
  W,
  H,
}) => {
  const e = envelope(frame, 'sub');
  const horizon = H * 0.58;
  return (
    <AbsoluteFill>
      <div
        style={{
          position: 'absolute',
          inset: 0,
          background: `radial-gradient(ellipse ${W * 0.7}px ${H * 0.5}px at 50% ${horizon}px,
            rgba(255,138,31,${0.20 + e * 0.16}) 0%,
            rgba(177,74,0,0.10) 38%,
            ${INK} 72%)`,
        }}
      />
      <div
        style={{
          position: 'absolute',
          left: 0,
          right: 0,
          top: horizon,
          height: 2,
          background: `linear-gradient(90deg, transparent, rgba(255,196,107,${0.35 + e * 0.4}), transparent)`,
        }}
      />
    </AbsoluteFill>
  );
};

export const SCENE_COUNT = SCENES.length;
