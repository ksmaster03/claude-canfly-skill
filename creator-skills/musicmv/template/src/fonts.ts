import { SARABUN_REGULAR, SARABUN_SEMIBOLD } from './fonts-data';

/**
 * Sarabun, injected as CSS with NO delayRender at all.
 *
 * Thai has to come from a real Thai face — a Latin fallback drops the tone marks
 * onto the wrong vowels or loses them entirely.
 *
 * Three ways of doing this were tried and each killed a full-length render while
 * stills and short frame ranges passed:
 *  1. Loading over staticFile() left delayRender hanging.
 *  2. Inlining the bytes as data URIs and calling `new FontFace(...).load()`
 *     still hung — the promise never settled in a freshly spawned render tab.
 *  3. Guarding that with `Promise.race([…, setTimeout(5000)])` ALSO hung: the
 *     run died having never fired a 5-second timer, because the tab Remotion
 *     respawns mid-render is offscreen and Chromium freezes its timers.
 *     Anything that waits on the tab's own event loop can be starved for longer
 *     than the delayRender timeout.
 *
 * So nothing is awaited. The faces are plain CSS carrying their own bytes as
 * data URIs — no network, no promise, nothing to hang on — and the probe below
 * forces the browser to resolve them synchronously during this module's
 * execution, before React has rendered a single frame.
 *
 * Related: a delayRender timeout naming a font is often not about fonts at all.
 * It is what Remotion reports when the render tab dies, and the usual cause is
 * memory — see the note on the reflection layer in Stage.tsx.
 */
export const THAI = "'Sarabun', 'Leelawadee UI', 'Segoe UI', sans-serif";

const css = `
@font-face {
  font-family: 'Sarabun';
  font-style: normal;
  font-weight: 400;
  font-display: block;
  src: url(${SARABUN_REGULAR}) format('truetype');
}
@font-face {
  font-family: 'Sarabun';
  font-style: normal;
  font-weight: 600;
  font-display: block;
  src: url(${SARABUN_SEMIBOLD}) format('truetype');
}
`;

const style = document.createElement('style');
style.textContent = css;
document.head.appendChild(style);

/**
 * Force both weights to resolve now.
 *
 * Reading offsetWidth flushes pending style and layout, and laying out real Thai
 * text in each weight is what makes the engine pull the face in. With the bytes
 * already in the document there is nothing to fetch, so this completes within
 * this synchronous block rather than at some later, throttled tick.
 */
const probe = document.createElement('div');
probe.setAttribute(
  'style',
  'position:absolute;left:-9999px;top:0;visibility:hidden;white-space:pre;contain:strict;',
);
for (const weight of [400, 600]) {
  const span = document.createElement('span');
  span.setAttribute('style', `font:${weight} 46px Sarabun`);
  // Real Thai with tone marks: that is what forces the face to actually load.
  span.textContent = 'ทดสอบวรรณยุกต์ไทย';
  probe.appendChild(span);
}
if (document.body) {
  document.body.appendChild(probe);
  void probe.offsetWidth;
  probe.remove();
} else {
  // Module ran before <body> existed; the CSS above is still live, so the faces
  // are available by the time anything is painted.
  document.addEventListener('DOMContentLoaded', () => {
    document.body.appendChild(probe);
    void probe.offsetWidth;
    probe.remove();
  });
}
