/**
 * Render the video in chunks, join them, and mux the real track under it.
 *
 * Why chunks: a single 6,738-frame render died twice at around frame 1,250 with
 * "A delayRender() was called but not cleared after 118000ms" pointing at the
 * font loader — but a still at frame 1,350 rendered fine, and the failure moved
 * when the font loading strategy changed. That pattern is a browser tab running
 * out of room after ~1,200 frames, not a bad frame: the reflection layer is the
 * whole stage drawn a second time through a CSS blur, so each frame is
 * expensive and something accumulates. Rendering ranges gives every chunk a
 * fresh browser, which sidesteps the accumulation entirely and also means a
 * failure costs one chunk instead of the whole run.
 *
 *   node tools/render-mv.mjs [--chunk=1000] [--scale=1]
 */
import { execFileSync } from 'node:child_process';
import { mkdirSync, existsSync, statSync, writeFileSync, rmSync } from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const ROOT = path.dirname(path.dirname(fileURLToPath(import.meta.url)));
const OUT = path.join(ROOT, 'out');
const PARTS = path.join(OUT, 'parts');
mkdirSync(PARTS, { recursive: true });

/** Take 2 — the only one of the pair where Suno kept every section tag; take 1
 *  swallowed Verse 1 into the intro, which would have left a scene with no lyric. */
const TRACK = '$PROJECTS/claude-song/audio/take2-6c76f142.mp3';
/** Must match SEC_F(SONG_S) in src/theme.ts. */
const TOTAL_FRAMES = 6738;

const num = (flag, def) => {
  const a = process.argv.find((x) => x.startsWith(`--${flag}=`));
  return a ? Number(a.split('=')[1]) : def;
};
const CHUNK = num('chunk', 1000);
const scaleArg = `--scale=${num('scale', 1)}`;

// Bare `npx` is ENOENT on Windows and `npx.cmd` is EINVAL under Node's
// post-CVE-2024-27980 block on spawning batch files. Call the CLI's JS entry.
const CLI = path.join(ROOT, 'node_modules', '@remotion', 'cli', 'remotion-cli.js');
const run = (cmd, args) => execFileSync(cmd, args, { stdio: 'inherit', cwd: ROOT });

if (!existsSync(TRACK)) throw new Error(`track missing: ${TRACK}`);

const parts = [];
for (let start = 0, i = 0; start < TOTAL_FRAMES; start += CHUNK, i++) {
  const end = Math.min(start + CHUNK - 1, TOTAL_FRAMES - 1);
  const part = path.join(PARTS, `part${String(i).padStart(2, '0')}.mp4`);
  parts.push(part);
  if (existsSync(part)) {
    console.log(`\n[${i}] frames ${start}-${end} — already rendered, skipping`);
    continue;
  }
  console.log(`\n[${i}] frames ${start}-${end}`);
  run(process.execPath, [CLI, 'render', 'src/index.ts', 'Mv', part,
    '--codec=h264', '--crf=18', '--concurrency=2', `--frames=${start}-${end}`,
    scaleArg, '--log=error']);
}

console.log('\njoining chunks...');
const list = path.join(PARTS, 'list.txt');
writeFileSync(list, parts.map((p) => `file '${p.replace(/\\/g, '/')}'`).join('\n'));
const silent = path.join(OUT, 'mv.silent.mp4');
// Every chunk came out of the same encoder with the same settings, so the
// streams concatenate without a re-encode.
run('ffmpeg', ['-y', '-v', 'error', '-f', 'concat', '-safe', '0', '-i', list,
  '-c', 'copy', silent]);

console.log('muxing audio...');
const final = path.join(OUT, 'phim-ma-si.mp4');
// Picture is locked to the song from the first frame, so the audio goes on at
// offset zero — any -ss here would slide the track out of phase with the cuts.
// Suno masters its output already; a second loudnorm pass would only pump it.
run('ffmpeg', ['-y', '-v', 'error', '-i', silent, '-i', TRACK,
  '-map', '0:v', '-map', '1:a', '-c:v', 'copy', '-c:a', 'aac', '-b:a', '192k',
  '-shortest', '-movflags', '+faststart', final]);

rmSync(list, { force: true });
const mb = (statSync(final).size / 1e6).toFixed(1);
console.log(`\n-> ${final}  (${mb} MB)`);
