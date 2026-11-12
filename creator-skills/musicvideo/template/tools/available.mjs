/**
 * Write src/available.json: which backdrop stills actually exist right now.
 *
 * Remotion's <Img> fails the render when a staticFile() is missing, and the
 * stills arrive one at a time from the image bridge, so the scene list cannot
 * assume all twelve are on disk. Re-run this immediately before any render.
 */
import { readdirSync, writeFileSync, statSync } from 'node:fs';
import path from 'node:path';

const DIR = path.join(process.cwd(), 'public', 'img');
let files = [];
try {
  files = readdirSync(DIR)
    .filter((f) => /\.(png|jpe?g|webp)$/i.test(f))
    // A half-written download is worse than a missing one: it renders as a
    // broken frame instead of falling back cleanly.
    .filter((f) => statSync(path.join(DIR, f)).size > 50_000)
    .sort();
} catch {
  files = [];
}
writeFileSync(
  path.join(process.cwd(), 'src', 'available.json'),
  JSON.stringify({ images: files }, null, 2),
);
console.log(`available stills: ${files.length}`);
for (const f of files) console.log('  ' + f);
