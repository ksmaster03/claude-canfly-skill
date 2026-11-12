// ใช้: node bg_to_png.cjs <proj>   แปลง <proj>/bg.html เป็น bg.png (1080x1920) และ cover.jpg
// รันด้วย NODE_PATH=$PROJECTS/reel-bridge/node_modules (ใช้ playwright ของ reel-bridge)
const path = require('path');
const { chromium } = require('playwright');
const proj = path.resolve(process.argv[2] || '.');
(async () => {
  const b = await chromium.launch();
  const p = await b.newPage({ viewport: { width: 1080, height: 1920 } });
  await p.goto('file:///' + path.join(proj, 'bg.html').split(path.sep).join('/'));
  await p.evaluate(() => document.fonts.ready);
  await p.waitForTimeout(500);
  await p.screenshot({ path: path.join(proj, 'bg.png') });
  await p.screenshot({ path: path.join(proj, 'cover.jpg'), type: 'jpeg', quality: 90 });
  await b.close();
  console.log('ok bg.png + cover.jpg');
})();
