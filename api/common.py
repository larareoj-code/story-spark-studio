from __future__ import annotations

import json
from http.server import BaseHTTPRequestHandler


class JsonHandler(BaseHTTPRequestHandler):
    def respond(self, payload: object, status: int = 200) -> None:
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def read_json(self, limit: int = 20_000) -> dict[str, object]:
        length = int(self.headers.get("Content-Length", "0"))
        if length > limit:
            raise ValueError("Request is too large.")
        payload = json.loads(self.rfile.read(length) or b"{}")
        if not isinstance(payload, dict):
            raise ValueError("Expected a JSON object.")
        return payload

