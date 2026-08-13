import { continueRender, delayRender, staticFile } from 'remotion';

/**
 * Sarabun, loaded from public/fonts before the first frame is captured.
 *
 * Thai has to come from a real Thai face — a Latin fallback drops the tone marks
 * onto the wrong vowels or loses them entirely. delayRender holds the render
 * until the faces are in document.fonts, so no frame is ever captured mid-swap.
 */
export const THAI = "'Sarabun', 'Leelawadee UI', 'Segoe UI', sans-serif";

const load = (weight: number, file: string) => {
  // Stills clear this in well under a second, but a full render runs several
  // headless tabs against the same static server and the default 28s timeout
  // does get hit. Fonts are cheap to wait for and fatal to skip.
  const handle = delayRender(`font ${file}`, { timeoutInMilliseconds: 120000 });
  const face = new FontFace('Sarabun', `url(${staticFile(`fonts/${file}`)}) format('truetype')`, {
    weight: String(weight),
  });
  face
    .load()
    .then((loaded) => {
      // FontFaceSet#add is missing from this TS DOM lib; the browser has it.
      (document.fonts as unknown as { add: (f: FontFace) => void }).add(loaded);
      continueRender(handle);
    })
    .catch((err) => {
      // Never fail the render over a font; fall back and say so.
      console.error(`[fonts] ${file} failed to load`, err);
      continueRender(handle);
    });
};

load(400, 'Sarabun-Regular.ttf');
load(600, 'Sarabun-SemiBold.ttf');
