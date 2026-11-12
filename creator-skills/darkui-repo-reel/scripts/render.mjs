// render.mjs: วาด template/scene.html ทีละเฟรมด้วย Playwright แล้วรวมเป็น mp4 พร้อมเพลง
// ใช้: node render.mjs <data.json> <outdir> [--fps 30] [--bgm <ไฟล์เพลง>] [--still 5.5]
//   --still <วินาที>  เรนเดอร์เฟรมเดียวเป็น still.png ไว้ตรวจเลย์เอาต์ ไม่ทำวิดีโอ
import { createRequire } from 'node:module';
import { execFileSync } from 'node:child_process';
import fs from 'node:fs'; import path from 'node:path'; import { fileURLToPath, pathToFileURL } from 'node:url';
const require = createRequire('$PROJECTS/reel-bridge/package.json');
const { chromium } = require('playwright');

const argv = process.argv.slice(2);
const opt = (k, d) => { const i = argv.indexOf('--' + k); return i >= 0 ? argv[i + 1] : d; };
const [dataPath, out] = argv.filter((a, i) => !a.startsWith('--') && !argv[i - 1]?.startsWith('--'));
const fps = Number(opt('fps', '30')), still = opt('still');
const bgm = opt('bgm', '$MEDIA/bgm/Deep Space Sector 9 - Ezra Lipp.mp3');
const FF = '$FFMPEG_BIN/ffmpeg.exe';
const scene = path.join(path.dirname(fileURLToPath(import.meta.url)), '..', 'template', 'scene.html');

const data = JSON.parse(fs.readFileSync(dataPath, 'utf8'));
fs.mkdirSync(out, { recursive: true });
const browser = await chromium.launch();
const page = await browser.newPage({ viewport: { width: 1080, height: 1920 } });
await page.goto(pathToFileURL(scene).href);
await page.evaluate(() => document.fonts.load('700 40px Kanit'));
const total = await page.evaluate((d) => window.setup(d), data);
const grab = async (t) => Buffer.from((await page.evaluate((t) => { window.draw(t); return document.getElementById('c').toDataURL('image/jpeg', 0.92); }, t)).split(',')[1], 'base64');

if (still) {
  fs.writeFileSync(path.join(out, 'still.jpg'), await grab(Number(still)));
  console.log('still', path.join(out, 'still.jpg'), 'total', total.toFixed(1), 's');
  await browser.close(); process.exit(0);
}
const fdir = path.join(out, 'frames'); fs.rmSync(fdir, { recursive: true, force: true }); fs.mkdirSync(fdir);
const N = Math.round(total * fps);
for (let i = 0; i < N; i++) {
  fs.writeFileSync(path.join(fdir, `f${String(i).padStart(5, '0')}.jpg`), await grab(i / fps));
  if (i % (fps * 5) === 0) console.log(`frame ${i}/${N}`);
}
await browser.close();
const mp4 = path.join(out, 'reel.mp4');
execFileSync(FF, ['-loglevel', 'error', '-y', '-framerate', String(fps), '-i', path.join(fdir, 'f%05d.jpg'),
  '-i', bgm, '-filter_complex', `[1:a]atrim=0:${total},afade=t=in:d=0.8,afade=t=out:st=${total - 1.5}:d=1.5,volume=-6dB[a]`,
  '-map', '0:v', '-map', '[a]', '-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-crf', '20', '-preset', 'medium',
  '-c:a', 'aac', '-b:a', '160k', '-shortest', '-movflags', '+faststart', mp4]);
fs.rmSync(fdir, { recursive: true, force: true });
console.log('done', mp4, total.toFixed(1), 's', (fs.statSync(mp4).size / 1e6).toFixed(1), 'MB');
