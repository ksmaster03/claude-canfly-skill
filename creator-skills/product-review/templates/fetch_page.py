# fetch_page.py <URL> <PROJ> — ดึงหน้าเว็บสินค้า: ข้อความทั้งหน้า + วิดีโอทุกตัว (ความละเอียดสูงสุด) + บริบทหัวข้อของแต่ละวิดีโอ
# ผลลัพธ์: <PROJ>/page.html, text.txt, videos.json, src/NN.mp4, src_info.txt
# หน้า Shopify/JS ส่วนใหญ่ฝัง <source data-src=...mp4> ไว้ใน HTML ดิบ แม้ WebFetch จะเห็นแค่เมนู
# ใช้: python fetch_page.py <URL> <PROJ> [--allow-host cdn.example.com ...]
#
# ความปลอดภัย: URL วิดีโอมาจาก HTML ของเว็บภายนอก (ไม่น่าเชื่อถือ) แล้วถูกส่งต่อให้ ffprobe/ffmpeg จึงต้องกันไว้ก่อน
#   - รับเฉพาะ https และเฉพาะโฮสต์ของหน้าเว็บเอง (รวมซับโดเมน) + CDN ที่รู้จัก + ที่ระบุด้วย --allow-host
#   - ปฏิเสธโฮสต์ที่ชี้ไป IP ภายใน/loopback (กัน SSRF) และไม่ตาม redirect ออกนอกรายการที่อนุญาต
#   - จำกัดจำนวนไฟล์ ขนาดต่อไฟล์ และขนาดหน้าเว็บ
#   - ตรวจ magic bytes ว่าเป็นคอนเทนเนอร์ MP4/WebM จริง (ไฟล์ playlist/สคริปต์ที่ตั้งชื่อ .mp4 จะถูกทิ้ง)
#   - ffprobe เปิดด้วย -protocol_whitelist file เท่านั้น
import re, io, json, html, sys, socket, ipaddress, subprocess as sp, urllib.request, urllib.parse, urllib.error, concurrent.futures as cf
from pathlib import Path
args = sys.argv[1:]; EXTRA = set()
while "--allow-host" in args:
    i = args.index("--allow-host"); EXTRA.add(args[i+1].lower()); del args[i:i+2]
URL, P = args[0], Path(args[1]); P.mkdir(parents=True, exist_ok=True); (P/"src").mkdir(exist_ok=True)
UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/128 Safari/537.36"}
MAX_PAGE, MAX_FILE, MAX_VIDEOS = 20 << 20, 400 << 20, 150
PAGE_HOST = (urllib.parse.urlsplit(URL).hostname or "").lower()
assert urllib.parse.urlsplit(URL).scheme == "https" and PAGE_HOST, "รับเฉพาะ URL แบบ https"
BASE = ".".join(PAGE_HOST.split(".")[-2:])                      # hoverair.com
CDN = {"cdn.shopify.com", "cdn.shopifycdn.net"} | EXTRA

def host_ok(h):
    h = (h or "").lower()
    if not (h == BASE or h.endswith("." + BASE) or h in CDN): return False
    try:
        for info in socket.getaddrinfo(h, 443):
            ip = ipaddress.ip_address(info[4][0])
            if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved or ip.is_multicast: return False
    except Exception: return False
    return True
def url_ok(u):
    p = urllib.parse.urlsplit(u)
    return p.scheme == "https" and not p.username and host_ok(p.hostname)
