import json, subprocess, sys, time, io
from playwright.sync_api import sync_playwright
D = '__PROJECT__/qc/pose'
srv = subprocess.Popen([sys.executable, '-m', 'http.server', '8771', '--bind', '127.0.0.1'], cwd=D, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
time.sleep(1.2)
try:
    with sync_playwright() as p:
        b = p.chromium.launch(); pg = b.new_page()
        pg.on('console', lambda m: print('console', m.text) if m.type == 'error' else None)
        pg.goto('http://127.0.0.1:8771/pose.html'); pg.wait_for_function('window.ok === true', timeout=30000)
        res = pg.evaluate("async () => await window.run(['crop_m22-pushup.jpg', 'crop_m23-situp.jpg'])")
        json.dump(res, io.open(D + '/poses_crop.json', 'w'), indent=0)
        for k, v in res.items():
            print(k, 'people', len(v), [round(sum(q[2] for q in pp) / len(pp), 2) for pp in v])
        b.close()
finally:
    srv.terminate()
