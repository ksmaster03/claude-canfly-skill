/**
 * build-book.mjs — TEMPLATE ของสกิล /ebook · ประกอบหนังสือเป็น 3 ฟอร์แมต:
 *   dist/<slug>.html  (self-contained — ฟอนต์+ภาพฝัง base64)
 *   dist/<slug>.pdf   (render จาก HTML เดียวกันด้วย Chromium/print_pdf.mjs)
 *   dist/<slug>.epub  (pandoc + ฝังฟอนต์ Sarabun + cover)
 *
 * วิธีใช้: คัดลอกไฟล์นี้ไปไว้ที่รากโปรเจกต์ แล้วแก้ค่าคงที่ด้านล่าง
 *          (DIR / SLUG / TITLE / SUB1 / SUB2 / AUTHOR / CREDIT / จำนวนบท) + สีใน :root และ .cover
 *
 * ต้องมี: raw/chNN.md, fonts/Sarabun-*.ttf, (ออปชัน) images/cover.* + images/chNN.*
 * ต้องการ: pandoc ใน PATH, playwright + chromium ที่ $CHATGPT_BRIDGE
 *          (เช็กก่อน: ls ~/AppData/Local/ms-playwright/ — ไม่มีให้ npx playwright install chromium)
 *
 * ทนไฟล์หาย: บทที่ยังไม่มีจะข้าม ภาพที่ยังไม่มีก็ข้าม → build ทดสอบได้ตั้งแต่เขียนไม่ครบ
 * ภาพ: เลือก .jpg ก่อน .png เสมอ — ต้องรัน scripts/optimize-images.py ก่อน ไม่งั้น PDF บวม 10 เท่า
 */
import { readFile, writeFile, mkdir } from 'node:fs/promises';
import { existsSync, readFileSync } from 'node:fs';
import { execFile } from 'node:child_process';
import { promisify } from 'node:util';
import path from 'node:path';

const pexec = promisify(execFile);
const DIR = '$WORK/<slug>-ebook';
const RAW = path.join(DIR, 'raw');
const IMG = path.join(DIR, 'images');
const DIST = path.join(DIR, 'dist');
const FONTS = path.join(DIR, 'fonts');

const SLUG = '<slug>';                       // ชื่อไฟล์ผลลัพธ์ dist/<slug>.pdf
const TITLE = '<ชื่อเล่ม>';
const SUB1 = '<ชื่อรอง — ขึ้นปกและ metadata>';
const SUB2 = '<ชื่อรองบรรทัดสอง — ขอบเขตของเล่ม>';
const AUTHOR = '<ชื่อผู้เขียน · แบรนด์>';
const CREDIT = '<ชื่อผู้เขียน · แบรนด์>';   // โผล่ที่ .bookbar / .bookfoot / header+footer ของ PDF
// <-- แก้จำนวนบทตรงนี้
const CHAPTERS = Array.from({ length: 14 }, (_, i) => `ch${String(i + 1).padStart(2, '0')}`);

const b64 = (p) => readFileSync(p).toString('base64');
const fontFace = (w, style, weight) =>
  `@font-face{font-family:'Sarabun';font-style:${style};font-weight:${weight};` +
  `src:url(data:font/ttf;base64,${b64(path.join(FONTS, `Sarabun-${w}.ttf`))}) format('truetype');}`;

const FONT_CSS = [
  fontFace('Regular', 'normal', 400),
  fontFace('Medium', 'normal', 500),
  fontFace('SemiBold', 'normal', 600),
  fontFace('Bold', 'normal', 700),
  fontFace('ExtraBold', 'normal', 800),
].join('\n');

