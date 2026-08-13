/**
 * Render every composition, then lay a bar-aligned music cut under each one.
 *
 * The music matters as much as the picture here: the video's pose swaps sit on
 * the 113.5 BPM bar grid, so the audio has to be cut on a real downbeat of the
 * track (8.468s, measured with the onset-flux scan) or the whole series feels
 * half a beat out.
 *
 *   node tools/render-all.mjs [ClipId ...]
 */
import { execFileSync } from 'node:child_process';
import { mkdirSync, existsSync } from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const ROOT = path.dirname(path.dirname(fileURLToPath(import.meta.url)));
const OUT = path.join(ROOT, 'out');
mkdirSync(OUT, { recursive: true });

const TRACK = '$MEDIA/bgm/Fiesta Jarocha - Jimena Contreras.mp3';
const DOWNBEAT = 8.468;
const BAR_S = (4 * 60) / 113.5;

/** id -> bars, mirroring src/Root.tsx. */
const CLIPS = {
  Bucket: 4, Boat: 3, Hill: 4, Cargo: 3,
  Domino: 4, Rings: 3, Hourglass: 4, Closer: 4,
};

// Do not shell out to npx here. Bare 'npx' is ENOENT on Windows (it is a .cmd
// shim), and 'npx.cmd' is EINVAL under Node's post-CVE-2024-27980 restriction on
// spawning batch files without a shell. Running the CLI's own JS entry with the
// current node binary sidesteps both and is faster besides.
const REMOTION_CLI = path.join(ROOT, 'node_modules', '@remotion', 'cli', 'remotion-cli.js');
const run = (cmd, args) => execFileSync(cmd, args, { stdio: 'inherit', cwd: ROOT });
const remotion = (args) => run(process.execPath, [REMOTION_CLI, ...args]);

const wanted = process.argv.slice(2);
const ids = wanted.length ? wanted : Object.keys(CLIPS);

for (const [i, id] of ids.entries()) {
  const bars = CLIPS[id];
  if (!bars) throw new Error(`unknown clip: ${id}`);
  const dur = +(bars * BAR_S).toFixed(3);
  const silent = path.join(OUT, `${id}.silent.mp4`);
  const audio = path.join(OUT, `${id}.m4a`);
  const final = path.join(OUT, `${id}.mp4`);

  console.log(`\n[${i + 1}/${ids.length}] ${id} — ${bars} bars / ${dur}s`);
  remotion(['render', 'src/index.ts', id, silent,
    '--codec=h264', '--crf=18', '--concurrency=2', '--log=error']);

  // Each clip starts from a different bar of the track so the series does not
  // sound like the same two seconds eight times over.
  const start = +(DOWNBEAT + i * 2 * BAR_S).toFixed(3);
  run('ffmpeg', ['-y', '-v', 'error', '-ss', String(start), '-t', String(dur), '-i', TRACK,
    '-af', `afade=t=in:st=0:d=0.25,afade=t=out:st=${(dur - 0.35).toFixed(3)}:d=0.35,loudnorm=I=-14:TP=-1.0:LRA=9`,
    '-ar', '48000', '-ac', '2', audio]);

  run('ffmpeg', ['-y', '-v', 'error', '-i', silent, '-i', audio,
    '-map', '0:v', '-map', '1:a', '-c:v', 'copy', '-c:a', 'aac', '-b:a', '192k', '-shortest', final]);

  if (!existsSync(final)) throw new Error(`${id} produced no output`);
  console.log(`      -> out/${id}.mp4`);
}

console.log('\nall clips written to out/');
