#!/usr/bin/env python
"""
pc_card.py — render an HTML template to PNG with headless Chromium.

  python pc_card.py TEMPLATE.html OUT.png --data data.json [--size 1080x1080] [--transparent]

Why Chromium: Thai vowels and tone marks only sit right when the text is shaped by
a real layout engine. ffmpeg drawtext and PIL (no raqm on this machine) float them.

Text goes in data.json, never on the command line: Git Bash turns non-ASCII
arguments into '?????' and still exits 0.

data.json keys match the template's data-k attributes. Also understood:
  "logos": ["C:/abs/logo1.png", ...]   images for the template's logo row
  "vars":  {"accent": "#ffb000", ...}  CSS variable overrides (no leading --)
In text, *word* marks the accent colour and \\n breaks the line.
"""
import argparse
import json
import pathlib
import sys

from playwright.sync_api import sync_playwright


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("template")
    ap.add_argument("out")
    ap.add_argument("--data", help="UTF-8 JSON file with the text / logos / vars")
    ap.add_argument("--size", default="1080x1080", help="WxH in px (frame: 1080x1080, card: the footage window)")
    ap.add_argument("--transparent", action="store_true", help="keep the page background transparent (frame)")
    a = ap.parse_args()

    w, h = (int(v) for v in a.size.lower().split("x"))
    data = {}
    if a.data:
        with open(a.data, encoding="utf-8") as f:
            data = json.load(f)
    # local image paths -> file:// URLs so the page may load them
    if isinstance(data.get("logos"), list):
        data["logos"] = [p if "://" in p else pathlib.Path(p).resolve().as_uri() for p in data["logos"]]

    tpl = pathlib.Path(a.template).resolve()
    out = pathlib.Path(a.out).resolve()
    out.parent.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as p:
        b = p.chromium.launch(headless=True)
        page = b.new_page(viewport={"width": w, "height": h}, device_scale_factor=1)
        page.add_init_script("window.PC = " + json.dumps(data, ensure_ascii=False) + ";")
        page.goto(tpl.as_uri())
        page.evaluate("document.fonts.ready")
        # an image that failed to load is a silent hole in the card: fail instead
        broken = page.evaluate("Array.from(document.images).filter(i => !i.complete || !i.naturalWidth).map(i => i.src)")
        if broken:
            b.close()
            sys.exit("image(s) failed to load: " + ", ".join(broken))
        fonts = page.evaluate(
            "Array.from(new Set(Array.from(document.querySelectorAll('[data-k]'))"
            ".map(e => getComputedStyle(e).fontFamily.split(',')[0].trim())))")
        page.screenshot(path=str(out), omit_background=a.transparent, full_page=False)
        b.close()
    print(f"wrote {out}  ({w}x{h}{', transparent' if a.transparent else ''})  first-choice font: {', '.join(fonts)}")


if __name__ == "__main__":
    for s in (sys.stdout, sys.stderr):
        try:
            s.reconfigure(encoding="utf-8")
        except Exception:
            pass
    main()
