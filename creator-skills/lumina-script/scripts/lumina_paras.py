# -*- coding: utf-8 -*-
# Kosin 17/10/2026 ตัวกลางกับหน้า Lumina แบบหลายย่อหน้า: GET /pNN ส่งบท vo/para/pNN.txt · POST /pNN เก็บเสียงเป็น vo/para/pNN.mp3
# ใช้: python lumina_paras.py <port> <para_dir>   para_dir มี pNN.txt (บทรายย่อหน้า) เสียงที่ได้เก็บเป็น pNN.mp3 ในโฟลเดอร์เดียวกัน
import http.server, io, json, os, re, sys
PORT = int(sys.argv[1])
D = os.path.abspath(sys.argv[2])


class H(http.server.BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def _cors(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "*")
        self.send_header("Access-Control-Allow-Private-Network", "true")

    def _name(self):
        m = re.fullmatch(r"/(p\d\d)(?:_r\d)?", self.path)
        return m and m.group(0)[1:]

    def do_OPTIONS(self):
        self.send_response(204); self._cors(); self.end_headers()

    def do_GET(self):
        n = self._name()
        src = n and os.path.join(D, n.split("_")[0] + ".txt")
        if not src or not os.path.exists(src):
            self.send_response(404); self._cors(); self.end_headers(); return
        body = json.dumps({"t": io.open(src, encoding="utf-8").read().strip()}, ensure_ascii=False).encode("utf-8")
        self.send_response(200); self._cors()
        self.send_header("Content-Type", "application/json; charset=utf-8"); self.end_headers(); self.wfile.write(body)

    def do_POST(self):
        n = self._name()
        data = self.rfile.read(int(self.headers.get("Content-Length", 0)))
        open(os.path.join(D, n + ".mp3"), "wb").write(data)
        self.send_response(200); self._cors(); self.end_headers(); self.wfile.write(b"ok %d" % len(data))
        print("saved", n, len(data), flush=True)


import socket


class S(http.server.HTTPServer):
    allow_reuse_address = False  # จองพอร์ตผูกขาด กันชนกับเซสชันอื่น ดู lumina_bridge.py

    def server_bind(self):
        if hasattr(socket, "SO_EXCLUSIVEADDRUSE"):
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_EXCLUSIVEADDRUSE, 1)
        super().server_bind()


try:
    srv = S(("127.0.0.1", PORT), H)
except OSError as e:
    sys.exit(f"พอร์ต {PORT} มีงานอื่นใช้อยู่ ({e})")
print("ready", PORT, D, flush=True)
srv.serve_forever()
