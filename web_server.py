"""HTTP server cục bộ cho giao diện khách hàng sau khi quét QR."""

from __future__ import annotations

import json
import socket
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any

from models import SharedBridge

MOBILE_HTML = """<!doctype html>
<html lang="vi">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Smart Parking B1</title>
<style>
:root{--bg:#07101c;--card:#111e2d;--line:#24364a;--text:#edf5fc;--muted:#94a7ba;
--green:#2ac97e;--red:#f2535b;--blue:#3a9aff;--yellow:#ffc43d;--cyan:#29d3da}
*{box-sizing:border-box}body{margin:0;background:radial-gradient(circle at top,#14283e,#07101c 48%);
color:var(--text);font:15px "Segoe UI",system-ui,sans-serif;min-height:100vh}
.app{max-width:560px;margin:auto;padding:20px}.head{display:flex;justify-content:space-between;align-items:center}
.brand{font-size:12px;letter-spacing:1.5px;color:var(--cyan);font-weight:800}
h1{font-size:25px;margin:5px 0}.live{color:var(--green);font-size:12px;font-weight:700}
.live:before{content:"";display:inline-block;width:8px;height:8px;background:var(--green);
border-radius:50%;margin-right:7px;box-shadow:0 0 0 5px #2ac97e22}
.stats{display:grid;grid-template-columns:repeat(3,1fr);gap:9px;margin:18px 0}
.card{background:#111e2ddd;border:1px solid var(--line);border-radius:17px;padding:14px;
box-shadow:0 12px 35px #0004;backdrop-filter:blur(12px)}.num{font-size:27px;font-weight:800}
.label{font-size:11px;color:var(--muted);margin-top:3px}.actions{display:grid;gap:10px}
button{border:0;border-radius:14px;padding:15px;color:white;font:700 14px "Segoe UI";
background:linear-gradient(135deg,#1878e5,#3a9aff);box-shadow:0 8px 20px #1878e533}
button:last-child{background:linear-gradient(135deg,#c98d0d,#ffc43d);color:#151a20}
.message{margin:14px 0;line-height:1.45}.route{display:grid;grid-template-columns:repeat(3,1fr);gap:8px}
.route div{background:#0a1521;border-radius:10px;padding:10px}.route b{display:block;font-size:18px}
.section{display:flex;justify-content:space-between;align-items:end;margin:18px 2px 9px}
.section b{font-size:15px}.section span{font-size:11px;color:var(--muted)}
.grid{display:grid;grid-template-columns:repeat(10,1fr);gap:4px}
.slot{aspect-ratio:1.2;border-radius:5px;background:var(--green);display:grid;place-items:center;
font-size:7px;font-weight:700;color:#07130d;position:relative}.slot.busy{background:var(--red);color:white}
.slot.mine{background:var(--yellow);color:#171717;box-shadow:0 0 13px #ffc43d99}
.slot.reserved{background:var(--blue);color:white}.slot.ev:after{content:"⚡";position:absolute;right:1px;top:0}
.legend{display:flex;flex-wrap:wrap;gap:12px;margin-top:12px;color:var(--muted);font-size:11px}
.dot{display:inline-block;width:9px;height:9px;border-radius:3px;margin-right:5px}
.tech{display:grid;grid-template-columns:1fr 1fr;gap:8px;margin-top:10px}
.tech div{font-size:12px;color:var(--muted)}.tech b{display:block;color:var(--text);font-size:14px}
</style>
</head>
<body><main class="app">
<div class="head"><div><div class="brand">MALL DIGITAL TWIN</div><h1>Bãi xe thông minh B1</h1></div>
<div class="live">TRỰC TUYẾN</div></div>
<div class="stats">
 <div class="card"><div class="num" id="free">--</div><div class="label">CHỖ TRỐNG</div></div>
 <div class="card"><div class="num" id="busy">--</div><div class="label">ĐÃ ĐỖ</div></div>
 <div class="card"><div class="num" id="moving">--</div><div class="label">ĐANG DI CHUYỂN</div></div>
</div>
<div class="actions">
 <button onclick="action('empty')">DẪN ĐẾN CHỖ ĐỖ TỐT NHẤT</button>
 <button onclick="action('mycar')">TÌM XE CỦA TÔI</button>
</div>
<div class="card message"><div id="message">Đang kết nối hệ thống...</div>
 <div class="route">
  <div><b id="target">--</b><span class="label">ĐÍCH ĐẾN</span></div>
  <div><b id="distance">--</b><span class="label">QUÃNG ĐƯỜNG</span></div>
  <div><b id="nodes">--</b><span class="label">NODE A*</span></div>
 </div>
</div>
<div class="section"><b>Sơ đồ 100 vị trí</b><span>Cập nhật mỗi giây</span></div>
<div class="card"><div class="grid" id="grid"></div>
 <div class="legend">
  <span><i class="dot" style="background:var(--green)"></i>Trống</span>
  <span><i class="dot" style="background:var(--red)"></i>Đã đỗ</span>
  <span><i class="dot" style="background:var(--blue)"></i>Đã giữ</span>
  <span><i class="dot" style="background:var(--yellow)"></i>Xe của bạn</span>
 </div>
</div>
<div class="section"><b>Hạ tầng thông minh</b><span id="latency">-- ms</span></div>
<div class="card tech">
 <div><b>ANPR Camera</b><span id="plate">---</span></div>
 <div><b>Cảm biến IoT</b><span id="uptime">--</span></div>
 <div><b>Thanh toán số</b>Đang hoạt động</div>
 <div><b>Sạc xe điện</b>10 vị trí</div>
</div>
</main>
<script>
async function refresh(){
 try{
  const s=await fetch("/api/status",{cache:"no-store"}).then(r=>r.json());
  free.textContent=s.free;busy.textContent=s.occupied;moving.textContent=s.moving;
  message.textContent=s.message;target.textContent=s.target||"--";
  distance.textContent=s.route_distance?s.route_distance+" m":"--";
  nodes.textContent=s.expanded_nodes||"--";latency.textContent=s.iot_latency+" ms";
  plate.textContent=s.last_plate;uptime.textContent=s.sensor_uptime+"% online";
  grid.innerHTML=s.slots.map(x=>`<div class="slot ${x.status} ${x.electric?"ev":""}"
    title="${x.id}">${x.id.replace("-","")}</div>`).join("");
 }catch(error){message.textContent="Không thể kết nối Digital Twin trên máy chủ."}
}
async function action(name){
 await fetch("/api/action",{method:"POST",headers:{"Content-Type":"application/json"},
 body:JSON.stringify({action:name})});refresh();
}
setInterval(refresh,1000);refresh();
</script></body></html>"""


