# -*- coding: utf-8 -*-
# เรนเดอร์ post.json เป็น PNG ด้วย Chromium (ตัวไทยไม่ลอย) ตรวจข้อความล้น ฟอนต์ และภาพที่หาไม่เจอ
# ใช้: python render_post.py <post.json> [post2.json ...] [--brand brand.json]
# ภาพออกข้าง json ชื่อตาม "out" หรือชื่อ json (slide-1.json → slide-1.png) · exit 1 ถ้ามีชิ้นไหนไม่ผ่าน
import json
import sys
import tempfile
from pathlib import Path
from playwright.sync_api import sync_playwright

HERE = Path(__file__).resolve().parent
TEMPLATE = (HERE / "post_template.html").read_text(encoding="utf-8")
FONTDIR = (HERE.parent / "assets" / "fonts").as_uri()
SIZES = json.loads((HERE.parent / "reference" / "styles.json").read_text(encoding="utf-8"))["aspect"]


def uri(base, p):
    if not p:
        return None
    q = (base / p).resolve()
    return q.as_uri() if q.exists() else "missing:" + str(q)


def load(path, brand, brand_dir):
    try:
        post = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        raise SystemExit("JSON เสียที่ %s: %s (ขึ้นบรรทัดในข้อความต้องเขียน \\n)" % (path.name, e))
    base = path.parent
    size = post.get("size", "1:1")
    post["px"] = SIZES[size]["px"] if isinstance(size, str) else list(size)
    visual = (brand or {}).get("visual", {})
    theme = dict(visual.get("colors") or {})
    if visual.get("font"):
        theme["font"] = visual["font"]
    theme.update(post.get("theme") or {})
    post["theme"] = theme
    for k in ("bg", "person"):
        post[k] = uri(base, post.get(k))
    if post.get("logo"):
        post["logo"] = uri(base, post["logo"])
    elif brand and brand.get("logo") and post.get("logo", True) is not False:
        post["logo"] = uri(brand_dir, brand["logo"])
    post["fontdir"] = FONTDIR
    out = base / post.get("out", path.stem + ".png")
    return post, out


def main():
    args = sys.argv[1:]
    brand, brand_dir = None, None
    if "--brand" in args:
        i = args.index("--brand")
        bp = Path(args[i + 1]).resolve()
        brand, brand_dir = json.loads(bp.read_text(encoding="utf-8")), bp.parent
        args = args[:i] + args[i + 2:]
    if not args:
        raise SystemExit("ใช้: python render_post.py <post.json> [...] [--brand brand.json]")
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    bad = 0
    with sync_playwright() as pw, tempfile.TemporaryDirectory() as tmp:
        b = pw.chromium.launch(args=["--allow-file-access-from-files"])
        for a in args:
            path = Path(a).resolve()
            post, out = load(path, brand, brand_dir)
            w, h = post["px"]
            html = TEMPLATE.replace("/*__DATA__*/", "window.POST = " + json.dumps(post, ensure_ascii=False) + ";")
            page_file = Path(tmp) / (path.stem + ".html")
            page_file.write_text(html, encoding="utf-8")
            pg = b.new_page(viewport={"width": w, "height": h}, device_scale_factor=1)
            pg.goto(page_file.as_uri())
            pg.wait_for_function("window.__READY === true", timeout=30000)
            rep = pg.evaluate("window.__REPORT")
            pg.locator("#c").screenshot(path=str(out))
            pg.close()
            problems = []
            if rep.get("overflow"):
                problems.append("ข้อความล้นกรอบ (ตัดคำหรือย่อข้อความ)")
            if rep.get("fontError"):
                problems.append("โหลดฟอนต์ไม่ได้ " + rep["fontError"])
            missing = [m for m in (rep.get("missing") or [])] + [v for v in (post.get("bg"), post.get("logo"), post.get("person")) if v and v.startswith("missing:")]
            if missing:
                problems.append("หาภาพไม่เจอ " + ", ".join(sorted(set(missing))))
            status = "ผ่าน" if not problems else "ไม่ผ่าน: " + " · ".join(problems)
            bad += bool(problems)
            print("%s  %dx%d  ย่อ %.2f  %s" % (out.name, w, h, rep.get("scale", 1), status))
        b.close()
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
