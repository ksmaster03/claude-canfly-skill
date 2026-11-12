# -*- coding: utf-8 -*-
# หาภาพที่ใช้ได้ฟรีพร้อมสัญญาอนุญาต จาก Wikimedia Commons และ Openverse แล้วโหลดลง <project_dir>/img
# ใช้: python find_images.py <project_dir> <queries.txt> [จำนวนต่อคำค้น=4]
# queries.txt (UTF-8) บรรทัดละ:  slug | คำค้น | แหล่ง(commons หรือ openverse ไม่ใส่คือทั้งคู่)
# ได้: img/<slug>_<n>.jpg · img/_sheet_<slug>.jpg (แผ่นรวมไว้เปิดดูเลือก) · credits.json (เครดิตและสัญญาอนุญาตของทุกไฟล์)
import html
import io
import json
import os
import re
import subprocess
import sys
import urllib.parse
import urllib.request

d, qfile = sys.argv[1], sys.argv[2]
N = int(sys.argv[3]) if len(sys.argv) > 3 else 4
UA = {"User-Agent": "newsreel-skill/1.0 (personal video tool)"}
def ok_lic(lic):   # รับเฉพาะ CC0 / CC BY / CC BY-SA / สาธารณสมบัติ  ตัด NC และ ND ออก
    x = lic.lower().replace("-", " ")
    return bool(re.match(r"(cc0|cc by( sa)?( \d|$)|public domain|pdm?$)", x)) and " nc" not in x and " nd" not in x
os.makedirs(f"{d}/img", exist_ok=True)
cpath = f"{d}/credits.json"
credits = json.load(io.open(cpath, encoding="utf-8")) if os.path.exists(cpath) else {}


def get(url):
    return urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=40).read()


def strip(s):
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", "", s or ""))).strip()[:80]


def commons(q):
    u = "https://commons.wikimedia.org/w/api.php?" + urllib.parse.urlencode({
        "action": "query", "generator": "search", "gsrsearch": q + " filetype:bitmap", "gsrnamespace": 6, "gsrlimit": N * 3,
        "prop": "imageinfo", "iiprop": "url|extmetadata|size|mime", "iiurlwidth": 1600, "format": "json"})
    pages = json.loads(get(u)).get("query", {}).get("pages", {})
    for p in sorted(pages.values(), key=lambda x: x.get("index", 0)):
        ii = p["imageinfo"][0]
        m = ii.get("extmetadata", {})
        lic = m.get("LicenseShortName", {}).get("value", "")
        if ii.get("mime") not in ("image/jpeg", "image/png") or ii.get("width", 0) < 900:
            continue
        yield {"url": ii.get("thumburl") or ii["url"], "license": lic, "artist": strip(m.get("Artist", {}).get("value", "")),
               "page": ii.get("descriptionurl", ""), "source": "Wikimedia Commons", "title": p.get("title", "")}


def openverse(q):
    u = "https://api.openverse.org/v1/images/?" + urllib.parse.urlencode({"q": q, "license_type": "commercial,modification", "page_size": N * 3})
    for r in json.loads(get(u)).get("results", []):
        if (r.get("width") or 0) < 900:
            continue
        yield {"url": r["url"], "license": ("CC " + r["license"].upper() + " " + (r.get("license_version") or "")).strip() if r["license"] not in ("cc0", "pdm") else r["license"].upper(),
               "artist": strip(r.get("creator")), "page": r.get("foreign_landing_url", ""), "source": "Openverse/" + (r.get("source") or ""), "title": r.get("title") or ""}


for raw in io.open(qfile, encoding="utf-8"):
    parts = [x.strip() for x in raw.split("|")]
    if len(parts) < 2 or not parts[0] or parts[0].startswith("#"):
        continue
    slug, q, src = parts[0], parts[1], (parts[2] if len(parts) > 2 else "")
    got, files = 0, []
    for name, fn in (("commons", commons), ("openverse", openverse)):
        if src and src != name:
            continue
        try:
            items = list(fn(q))
        except Exception as e:
            print(f"  {slug}: {name} ล้มเหลว {e}")
            continue
        for it in items:
            if got >= N:
                break
            if not ok_lic(it["license"]):
                continue
            out = f"img/{slug}_{got + 1}.jpg"
            try:
                tmp = f"{d}/img/_dl.bin"
                open(tmp, "wb").write(get(it["url"]))
                # แปลงเป็น jpg กว้างไม่เกิน 1600 และตรวจว่าเปิดได้จริง
                subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", tmp, "-vf", "scale='min(1600,iw)':-2", "-q:v", "3", f"{d}/{out}"], check=True)
            except Exception as e:
                print(f"  {slug}: ข้าม {it['url'][:60]} ({e})")
                continue
            it["credit"] = "ภาพ: " + " / ".join(x for x in (it["artist"] or it["source"], it["license"]) if x)
            it["query"] = q
            credits[out] = it
            files.append(f"{d}/{out}")
            got += 1
    if os.path.exists(f"{d}/img/_dl.bin"):
        os.remove(f"{d}/img/_dl.bin")
    if files:
        ins = sum([["-i", f] for f in files], [])
        cell = "scale=360:360:force_original_aspect_ratio=decrease,pad=360:360:(ow-iw)/2:(oh-ih)/2"
        if len(files) == 1:
            fc = f"[0:v]{cell}"
        else:
            fc = "".join(f"[{i}:v]{cell}[v{i}];" for i in range(len(files))) + "".join(f"[v{i}]" for i in range(len(files))) + f"hstack=inputs={len(files)}"
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error"] + ins + ["-filter_complex", fc, "-frames:v", "1", "-q:v", "4", f"{d}/img/_sheet_{slug}.jpg"])
    print(f"{slug}: ได้ {got} ภาพ" + ("" if got else "  <-- ไม่เจอ ลองคำค้นภาษาอังกฤษ หรือคำที่กว้างขึ้น"))
io.open(cpath, "w", encoding="utf-8", newline="\n").write(json.dumps(credits, ensure_ascii=False, indent=1))
print("credits ->", cpath, len(credits), "ไฟล์")
