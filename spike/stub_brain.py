"""Stub of the brain's approve endpoint for the Action spike. Logs each call as one JSON line; never logs the secret."""

import json
import sys
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

ENV = Path(__file__).parent / ".env"
LOG = Path(__file__).parent / "stub_brain.log"


def secret():
    kv = dict(line.split("=", 1) for line in ENV.read_text().splitlines() if "=" in line)
    return kv["SPIKE_SERVICE_SECRET"]


class Handler(BaseHTTPRequestHandler):
    def do_POST(self):
        body = json.loads(self.rfile.read(int(self.headers.get("Content-Length", 0))) or b"{}")
        ok_secret = self.headers.get("X-Service-Secret") == secret()
        parts = self.path.strip("/").split("/")
        key = parts[1] if len(parts) == 3 and parts[0] == "actions" and parts[2] == "approve" else None
        status = "approved" if ok_secret and key else "refused"
        with LOG.open("a", encoding="utf-8") as f:
            f.write(json.dumps({"path": self.path, "secret_ok": ok_secret, "key": key, **body, "status": status}) + "\n")
        out = json.dumps({"status": status, "key": key}).encode()
        self.send_response(200 if status == "approved" else 403)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(out)

    def log_message(self, *args):
        pass


if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8766
    HTTPServer(("127.0.0.1", port), Handler).serve_forever()
