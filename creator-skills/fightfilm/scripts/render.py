import sys, subprocess, pathlib, json
from playwright.sync_api import sync_playwright

HERE = pathlib.Path(__file__).parent
FPS = 60
mode = sys.argv[1] if len(sys.argv) > 1 else "preview"
PAGE = __import__("os").environ.get("PAGE", "index.html")
OUT = __import__("os").environ.get("OUT", "model-release-forecast-2027.mp4")

with sync_playwright() as pw:
    b = pw.chromium.launch()
    pg = b.new_page(viewport={"width": 1920, "height": 1080})
    pg.on("pageerror", lambda e: print("PAGEERROR", e, flush=True))
    pg.goto((HERE / PAGE).as_uri())
    pg.wait_for_function("window.READY === true", timeout=60000)
    print(json.dumps(pg.evaluate("[window.STATS, window.TOTALS, document.fonts.check('700 20px \"Noto Sans Thai\"')]"), ensure_ascii=False))
    print(json.dumps(pg.evaluate("window.MWSTATS || null"), ensure_ascii=False))
    sfx = pg.evaluate("window.SFX || null")
    if sfx: (HERE / "sfx_events.json").write_text(json.dumps(sfx), encoding="utf-8")
    duck = pg.evaluate("window.DUCK || null")
    if duck: (HERE / "duck.json").write_text(json.dumps(duck), encoding="utf-8")
    cv = pg.locator("#c")
    if mode == "preview":
        for t in [float(x) for x in sys.argv[2:]]:
            pg.evaluate("t => draw(t)", t)
            cv.screenshot(path=str(HERE / f"{PAGE[:-5]}_{t:05.2f}.png"))
    else:
        tend = pg.evaluate("window.TEND")
        n = int(tend * FPS)
        F0 = int(__import__("os").environ.get("F0", "0")); F1 = int(__import__("os").environ.get("F1", str(n)))
        out = str(HERE / OUT)
        ff = subprocess.Popen(["ffmpeg", "-hide_banner", "-v", "error", "-y", "-f", "image2pipe", "-framerate", str(FPS),
                               "-c:v", "mjpeg", "-i", "-", "-c:v", "libx264", "-preset", "slow", "-crf", "17",
                               "-pix_fmt", "yuv420p", "-movflags", "+faststart", out], stdin=subprocess.PIPE)
        for i in range(F0, min(F1, n)):
            pg.evaluate("t => draw(t)", i / FPS)
            ff.stdin.write(cv.screenshot(type="jpeg", quality=95))
            if i % 150 == 0:
                print(f"frame {i}/{n}", flush=True)
        ff.stdin.close(); ff.wait()
        print("done", out, ff.returncode)
    b.close()
