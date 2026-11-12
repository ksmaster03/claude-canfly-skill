# -*- coding: utf-8 -*-
# ประกอบพรอมต์ภาพจาก images.json + brand.json + styles.json
# แล้วเขียนไฟล์งานให้ gen_images.sh ยิง chatgpt-bridge ทีละภาพ
# ใช้: python prompt.py <images.json> <jobs_dir> [--brand brand.json]
#
# images.json = [{ "id": "p01", "subject": "<ฉากภาษาอังกฤษ>", "aspect": "4:5", "text_zone": "bottom",
#                  "style": "Warm Minmal", "ref": "assets/products/x-1.jpg", "mode": "post|enhance|sku",
#                  "enhance": "Podium", "shot": "cover|howto|ambience|detail", "extra": "..." }]
# path ใน ref อิงโฟลเดอร์ของ images.json
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
STYLES = json.loads((HERE.parent / "reference" / "styles.json").read_text(encoding="utf-8"))

KEEP_PRODUCT = ("Use the attached photo as the exact product reference. Keep the product's shape, packaging, "
                "label artwork, colors and proportions identical; do not redesign, relabel or replace it. "
                "Do not add any new text; only the text already printed on the product itself may appear.")
SKU_SHOTS = {
    "cover": "Marketplace main image: the product centered and large, clean premium background, sharp and fully visible.",
    "howto": "The product being used in a natural real-life moment that shows how to use it, hands only, no faces.",
    "ambience": "A lifestyle scene that shows the mood and setting where this product belongs, product clearly visible.",
    "detail": "Extreme close-up macro of the product's texture, material and key detail.",
}


def build(item, brand):
    visual = (brand or {}).get("visual", {})
    aspect = item.get("aspect", "1:1")
    if aspect not in STYLES["aspect"]:
        raise SystemExit("aspect ไม่รู้จัก: %s (ใช้ได้ %s)" % (aspect, ", ".join(STYLES["aspect"])))
    gen_aspect = STYLES["aspect"][aspect]["gen"]
    mode = item.get("mode", "post")
    ref = item.get("ref")
    parts = []

    if mode == "enhance":
        if not ref:
            raise SystemExit("%s: mode enhance ต้องมี ref" % item["id"])
        name = item.get("enhance", "Natural Daylight")
        if name not in STYLES["enhance"]:
            raise SystemExit("%s: enhance style ไม่รู้จัก: %s" % (item["id"], name))
        parts += [KEEP_PRODUCT, "Re-shoot it as a professional product photo: " + STYLES["enhance"][name]["prompt"] + ".",
                  "Improve lighting, clarity and color while keeping every product detail true."]
        if item.get("extra"):
            parts.append(item["extra"])
        parts.append(gen_aspect if item.get("aspect") else "Keep the original aspect ratio of the attached photo.")
        return " ".join(parts)

    style_name = item.get("style") or visual.get("style") or "Vibrant Premium"
    if style_name not in STYLES["post"]:
        raise SystemExit("%s: style ไม่รู้จัก: %s" % (item["id"], style_name))
    if ref:
        parts.append(KEEP_PRODUCT)
        parts.append("Create a new advertising image with this product:")
    if mode == "sku":
        parts.append(SKU_SHOTS[item.get("shot", "cover")])
    if item.get("subject"):
        parts.append(item["subject"].rstrip(".") + ".")
    parts.append("Visual style: " + STYLES["post"][style_name]["prompt"] + ".")
    if visual.get("custom"):
        custom = visual["custom"].strip().rstrip(".")
        parts.append(custom[:1].upper() + custom[1:] + ".")
    colors = visual.get("colors") or {}
    accents = [c for c in (colors.get("primary"), colors.get("accent")) if c]
    if accents:
        parts.append("Use the brand colors %s as subtle accents in props, light or background." % " and ".join(accents))
    if item.get("extra"):
        parts.append(item["extra"])
    zone = STYLES["text_zone"].get(item.get("text_zone", "bottom"), "")
    if zone:
        parts.append(zone)
    if not ref:
        parts.append(STYLES["no_text"])
    parts.append(gen_aspect)
    return " ".join(parts)


def main():
    a = sys.argv[1:]
    if len(a) < 2:
        raise SystemExit("ใช้: python prompt.py <images.json> <jobs_dir> [--brand brand.json]")
    src = Path(a[0]).resolve()
    jobs = Path(a[1]).resolve()
    brand = json.loads(Path(a[a.index("--brand") + 1]).read_text(encoding="utf-8")) if "--brand" in a else None
    items = json.loads(src.read_text(encoding="utf-8"))
    jobs.mkdir(parents=True, exist_ok=True)
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    for it in items:
        prompt = build(it, brand)
        job = {"id": it["id"], "prompt": prompt}
        if it.get("ref"):
            ref = (src.parent / it["ref"]).resolve()
            if not ref.exists():
                raise SystemExit("%s: ไม่พบรูปอ้างอิง %s" % (it["id"], ref))
            job["ref"] = str(ref)
            (jobs / (it["id"] + ".prompt.txt")).write_text(prompt, encoding="utf-8")
        (jobs / (it["id"] + ".json")).write_text(json.dumps([job], ensure_ascii=False, indent=1), encoding="utf-8")
        print("%-10s %-6s %s%s" % (it["id"], it.get("mode", "post"), "ref " if it.get("ref") else "", prompt[:110] + "..."))
    print("เขียนงาน %d ชิ้นที่ %s" % (len(items), jobs))


if __name__ == "__main__":
    main()