class _Redir(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        if not url_ok(newurl): raise urllib.error.URLError(f"redirect ออกนอกโฮสต์ที่อนุญาต: {newurl[:80]}")
        return super().redirect_request(req, fp, code, msg, headers, newurl)
OPEN = urllib.request.build_opener(_Redir).open
def fetch(u, limit, timeout):
    assert url_ok(u), f"โฮสต์ไม่อยู่ในรายการที่อนุญาต: {u[:80]}"
    with OPEN(urllib.request.Request(u, headers=UA), timeout=timeout) as r:
        data = r.read(limit + 1)
    if len(data) > limit: raise ValueError(f"ไฟล์ใหญ่เกิน {limit >> 20} MB: {u[:80]}")
    return data
def is_video(data):
    return data[4:8] == b"ftyp" or data[:4] == bytes.fromhex("1a45dfa3")   # MP4/MOV or WebM/Matroska
s = fetch(URL, MAX_PAGE, 60).decode("utf-8", "ignore")
(P/"page.html").write_text(s, encoding="utf-8")

# ---- ข้อความ (ตัดซ้ำ) ----
t = re.sub(r"(?s)<(script|style|svg)[^>]*>.*?</\1>", " ", s)
seen = set(); out = []
for l in html.unescape(re.sub(r"<[^>]+>", "\n", t)).split("\n"):
    l = l.strip()
    if l and l not in seen: seen.add(l); out.append(l)
(P/"text.txt").write_text("\n".join(out), encoding="utf-8")

# ---- วิดีโอ: จับ URL .mp4/.webm ทุกตัว จัดกลุ่มตาม id แล้วเลือกตัวคุณภาพสูงสุด ----
pat = re.compile(r"(?:https?:)?//[A-Za-z0-9.\-]+/[A-Za-z0-9_./%\-]+?\.(?:mp4|webm)")
vids = {}
for m in pat.finditer(s):
    url = m.group(0); url = "https:" + url if url.startswith("//") else url
    stem = url.rsplit("/", 1)[-1]
    vid = re.match(r"([0-9a-f]{20,})", stem); vid = vid.group(1) if vid else stem.split(".")[0]
    r = re.search(r"(\d{3,4})p-([\d.]+)Mbps", url)
    q = int(r.group(1))*100 + float(r.group(2)) if r else 999999   # ไฟล์ original (ไม่มี preset) = ดีสุด
    d = vids.setdefault(vid, {"first": m.start(), "urls": []}); d["urls"].append((q, url))
def ctx(pos):
    c = re.sub(r"(?s)<(script|style|svg)[^>]*>.*?</\1>", " ", s[max(0, pos-8000):pos])
    tt = [html.unescape(x).strip() for x in re.sub(r"<[^>]+>", "\n", c).split("\n")]
    tt = [x for x in tt if x and len(x) < 200 and not x.startswith(("{", "}", ".", "@", "#", "<"))
          and "src=" not in x and "type=" not in x]
    return " | ".join(tt[-2:])
rejected = sorted({urllib.parse.urlsplit(u).hostname or "?" for d in vids.values() for _, u in d["urls"] if not url_ok(u)})
if rejected: print("ข้ามโฮสต์ที่ไม่อยู่ในรายการอนุญาต (เพิ่มได้ด้วย --allow-host):", ", ".join(rejected))
for d in vids.values(): d["urls"] = [(q, u) for q, u in d["urls"] if url_ok(u)]
vids = {k: d for k, d in vids.items() if d["urls"]}
V = [{"key": f"{i:02d}", "url": max(d["urls"])[1], "ctx": ctx(d["first"])}
     for i, (k, d) in enumerate(sorted(vids.items(), key=lambda kv: kv[1]["first"]))][:MAX_VIDEOS]
def dl(v):
    try:
        data = fetch(v["url"], MAX_FILE, 180)
        if not is_video(data): raise ValueError("ไม่ใช่คอนเทนเนอร์ MP4/WebM")
        (P/"src"/f"{v['key']}.mp4").write_bytes(data); return v["key"], None
    except Exception as e: return v["key"], str(e)
with cf.ThreadPoolExecutor(8) as ex: res = dict(ex.map(dl, V))
skipped = {k: e for k, e in res.items() if e}
V = [v for v in V if v["key"] not in skipped]
for k, e in skipped.items(): print(f"SKIP {k}: {e}")
lines = []
for v in V:
    f = P/"src"/f"{v['key']}.mp4"
    o = sp.run(["ffprobe","-v","error","-protocol_whitelist","file","-select_streams","v:0","-show_entries","stream=width,height:format=duration",
                "-of","csv=p=0:s=x",str(f)], capture_output=True, text=True).stdout.split()
    v["wh"], v["dur"] = (o + ["?", "?"])[:2]
    lines.append(f"{v['key']}  {v['wh']:>10}  {v['dur']:>8}s  :: {v['ctx'][:110]}")
json.dump(V, open(P/"videos.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
(P/"src_info.txt").write_text("\n".join(lines), encoding="utf-8")
print(f"text lines {len(out)}  videos {len(V)}"); print("\n".join(lines))
