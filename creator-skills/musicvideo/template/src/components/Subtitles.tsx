import React from 'react';
import { interpolate } from 'remotion';
import subs from '../subtitles.json';
import { F_SEC, PAPER, AMBER, DISPLAY } from '../theme';
import { envelope } from '../features';

type Line = { text: string; start: number; end: number };
const LINES = subs as Line[];

/** The line being sung at `seconds`, if any. */
const lineAt = (s: number): Line | null => {
  // Lines never overlap (tools/subtitles.py asserts it), so the first hit wins.
  for (const l of LINES) if (s >= l.start && s <= l.end) return l;
  return null;
};

/**
 * Lyrics, from the source's own word-level alignment.
 *
 * Set in the display face rather than a UI font: at this size over a moving
 * photograph a light UI weight disappears into the picture, and the frame
 * already carries that face in the titles.
 *
 * The scrim is doing real work. The backdrops cut every few bars and some of
 * them are bright amber in exactly the band the text sits in, so text-shadow
 * alone loses the line for a whole scene. A soft ellipse behind it costs
 * nothing on the dark stills and saves the bright ones.
 */
export const Subtitles: React.FC<{
  frame: number;
  W: number;
  bottom: number;
  /** Defaults are the 1920-wide values; a 1080-wide frame needs about 34. */
  size?: number;
  widthPct?: number;
}> = ({ frame, W, bottom, size = 46, widthPct = 0.78 }) => {
  const s = F_SEC(frame);
  const line = lineAt(s);
  if (!line) return null;

  // Fade rather than cut: a hard swap reads as a glitch when two lines land a
  // tenth of a second apart, which happens all through the dense sections.
  const FADE = 0.14;
  const op = interpolate(
    s,
    [line.start, line.start + FADE, line.end - FADE, line.end],
    [0, 1, 1, 0],
    { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' },
  );
  const e = envelope(frame, 'sub');

  return (
    <div
      style={{
        position: 'absolute',
        left: 0,
        right: 0,
        bottom,
        display: 'flex',
        justifyContent: 'center',
        opacity: op,
        pointerEvents: 'none',
      }}
    >
      <div style={{ position: 'relative', maxWidth: W * widthPct, padding: '18px 46px' }}>
        <div
          style={{
            position: 'absolute',
            inset: 0,
            background:
              'radial-gradient(ellipse at 50% 50%, rgba(3,5,8,0.82) 0%, rgba(3,5,8,0.55) 58%, rgba(3,5,8,0) 100%)',
            filter: 'blur(6px)',
          }}
        />
        <div
          style={{
            position: 'relative',
            fontFamily: DISPLAY,
            fontSize: size,
            fontWeight: 800,
            // Thai stacks vowel marks above and tone marks below the line,
            // so it needs more leading than Latin at the same size.
            lineHeight: 1.34,
            // Never track Thai: the marks belong to the glyph beneath them and
            // extra spacing visibly detaches them.
            letterSpacing: 0,
            textAlign: 'center',
            color: PAPER,
            textShadow: `0 2px 0 rgba(0,0,0,0.75), 0 0 ${18 + e * 26}px ${AMBER.glow}`,
          }}
        >
          {line.text}
        </div>
      </div>
    </div>
  );
};
