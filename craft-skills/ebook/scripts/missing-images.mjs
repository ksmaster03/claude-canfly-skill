/**
 * missing-images.mjs <project-dir> — สร้าง prompts-missing.json จากภาพที่ยังไม่มี
 *
 * chatgpt-batch ล้มบางรูปเป็นเรื่องปกติ (เน็ตสะดุด / โมเดลไม่ยอมออกภาพ)
 * สคริปต์นี้กรอง prompts.json เหลือเฉพาะ id ที่ยังไม่มีไฟล์ใน images/
 * แล้วสั่ง:
 *   cd /d/Project/chatgpt-bridge
 *   node chatgpt-batch.mjs <proj>/prompts-missing.json <proj>/images
 * วนจนครบ
 */
import { existsSync, readFileSync, writeFileSync } from 'node:fs';
import path from 'node:path';

const proj = process.argv[2] || '.';
const promptsPath = path.join(proj, 'prompts.json');
if (!existsSync(promptsPath)) {
  console.error(`ไม่พบ ${promptsPath}`);
  process.exit(1);
}

const prompts = JSON.parse(readFileSync(promptsPath, 'utf-8'));
const has = (id) => ['png', 'jpg', 'jpeg', 'webp']
  .some((ext) => existsSync(path.join(proj, 'images', `${id}.${ext}`)));

const missing = prompts.filter((p) => !has(p.id));
const outPath = path.join(proj, 'prompts-missing.json');
writeFileSync(outPath, JSON.stringify(missing, null, 1), 'utf-8');

console.log(`มีแล้ว ${prompts.length - missing.length}/${prompts.length} รูป`);
if (missing.length === 0) {
  console.log('ครบแล้ว — ไปขั้นบีบภาพ (optimize-images.py) ต่อได้เลย');
} else {
  console.log(`ยังขาด: ${missing.map((m) => m.id).join(' ')}`);
  console.log(`เขียน ${outPath} แล้ว`);
}
