import React from 'react';
import { AbsoluteFill } from 'remotion';
import { envelope, rms } from '../features';
import { AMBER } from '../theme';

/**
 * Vignette, bloom and grain -- the pass that makes the layers look photographed
 * together rather than stacked.
 *
 * The bloom is driven by the sub envelope, so the whole frame swells fractions
 * of a stop on each kick. It is the cheapest way to make a still picture feel
 * like it is in the room with the bass, and at 6% peak opacity it is felt more
 * than seen.
 */
export const Finish: React.FC<{ frame: number; W: number; H: number }> = ({
  frame,
  W,
  H,
}) => {
  const e = envelope(frame, 'sub');
  const level = rms(frame);
  return (
    <>
      <AbsoluteFill
        style={{
          background: `radial-gradient(ellipse at 50% 48%, transparent 52%, rgba(20,11,34,0.42) 86%, rgba(20,11,34,0.72) 100%)`,
          pointerEvents: 'none',
        }}
      />
      <AbsoluteFill
        style={{
          background: AMBER.base,
          mixBlendMode: 'overlay',
          opacity: 0.02 + e * 0.06,
          pointerEvents: 'none',
        }}
      />
      {/* No scanlines here. They read as a CRT over photography, but over flat
          cartoon fills they just look like a broken screen. The grain below
          carries the same job at a fraction of the strength. */}
      {/* Grain, drawn as an SVG turbulence tile so it costs one paint instead
          of a per-frame canvas. Opacity rides the level so loud passages are
          grittier. */}
      <AbsoluteFill
        style={{
          opacity: 0.035 + level * 0.035,
          mixBlendMode: 'overlay',
          pointerEvents: 'none',
          backgroundImage:
            "url(\"data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='160' height='160'><filter id='n'><feTurbulence type='fractalNoise' baseFrequency='0.85' numOctaves='3'/></filter><rect width='160' height='160' filter='url(%23n)' opacity='0.5'/></svg>\")",
          backgroundSize: '160px 160px',
        }}
      />
    </>
  );
};