const CSS = `
${FONT_CSS}
:root{--ink:#141b26;--muted:#586274;--accent:#0f6fd6;--accent2:#b45309;--bg:#ffffff;--soft:#f4f6f9;--line:#e2e6ec;--code:#0d1626;}
*{box-sizing:border-box;}
html{-webkit-print-color-adjust:exact;print-color-adjust:exact;}
body{font-family:'Sarabun',-apple-system,'Segoe UI',Tahoma,sans-serif;color:var(--ink);line-height:1.72;font-size:16.5px;margin:0;background:var(--bg);}
.wrap{max-width:760px;margin:0 auto;padding:0 26px;}
h1,h2,h3{line-height:1.32;font-weight:800;letter-spacing:-.01em;}
h1{font-size:2.0rem;margin:0 0 .3em;color:var(--ink);}
h2{font-size:1.34rem;margin:1.9em 0 .5em;padding-bottom:.28em;border-bottom:2px solid var(--line);}
h3{font-size:1.08rem;margin:1.4em 0 .35em;color:var(--accent2);font-weight:700;}
p{margin:.55em 0;}
a{color:var(--accent);word-break:break-word;}
strong{font-weight:700;}
ul,ol{padding-left:1.35em;margin:.5em 0;}
li{margin:.2em 0;}
code{font-family:'Cascadia Code',Consolas,'Courier New',monospace;background:#eaeef4;color:#0b5ba8;padding:.08em .38em;border-radius:5px;font-size:.85em;}
pre{background:var(--code);color:#e6edf3;padding:14px 16px;border-radius:10px;overflow-x:auto;font-size:.78rem;line-height:1.55;margin:1em 0;}
pre code{background:none;color:inherit;padding:0;font-size:1em;}
blockquote{margin:1em 0;padding:.6em 1em;border-left:4px solid var(--accent2);background:var(--soft);border-radius:0 8px 8px 0;color:var(--muted);}
blockquote strong{color:var(--ink);}
table{border-collapse:collapse;width:100%;margin:1em 0;font-size:.9em;}
th,td{border:1px solid var(--line);padding:7px 10px;text-align:left;vertical-align:top;}
th{background:var(--soft);font-weight:700;}
hr{border:none;border-top:1px solid var(--line);margin:2em 0;}
.bookbar{position:sticky;top:0;z-index:20;background:var(--bg);border-bottom:1px solid var(--line);
  color:var(--muted);font-size:.72rem;letter-spacing:.14em;text-transform:uppercase;text-align:center;padding:7px 12px;}
.bookfoot{border-top:1px solid var(--line);margin-top:3em;padding:34px 0 46px;text-align:center;
  color:var(--muted);font-size:.9rem;font-weight:600;}
.bookfoot span{display:inline-block;margin-top:6px;font-weight:400;font-size:.82rem;letter-spacing:.06em;color:var(--accent);}
.chapimg{width:100%;border-radius:14px;margin:.6em 0 1.2em;box-shadow:0 8px 30px rgba(15,23,42,.14);}
/* cover */
.cover{min-height:100vh;display:flex;flex-direction:column;justify-content:center;align-items:center;text-align:center;
  background:linear-gradient(160deg,#07162b 0%,#0d2a4d 55%,#12385f 100%);color:#fff;padding:48px 30px;page-break-after:always;}
.cover img{width:min(360px,72%);border-radius:18px;box-shadow:0 20px 60px rgba(0,0,0,.5);margin-bottom:26px;}
.cover .kicker{letter-spacing:.32em;font-size:.8rem;color:#f5b942;text-transform:uppercase;margin-bottom:10px;}
.cover h1{font-size:3.2rem;color:#fff;margin:.1em 0;text-shadow:0 3px 20px rgba(0,0,0,.4);}
.cover .s1{font-size:1.12rem;color:#dceaff;font-weight:600;margin-top:.4em;max-width:560px;}
.cover .s2{font-size:.92rem;color:#9db4d2;max-width:540px;margin:.9em auto 0;line-height:1.6;}
.cover .by{margin-top:34px;font-size:.9rem;color:#7d92b0;letter-spacing:.05em;}
/* toc */
.toc{page-break-after:always;padding:44px 0 10px;}
.toc h2{border:none;font-size:1.7rem;margin-bottom:.6em;}
.toc ol{list-style:none;padding:0;counter-reset:c;}
.toc li{counter-increment:c;display:flex;gap:12px;padding:9px 0;border-bottom:1px dashed var(--line);align-items:baseline;}
.toc li::before{content:counter(c,decimal-leading-zero);color:var(--accent);font-weight:800;min-width:1.8em;}
.toc a{color:var(--ink);text-decoration:none;font-weight:600;}
/* chapter */
.chapter{page-break-before:always;padding-top:20px;}
.chapter .num{display:inline-block;font-size:.78rem;font-weight:800;letter-spacing:.2em;color:#fff;background:var(--accent);
  padding:4px 12px;border-radius:999px;margin-bottom:12px;text-transform:uppercase;}
@media print{
  body{font-size:11.6pt;}
  .wrap{max-width:none;padding:0;}
  .cover{min-height:auto;height:250mm;}
  pre{font-size:8.0pt;white-space:pre-wrap;word-break:break-word;}
  h2,h3{page-break-after:avoid;}
  pre,table,blockquote,.chapimg{page-break-inside:avoid;}
  /* กันย่อหน้าตกหน้า: ห้ามทิ้งบรรทัดโดด ๆ ไว้ท้ายหน้าหรือต้นหน้า */
  p,li{orphans:3;widows:3;}
  .bookbar{display:none;}   /* PDF ใช้ header จริงในขอบกระดาษแทน */
  a{color:var(--ink);}
}
@media (prefers-color-scheme:dark){
  :root{--ink:#e7ebf2;--muted:#9aa3b2;--bg:#0f1420;--soft:#171d2b;--line:#283042;}
  body{background:var(--bg);}
  code{background:#1b2233;color:#7cc4ff;}
  th{background:#171d2b;}
}
`;

async function pandocFragment(mdPath) {
  const { stdout } = await pexec('pandoc', [mdPath, '-f', 'markdown-tex_math_dollars-yaml_metadata_block',
    '-t', 'html5', '--no-highlight', '--wrap=none'], { maxBuffer: 1 << 26 });
  return stdout;
}

