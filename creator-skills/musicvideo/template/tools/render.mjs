/**
 * Render a composition in chunks, join, and mux the mastered track under it.
 *
 *   node tools/render.mjs MvWide  mv-wide-1080p.mp4
 *   node tools/render.mjs MvTall  hook.mp4 --from=6072 --to=6962
 *
 * Chunks exist because a single multi-thousand-frame render on this machine
 * dies partway through with a delayRender timeout, and the failure point moves
 * when unrelated things change -- a browser accumulating, not a bad frame. The
 * reflections redraw the rig through a CSS blur, so frames are expensive. A
 * fresh browser per chunk sidesteps it and a failure costs one chunk.
 */
import { execFileSync } from 'node:child_process';
import { mkdirSync, existsSync, statSync, writeFileSync, rmSync, readFileSync } from 'node:fs';
import path from 'node:path';

const [COMP, OUTNAME] = process.argv.slice(2);
if (!COMP || !OUTNAME) throw new Error('usage: render.mjs <CompId> <out.mp4> [--from=N --to=N]');

const ROOT = process.cwd();
const OUT = path.join(ROOT, 'out');
const TRACK = path.join(ROOT, 'audio', 'master.wav');
if (!existsSync(TRACK)) throw new Error('track missing: ' + TRACK);

const arg = (f, d) => {
  const a = process.argv.find((x) => x.startsWith('--' + f + '='));
  return a ? Number(a.split('=')[1]) : d;
};
const FPS = 30;
const CHUNK = arg('chunk', 900);
const FROM = arg('from', 0);
// Frame count comes from the measurement, not a literal. It was hardcoded to
// one song's 8910 and carried to the next track, which runs 8998 -- without an
// explicit --to that silently drops the last 88 frames of the outro.
const FEATURES = JSON.parse(readFileSync(path.join(ROOT, 'src', 'features.json'), 'utf8'));
const TOTAL = FEATURES.frames;
const TO = arg('to', TOTAL - 1);
const TAG = FROM === 0 && TO === TOTAL - 1 ? COMP : COMP + '-' + FROM + '-' + TO;
const PARTS = path.join(OUT, 'parts-' + TAG);
mkdirSync(PARTS, { recursive: true });

// Bare npx is ENOENT on Windows and npx.cmd is EINVAL under Node's block on
// spawning batch files. Call the CLI's JS entry point directly.
const CLI = path.join(ROOT, 'node_modules', '@remotion', 'cli', 'remotion-cli.js');
const run = (cmd, args) => execFileSync(cmd, args, { stdio: 'inherit', cwd: ROOT });

/**
 * A cached chunk counts only if it holds every frame it was asked for.
 *
 * Checking the file size instead let a chunk that was killed mid-write pass as
 * complete, which would have been spliced into the finished video silently.
 */
const framesIn = (file) => {
  try {
    const out = execFileSync('ffprobe', ['-v', 'error', '-count_frames',
      '-select_streams', 'v:0', '-show_entries', 'stream=nb_read_frames',
      '-of', 'csv=p=0', file], { encoding: 'utf8' });
    return parseInt(out.trim(), 10) || 0;
  } catch { return 0; }
};

const parts = [];
for (let start = FROM, i = 0; start <= TO; start += CHUNK, i++) {
  const end = Math.min(start + CHUNK - 1, TO);
  const want = end - start + 1;
  const part = path.join(PARTS, 'p' + String(i).padStart(2, '0') + '.mp4');
  parts.push(part);
  if (existsSync(part) && framesIn(part) === want) {
    console.log('[' + i + '] ' + start + '-' + end + ' cached (' + want + ' frames)');
    continue;
  }
  if (existsSync(part)) { console.log('[' + i + '] incomplete, re-rendering'); rmSync(part); }
  console.log('[' + i + '] frames ' + start + '-' + end);
  run(process.execPath, [CLI, 'render', 'src/index.ts', COMP, part,
    '--codec=h264', '--crf=17', '--concurrency=2',
    '--frames=' + start + '-' + end, '--log=error']);
}

// ffmpeg's concat demuxer wants forward slashes. The separator, quote and
// newline are built from char codes: written as escapes they were rewritten in
// transit twice, each time producing a file that would not parse.
const BS = String.fromCharCode(92);
const Q = String.fromCharCode(39);
const NL = String.fromCharCode(10);
const fwd = (x) => x.split(BS).join('/');
const list = path.join(PARTS, 'list.txt');
writeFileSync(list, parts.map((p) => 'file ' + Q + fwd(p) + Q).join(NL));

const silent = path.join(OUT, TAG + '.silent.mp4');
// Same encoder and settings for every chunk, so this concatenates without a
// re-encode.
run('ffmpeg', ['-y', '-v', 'error', '-f', 'concat', '-safe', '0', '-i', list,
  '-c', 'copy', silent]);

const total = TO - FROM + 1;
const got = framesIn(silent);
if (got !== total) throw new Error('joined video has ' + got + ' frames, expected ' + total);

const final = path.join(OUT, OUTNAME);
// Audio starts at the same instant as the first rendered frame, so a partial
// range needs the track seeked to match. No -shortest: AAC padding made the
// muxer cut 16 frames off the full render even though picture and track
// differ by 4 ms.
const aArgs = FROM === 0 ? ['-i', TRACK]
  : ['-ss', String(FROM / FPS), '-t', String(total / FPS), '-i', TRACK];
run('ffmpeg', ['-y', '-v', 'error', '-i', silent, ...aArgs,
  '-map', '0:v', '-map', '1:a', '-c:v', 'copy', '-c:a', 'aac', '-b:a', '320k',
  '-movflags', '+faststart', final]);

rmSync(list, { force: true });
const finalFrames = framesIn(final);
console.log('-> ' + final + '  ' + (statSync(final).size / 1e6).toFixed(1) + ' MB  '
  + finalFrames + ' frames' + (finalFrames === total ? '' : '  *** FRAME COUNT WRONG ***'));
