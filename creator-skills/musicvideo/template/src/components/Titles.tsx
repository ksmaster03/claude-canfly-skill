import React from 'react';
import { interpolate, Easing } from 'remotion';
import { envelope } from '../features';
import { AMBER, CYAN, PAPER, SMOKE, DISPLAY, TITLE, ARTIST, F_SEC, DURATION_S } from '../theme';

/**
 * Title treatments.
 *
 * The previous video's lockup carried a running "tokens burned" counter, which
 * was that song's whole joke and is meaningless here -- it survived the move
 * between projects because it lived in a shared component and nothing failed
 * when it was wrong. It is gone.
 *
 * Everything here also sits on a scrim. Over the cartoon backdrops, which run
 * bright coral and neon in exactly the corner the credit occupies, unbacked
 * text at any weight simply disappears for whole scenes.
 */

const Scrim: React.FC<{ children: React.ReactNode; pad?: number }> = ({ children, pad = 22 }) => (
  <div style={{ position: 'relative', display: 'inline-block', padding: `${pad * 0.7}px ${pad}px` }}>
    <div
      style={{
        position: 'absolute',
        inset: 0,
        background:
          'radial-gradient(ellipse at 50% 50%, rgba(20,11,34,0.80) 0%, rgba(20,11,34,0.52) 60%, rgba(20,11,34,0) 100%)',
        filter: 'blur(7px)',
      }}
    />
    <div style={{ position: 'relative' }}>{children}</div>
  </div>
);

export const OpeningCard: React.FC<{ frame: number; W: number; wide: boolean }> = ({
  frame, W, wide,
}) => {
  const s = F_SEC(frame);
  if (s > 13) return null;
  const inT = interpolate(s, [0.4, 1.5], [0, 1], {
    extrapolateLeft: 'clamp', extrapolateRight: 'clamp', easing: Easing.out(Easing.cubic),
  });
  const out = interpolate(s, [10.5, 13], [1, 0], {
    extrapolateLeft: 'clamp', extrapolateRight: 'clamp', easing: Easing.in(Easing.cubic),
  });
  const e = envelope(frame, 'sub');

  return (
    <div
      style={{
        position: 'absolute', inset: 0, display: 'flex', alignItems: 'center',
        justifyContent: 'center', opacity: inT * out,
      }}
    >
      <Scrim pad={wide ? 54 : 40}>
        <div style={{ textAlign: 'center' }}>
          <div
            style={{
              fontFamily: DISPLAY, fontWeight: 800,
              fontSize: wide ? W * 0.085 : W * 0.15,
              lineHeight: 1.1, color: PAPER, letterSpacing: 0,
              transform: `scale(${1 + e * 0.025})`,
              textShadow: `0 0 ${30 + e * 50}px ${AMBER.glow}, 0 ${wide ? 5 : 4}px 0 rgba(20,11,34,0.6)`,
            }}
          >
            {TITLE}
          </div>
          <div
            style={{
              marginTop: wide ? 18 : 14, fontFamily: DISPLAY, fontWeight: 600,
              fontSize: wide ? 26 : 24, color: CYAN.light, letterSpacing: 0,
            }}
          >
            {ARTIST}
          </div>
        </div>
      </Scrim>
    </div>
  );
};

/** The credit that lives in the corner through the body of the song. */
export const Lockup: React.FC<{ frame: number; wide: boolean; W: number; H: number }> = ({
  frame, wide, W, H,
}) => {
  const s = F_SEC(frame);
  const op = interpolate(s, [13, 15, DURATION_S - 17, DURATION_S - 14], [0, 1, 1, 0], {
    extrapolateLeft: 'clamp', extrapolateRight: 'clamp',
  });
  const pad = wide ? 40 : 30;
  return (
    <div style={{ position: 'absolute', left: pad, top: pad, opacity: op * 0.95 }}>
      <Scrim pad={wide ? 20 : 16}>
        <div
          style={{
            fontFamily: DISPLAY, fontWeight: 800, fontSize: wide ? 34 : 36,
            color: PAPER, letterSpacing: 0, lineHeight: 1.1,
          }}
        >
          {TITLE}
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginTop: 6 }}>
          <div style={{ width: 22, height: 3, background: AMBER.base, borderRadius: 2 }} />
          <div style={{ fontFamily: DISPLAY, fontWeight: 600, fontSize: wide ? 18 : 19, color: SMOKE }}>
            {ARTIST}
          </div>
        </div>
      </Scrim>
    </div>
  );
};

export const ClosingCard: React.FC<{ frame: number; W: number; wide: boolean }> = ({
  frame, W, wide,
}) => {
  const s = F_SEC(frame);
  if (s < DURATION_S - 15) return null;
  const op = interpolate(s, [DURATION_S - 14, DURATION_S - 11.5, DURATION_S - 1.2, DURATION_S],
    [0, 1, 1, 0], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' });
  return (
    <div
      style={{
        position: 'absolute', inset: 0, display: 'flex', alignItems: 'center',
        justifyContent: 'center', opacity: op,
      }}
    >
      <Scrim pad={wide ? 50 : 38}>
        <div style={{ textAlign: 'center' }}>
          <div
            style={{
              fontFamily: DISPLAY, fontWeight: 800, fontSize: wide ? W * 0.075 : W * 0.13,
              color: PAPER, letterSpacing: 0, textShadow: `0 0 44px ${AMBER.glow}`,
            }}
          >
            {TITLE}
          </div>
          <div
            style={{
              marginTop: wide ? 22 : 18, fontFamily: DISPLAY, fontWeight: 600,
              fontSize: wide ? 24 : 22, color: CYAN.light, letterSpacing: 0,
            }}
          >
            {ARTIST}
          </div>
        </div>
      </Scrim>
    </div>
  );
};
