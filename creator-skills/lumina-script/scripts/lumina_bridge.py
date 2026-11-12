# -*- coding: utf-8 -*-
# ตัวกลางระหว่างหน้า Lumina ใน Chrome กับเครื่อง: GET ส่งบท (UTF-8) ให้หน้าเว็บ · POST รับไฟล์เสียงแล้วบันทึก แล้วปิดตัวเอง
# ใช้: python lumina_bridge.py <script.txt> <out.mp3> [port]
import http.server, io, json, sys, threading

SRC, OUT = sys.argv[1], sys.argv[2]
PORT = int(sys.argv[3]) if len(sys.argv) > 3 else 8799


class H(http.server.BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def _cors(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "*")
        self.send_header("Access-Control-Allow-Private-Network", "true")

    def do_OPTIONS(self):
        self.send_response(204); self._cors(); self.end_headers()

    def do_GET(self):
        body = json.dumps({"t": io.open(SRC, encoding="utf-8").read().strip()}, ensure_ascii=False).encode("utf-8")
        self.send_response(200); self._cors()
        self.send_header("Content-Type", "application/json; charset=utf-8"); self.end_headers(); self.wfile.write(body)

    def do_POST(self):
        n = int(self.headers.get("Content-Length", 0))
        open(OUT, "wb").write(self.rfile.read(n))
        self.send_response(200); self._cors(); self.end_headers(); self.wfile.write(b"ok %d" % n)
        print("saved", OUT, n, flush=True)
        threading.Thread(target=self.server.shutdown, daemon=True).start()


# Kosin 17/10/2026 จองพอร์ตแบบผูกขาด: บน Windows HTTPServer ปกติเปิดพอร์ตซ้อนกับอีกเซสชันได้
# (เคยเกิด 16/10/2569: หน้าเว็บดึงบทของงานอื่นไปสร้างเสียง แล้วเสียงไปลงโฟลเดอร์ของงานนั้น)
import socket


class S(http.server.HTTPServer):
    allow_reuse_address = False

    def server_bind(self):
        if hasattr(socket, "SO_EXCLUSIVEADDRUSE"):
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_EXCLUSIVEADDRUSE, 1)
        super().server_bind()


try:
    srv = S(("127.0.0.1", PORT), H)
except OSError as e:
    sys.exit(f"พอร์ต {PORT} มีงานอื่นใช้อยู่ ({e}) ให้ระบุพอร์ตอื่นเป็นอาร์กิวเมนต์ที่ 3 และแก้ PORT ใน lumina_page.js ให้ตรงกัน")
print("ready", PORT, "chars", len(io.open(SRC, encoding="utf-8").read().strip()), flush=True)
srv.serve_forever()
