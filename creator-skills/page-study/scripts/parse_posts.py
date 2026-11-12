# parse_posts.py: posts.json (จาก fb-page-read.mjs) -> lastN.txt + ตารางจัดอันดับ reaction/แชร์
# ใช้: PYTHONIOENCODING=utf-8 python parse_posts.py <outdir> "<ชื่อเพจตามที่ขึ้นบนโพสต์>" [วันเริ่ม YYYY-MM-DD]
import json, re, sys
out, NAME = sys.argv[1], sys.argv[2]
SINCE = sys.argv[3] if len(sys.argv) > 3 else '0000'
th = 'มกราคม กุมภาพันธ์ มีนาคม เมษายน พฤษภาคม มิถุนายน กรกฎาคม สิงหาคม กันยายน ตุลาคม พฤศจิกายน ธันวาคม'.split()
P = json.load(open(f'{out}/posts.json', encoding='utf-8'))
best = {}
for p in P:
    t = p['text']
    if not t.startswith(NAME): continue  # ข้ามคอมเมนต์ที่ติดมา
    m = re.search(r'วัน\S+ที่ (\d+) (' + '|'.join(th) + r') (\d{4}) เวลา (\d+:\d+)', t[:250])
    if not m: continue
    d = f"{m.group(3)}-{th.index(m.group(2))+1:02d}-{int(m.group(1)):02d} {m.group(4)}"
    if d < SINCE: continue
    body = t.split('·\n', 1)[-1]
    key = d + re.sub(r'\s+', ' ', body)[:25]
    full = 'ดูน้อยลง' in t
    if key not in best or (full and 'ดูน้อยลง' not in best[key]['text']): best[key] = {'date': d, 'text': t, 'link': p['link']}
rows = []
with open(f'{out}/posts_since.txt', 'w', encoding='utf-8') as f:
    for x in sorted(best.values(), key=lambda x: x['date'], reverse=True):
        body = re.sub(r'อาจเป็น[^\n]*\n?', '', x['text'].split('·\n', 1)[-1])
        seg = body.split('ดูน้อยลง')[-1].split('แสดงความคิดเห็นในชื่อ')[0]
        nums = re.findall(r'^\s*([\d.,]+(?: ?(?:พัน|หมื่น))?)\s*$', seg, re.M)  # [reaction, (คอมเมนต์), แชร์]
        rows.append((x['date'], nums, re.sub(r'\s+', ' ', body)[:80]))
        f.write(f"=== {x['date']} {x['link'][:100]}\n{body.split('ดูน้อยลง')[0][:3000]}\n\n")
val = lambda n: float(n[0].replace(',', '')) if n and re.fullmatch(r'[\d.,]+', n[0]) else 0
print(len(rows), 'โพสต์')
for d, n, b in sorted(rows, key=lambda r: -val(r[1])): print(d, n, b)