// ใช้ .jpg ที่บีบแล้วก่อน (ไฟล์เล็กกว่า PNG ~10 เท่า) แล้วค่อย fallback เป็น .png
const pickImg = (id) => {
  for (const [ext, mime] of [['jpg', 'image/jpeg'], ['png', 'image/png']]) {
    const p = path.join(IMG, `${id}.${ext}`);
    if (existsSync(p)) return { p, mime };
  }
  return null;
};

const imgTag = (id) => {
  const f = pickImg(id);
  return f ? `<img class="chapimg" src="data:${f.mime};base64,${b64(f.p)}" alt="">` : '';
};

async function main() {
  await mkdir(DIST, { recursive: true });

  const titles = [];
  const frags = [];
  for (const id of CHAPTERS) {
    const f = path.join(RAW, `${id}.md`);
    if (!existsSync(f)) { console.warn('SKIP (missing)', f); titles.push(id); frags.push(''); continue; }
    const md = await readFile(f, 'utf-8');
    const first = md.split('\n').find((l) => l.trim()) || id;
    titles.push(first.replace(/^#+\s*/, '').trim());
    frags.push(await pandocFragment(f));
  }

  const toc = titles.map((t, i) => `<li><a href="#ch${i + 1}">${t}</a></li>`).join('\n');

  const chaptersHtml = frags.map((frag, i) => {
    const body = frag.replace(/^\s*<h1[^>]*>[\s\S]*?<\/h1>/, '');
    return `<section class="chapter" id="ch${i + 1}"><div class="wrap">
      <span class="num">บทที่ ${i + 1}</span>
      <h1>${titles[i]}</h1>
      ${imgTag(CHAPTERS[i])}
      ${body}
    </div></section>`;
  }).join('\n');

  const cf = pickImg('cover');
  const coverImg = cf ? `<img src="data:${cf.mime};base64,${b64(cf.p)}" alt="ปกหนังสือ">` : '';

  const html = `<!doctype html><html lang="th"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>${TITLE} — ${SUB1}</title><style>${CSS}</style></head><body>
<div class="bookbar">${CREDIT}</div>
<section class="cover">
  ${coverImg}
  <div class="kicker">E-BOOK · 2026</div>
  <h1>${TITLE}</h1>
  <div class="s1">${SUB1}</div>
  <div class="s2">${SUB2}</div>
  <div class="by">โดย ${AUTHOR}</div>
</section>
<nav class="toc"><div class="wrap"><h2>สารบัญ</h2><ol>${toc}</ol></div></nav>
${chaptersHtml}
<footer class="bookfoot"><div class="wrap">${TITLE}<br><span>${CREDIT}</span></div></footer>
</body></html>`;

  const htmlOut = path.join(DIST, `${SLUG}.html`);
  await writeFile(htmlOut, html, 'utf-8');
  console.log('WROTE', htmlOut);

  const fileUrl = 'file:///' + htmlOut.replace(/\\/g, '/');
  const pdfOut = path.join(DIST, `${SLUG}.pdf`);
  try {
    await pexec('node', ['$CHATGPT_BRIDGE/print_pdf.mjs', fileUrl, pdfOut,
      `${TITLE} · ${CREDIT}`, CREDIT], { maxBuffer: 1 << 26 });
    console.log('WROTE', pdfOut);
  } catch (e) { console.error('PDF failed:', e.message); }

  const meta = `---\ntitle: "${TITLE}"\nsubtitle: "${SUB1}"\nauthor: "${AUTHOR}"\nlang: th\n---\n\n`;
  const parts = [];
  for (const id of CHAPTERS) {
    const f = path.join(RAW, `${id}.md`);
    if (existsSync(f)) parts.push(await readFile(f, 'utf-8'));
  }
  const bookMdPath = path.join(DIR, 'book.md');
  await writeFile(bookMdPath, meta + parts.join('\n\n'), 'utf-8');
  const epubOut = path.join(DIST, `${SLUG}.epub`);
  const epubArgs = [bookMdPath, '-o', epubOut, '--toc', '--toc-depth=2',
    '--metadata', `title=${TITLE}`, '--metadata', `author=${AUTHOR}`, '--metadata', 'lang=th',
    '--epub-embed-font=fonts/Sarabun-Regular.ttf', '--epub-embed-font=fonts/Sarabun-Bold.ttf'];
  const epubCover = pickImg('cover');   // .jpg ที่ใส่ชื่อเรื่องแล้วมาก่อน .png ดิบ
  if (epubCover) epubArgs.push(`--epub-cover-image=${epubCover.p}`);
  try {
    await pexec('pandoc', epubArgs, { cwd: DIR, maxBuffer: 1 << 26 });
    console.log('WROTE', epubOut);
  } catch (e) { console.error('EPUB failed:', e.message); }

  console.log('DONE');
}
main().catch((e) => { console.error('FATAL', e); process.exit(1); });
