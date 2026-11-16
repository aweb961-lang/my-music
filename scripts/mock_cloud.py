"""Local stand-in for cloud/worker.js, for testing the app without Cloudflare.
Serves a music folder with the same API: /index and /file/<key>, ?k=<key> required, Range supported.
  py scripts/mock_cloud.py <music folder> <access key> [port=8768]
"""
import json, sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse, parse_qs, unquote
from music_files import match_folder

FOLDER, KEY = sys.argv[1], sys.argv[2]
PORT = int(sys.argv[3]) if len(sys.argv) > 3 else 8768

class H(BaseHTTPRequestHandler):
    def cors(self):
        self.send_header("Access-Control-Allow-Origin", self.headers.get("Origin") or "*")
        self.send_header("Access-Control-Allow-Headers", "Range")
        self.send_header("Access-Control-Expose-Headers", "Content-Length, Content-Range, Accept-Ranges")

    def do_OPTIONS(self):
        self.send_response(204); self.cors(); self.end_headers()

    def do_GET(self):
        u = urlparse(self.path)
        if parse_qs(u.query).get("k", [""])[0] != KEY:
            self.send_response(401); self.cors(); self.end_headers(); self.wfile.write(b"Wrong or missing key"); return
        files = {f["key"]: f for f in match_folder(FOLDER)}
        if u.path == "/index":
            body = json.dumps({"files": [{"key": k, "size": f["path"].stat().st_size} for k, f in files.items()]}).encode()
            self.send_response(200); self.cors(); self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body))); self.end_headers(); self.wfile.write(body); return
        if u.path.startswith("/file/"):
            f = files.get(unquote(u.path[6:]))
            if not f:
                self.send_response(404); self.cors(); self.end_headers(); return
            data = f["path"].read_bytes(); size = len(data)
            rng = self.headers.get("Range")
            if rng and rng.startswith("bytes="):
                a, b = rng[6:].split("-")
                start = int(a) if a else size - int(b)
                end = int(b) if a and b else size - 1
                end = min(end, size - 1)
                self.send_response(206); self.send_header("Content-Range", f"bytes {start}-{end}/{size}")
                chunk = data[start:end + 1]
            else:
                self.send_response(200); chunk = data
            self.cors(); self.send_header("Accept-Ranges", "bytes"); self.send_header("Content-Type", f["type"])
            self.send_header("Content-Length", str(len(chunk))); self.end_headers(); self.wfile.write(chunk); return
        self.send_response(404); self.cors(); self.end_headers()

    def log_message(self, *a):
        pass

print(f"mock cloud on http://localhost:{PORT}")
ThreadingHTTPServer(("127.0.0.1", PORT), H).serve_forever()
