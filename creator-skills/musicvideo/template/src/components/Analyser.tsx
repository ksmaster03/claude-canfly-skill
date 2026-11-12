import React from 'react';
import { spectrum, NBINS, envelope } from '../features';
import { AMBER, CYAN } from '../theme';

/**
 * The spectrum analyser that runs along the foot of the frame.
 *
 * 48 log-spaced bins, not 5 bands: with five, neighbouring bars move as one
 * block and the eye reads it as four fat blocks jumping, which looks like a
 * loading screen rather than a rig.
 *
 * Bars are drawn from the bottom up and mirrored into a dimmer reflection, so
 * the row reads as sitting ON something -- the same polished-floor logic the
 * stills were lit for.
 */
export const Analyser: React.FC<{
  frame: number;
  W: number;
  height: number;
  reflect?: boolean;
}> = ({ frame, W, height, reflect = true }) => {
  const bins = spectrum(frame);
  const gap = 3;
  const bw = (W - gap * (NBINS - 1)) / NBINS;
  const sub = envelope(frame, 'sub');

  return (
    <div style={{ position: 'relative', width: W, height, display: 'flex', gap }}>
      {bins.map((v, i) => {
        // Low bins get the amber (the bass end is the subject of this track);
        // the top of the range cools toward cyan so the row has a direction.
        const k = i / Math.max(1, NBINS - 1);
        const col = k < 0.55 ? AMBER.base : CYAN.base;
        const light = k < 0.55 ? AMBER.light : CYAN.light;
        // A floor of 4% keeps the row present through the quiet bars instead
        // of collapsing to a line and popping back.
        const h = (0.04 + v * 0.96) * height;
        return (
          <div key={i} style={{ width: bw, height, position: 'relative' }}>
            <div
              style={{
                position: 'absolute',
                bottom: 0,
                width: '100%',
                height: h,
                background: `linear-gradient(180deg, ${light}, ${col} 42%, rgba(0,0,0,0) 100%)`,
                boxShadow: `0 0 ${8 + sub * 18}px ${col}`,
                borderRadius: 1,
              }}
            />
            {reflect && (
              <div
                style={{
                  position: 'absolute',
                  top: height,
                  width: '100%',
                  height: h * 0.42,
                  background: `linear-gradient(0deg, transparent, ${col})`,
                  opacity: 0.16,
                  filter: 'blur(2px)',
                  transform: 'scaleY(-1)',
                  transformOrigin: 'top',
                }}
              />
            )}
          </div>
        );
      })}
    </div>
  );
};
