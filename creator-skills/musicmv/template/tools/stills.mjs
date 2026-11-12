/**
 * Render one still per scene and tile them into contact sheets.
 *
 * Checking a 3:44 render by watching it is far too slow a loop while poses and
 * prop placement are still moving. A contact sheet shows every scene's worst
 * problems — figures standing inside props, limbs collapsing to a rod, text
 * colliding — in a single look.
 *
 *   node tools/stills.mjs            # all scenes
 *   node tools/stills.mjs 3840 4020  # just these frames
 */
import { execFileSync } from 'node:child_process';
import { mkdirSync, readdirSync, rmSync } from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const ROOT = path.dirname(path.dirname(fileURLToPath(import.meta.url)));
const OUT = path.join(ROOT, 'out', 'stills');

/** Mid-scene frames, one per entry in Mv.tsx's SCHEDULE. */
const SHOTS = [
  [240, 'Title'], [690, 'NightBugs'], [1020, 'ReadRepo'], [1350, 'Count'],
  [1710, 'Million'], [2130, 'WholeWorld'], [2430, 'Contract'], [2595, 'Photo'],
  [3798, 'RapCode'], [3885, 'RapTests'], [3972, 'RapPdf'], [4059, 'RapChart'],
  [4146, 'RapConnect'], [4230, 'RapSearch'], [4350, 'RapAgents'], [4494, 'RapSkill'],
  [4581, 'RapThink'], [4653, 'RapLang'], [4740, 'RapArtifact'], [4842, 'RapAlways'],
  [4980, 'RapHuman'], [5250, 'BridgeUnsure'], [5580, 'BridgeTrust'], [5940, 'Final'],
  [6300, 'WalkOff'], [6570, 'Outro'],
];

// Bare `npx` is ENOENT on Windows and `npx.cmd` is EINVAL under Node's
// post-CVE-2024-27980 block on spawning batch files. Run the CLI's JS entry.
const CLI = path.join(ROOT, 'node_modules', '@remotion', 'cli', 'remotion-cli.js');
const remotion = (args) => execFileSync(process.execPath, [CLI, ...args], { stdio: 'inherit', cwd: ROOT });

const only = process.argv.slice(2).map(Number);
const shots = only.length ? SHOTS.filter(([f]) => only.includes(f)) : SHOTS;

rmSync(OUT, { recursive: true, force: true });
mkdirSync(OUT, { recursive: true });

for (const [frame, name] of shots) {
  console.log(`\n--- ${name} @ frame ${frame}`);
  remotion(['still', 'src/index.ts', 'Mv', path.join(OUT, `${String(frame).padStart(5, '0')}-${name}.png`),
    `--frame=${frame}`, '--scale=0.5', '--log=error']);
}

// Tile into sheets of 6 (3 across) so each panel stays big enough to judge.
const files = readdirSync(OUT).filter((f) => f.endsWith('.png')).sort();
for (let i = 0; i < files.length; i += 6) {
  const group = files.slice(i, i + 6);
  const sheet = path.join(ROOT, 'out', `sheet${Math.floor(i / 6) + 1}.png`);
  execFileSync('ffmpeg', [
    '-y', '-v', 'error',
    ...group.flatMap((f) => ['-i', path.join(OUT, f)]),
    '-filter_complex', `${group.map((_, k) => `[${k}]scale=360:-1[s${k}]`).join(';')};` +
      `${group.map((_, k) => `[s${k}]`).join('')}xstack=inputs=${group.length}:layout=${
        group.map((_, k) => `${(k % 3) === 0 ? '0' : (k % 3) === 1 ? 'w0' : 'w0+w1'}_${k < 3 ? '0' : 'h0'}`).join('|')
      }`,
    '-frames:v', '1', sheet,
  ], { stdio: 'inherit' });
  console.log(`-> ${sheet}`);
}
