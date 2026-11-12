// Frame rate of a page on plain Chrome (no Playwright launch flags). Connects over CDP only to read numbers.
//   node probe.mjs <label> <front|tile|behind> <url> [extra chrome flags...]
//   front = topmost and focused (real stage state, takes the screen) · tile = small corner window, topmost, no focus · behind = wherever it opens
//   env: POS=x,y WIN=w,h SECS=5 READY='js expr, wait until truthy' READ='js expr, extra numbers to report'
import { createRequire } from 'module';
import { spawn, execFileSync } from 'child_process';
import { fileURLToPath } from 'url';
import path from 'path';
import fs from 'fs';
import os from 'os';
const BRIDGE = process.env.CHATGPT_BRIDGE || '.';   // folder whose node_modules has playwright
const require = createRequire(path.resolve(BRIDGE) + '/');
const { chromium } = require('playwright');
const [label, mode, url, ...extra] = process.argv.slice(2);
const HERE = path.dirname(fileURLToPath(import.meta.url));
const CHROME = process.env.CHROME_PATH || 'C:/Program Files/Google/Chrome/Application/chrome.exe';
const PROFILE = path.join(os.tmpdir(), `fps-probe-${process.pid}`);
const CDP = 9333 + (process.pid % 200), SECS = Number(process.env.SECS || 5);
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
const ps = (f, ...a) => execFileSync('powershell', ['-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', path.join(HERE, f), ...a], { encoding: 'utf8' }).trim();
spawn(CHROME, [`--user-data-dir=${PROFILE}`, '--no-first-run', '--no-default-browser-check', '--autoplay-policy=no-user-gesture-required',
  `--window-position=${process.env.POS || '1000,620'}`, `--window-size=${process.env.WIN || '520,290'}`, `--remote-debugging-port=${CDP}`, ...extra, `--app=${url}`],
  { stdio: 'ignore', detached: true }).unref();
let browser, out = { label, mode, extra: extra.join(' ') };
try {
  for (let i = 0; i < 40 && !browser; i++) { try { browser = await chromium.connectOverCDP(`http://127.0.0.1:${CDP}`); } catch { await sleep(250); } }
  let page = null;
  for (let i = 0; i < 40 && !page; i++) { page = browser.contexts().flatMap((c) => c.pages()).find((p) => !p.url().startsWith('chrome') && p.url() !== 'about:blank') || null; if (!page) await sleep(250); }
  await page.waitForFunction(() => document.readyState === 'complete', null, { timeout: 15000 });
  if (process.env.READY) await page.waitForFunction(process.env.READY, null, { timeout: 40000 });
  const title = (await page.title()).slice(0, 16);
  await sleep(800);
  if (mode === 'tile') out.tile = ps('tile.ps1', '-Title', title);
  if (mode === 'front') out.front = ps('topmost.ps1', '-Title', title);
  await sleep(1200);
  const d = await page.evaluate((secs) => new Promise((res) => {
    const iv = []; let last = 0; const t0 = performance.now();
    const done = () => res({ iv, vis: document.visibilityState, dpr: devicePixelRatio, inner: `${innerWidth}x${innerHeight}` });
    const f = (t) => { if (last) iv.push(t - last); last = t; if (performance.now() - t0 < secs * 1000) requestAnimationFrame(f); else done(); };
    requestAnimationFrame(f); setTimeout(done, (secs + 2) * 1000);
  }), SECS);
  const s = d.iv.slice().sort((a, b) => a - b);
  Object.assign(out, { fps: +(s.length / SECS).toFixed(1), med: s.length ? +s[Math.floor(s.length / 2)].toFixed(1) : null, max: s.length ? +s[s.length - 1].toFixed(1) : null, vis: d.vis, inner: d.inner, dpr: d.dpr });
  if (process.env.READ) out.read = await page.evaluate(process.env.READ);
  out.ver = browser.version();
} catch (e) { out.err = String(e).slice(0, 200); }
try { const s = await browser.newBrowserCDPSession(); await s.send('Browser.close'); } catch { /* closed */ }
await sleep(500);
try { fs.rmSync(PROFILE, { recursive: true, force: true }); } catch { /* chrome may still hold it */ }
console.log(JSON.stringify(out));