def make_handler(bridge: SharedBridge) -> type[BaseHTTPRequestHandler]:
    class ParkingHandler(BaseHTTPRequestHandler):
        def send_bytes(self, data: bytes, content_type: str, status: int = 200) -> None:
            self.send_response(status)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(data)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(data)

        def do_GET(self) -> None:  # noqa: N802
            if self.path == "/" or self.path.startswith("/?"):
                self.send_bytes(MOBILE_HTML.encode("utf-8"), "text/html; charset=utf-8")
            elif self.path == "/api/status":
                payload = json.dumps(bridge.get_snapshot(), ensure_ascii=False).encode("utf-8")
                self.send_bytes(payload, "application/json; charset=utf-8")
            else:
                self.send_bytes(b"Not found", "text/plain", 404)

        def do_POST(self) -> None:  # noqa: N802
            if self.path != "/api/action":
                self.send_bytes(b"Not found", "text/plain", 404)
                return
            try:
                size = min(int(self.headers.get("Content-Length", "0")), 2048)
                data = json.loads(self.rfile.read(size) or b"{}")
                action = data.get("action")
                if action in {"empty", "mycar"}:
                    bridge.push_action(action)
                self.send_bytes(b'{"ok":true}', "application/json")
            except (ValueError, json.JSONDecodeError):
                self.send_bytes(b'{"ok":false}', "application/json", 400)

        def log_message(self, _format: str, *args: Any) -> None:
            return

    return ParkingHandler


def local_ip() -> str:
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        sock.connect(("8.8.8.8", 80))
        return sock.getsockname()[0]
    except OSError:
        return "127.0.0.1"
    finally:
        sock.close()


def start_web_server(
    bridge: SharedBridge, preferred_port: int
) -> tuple[ThreadingHTTPServer, str]:
    try:
        server = ThreadingHTTPServer(("0.0.0.0", preferred_port), make_handler(bridge))
    except OSError:
        server = ThreadingHTTPServer(("0.0.0.0", 0), make_handler(bridge))
    server.daemon_threads = True
    threading.Thread(target=server.serve_forever, daemon=True).start()
    return server, f"http://{local_ip()}:{server.server_address[1]}"

