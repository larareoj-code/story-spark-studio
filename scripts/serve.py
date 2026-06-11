from __future__ import annotations

import argparse
import json
import os
import sys
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
for env_path in (ROOT.parent.parent / ".env.local", ROOT / ".env.local"):
    if env_path.exists():
        for line in env_path.read_text(encoding="utf-8").splitlines():
            if line and not line.startswith("#") and "=" in line:
                key, value = line.split("=", 1)
                os.environ.setdefault(key.strip(), value.strip())

from api.checkout import public_origin
from story_spark.ai import generate_ai_story
from story_spark.generator import generate_free_story
from story_spark.licenses import redeem
from story_spark.models import StoryRequest
from story_spark.store import get_store


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(ROOT / "web"), **kwargs)

    def json_response(self, payload: object, status: int = 200):
        body = json.dumps(payload).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def payload(self):
        return json.loads(self.rfile.read(int(self.headers.get("Content-Length", "0"))) or b"{}")

    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path == "/api/health":
            return self.json_response({"status": "ok", "product": "story-spark-studio", "version": 1})
        if parsed.path == "/api/license":
            query = parse_qs(parsed.query)
            record = get_store().get(query.get("license_key", [""])[0], query.get("install_id", [""])[0])
            return self.json_response({"active": bool(record), "credits": record.credits if record else 0})
        if parsed.path.startswith("/assets/"):
            self.path = parsed.path.removeprefix("/assets/")
        return super().do_GET()

    def do_POST(self):
        try:
            payload = self.payload()
            if self.path == "/api/generate":
                request = StoryRequest.model_validate(payload.get("story") or payload)
                if not request.premium:
                    return self.json_response(generate_free_story(request).model_dump())
                key, install = str(payload.get("license_key", "")), str(payload.get("install_id", ""))
                remaining = get_store().consume_credit(key, install)
                try:
                    result = generate_ai_story(request)
                    result.credits_remaining = remaining
                    return self.json_response(result.model_dump())
                except Exception:
                    get_store().restore_credit(key)
                    return self.json_response({"error": "Premium story generation is temporarily unavailable. Your credit was restored.", "fallback": True}, 502)
            if self.path == "/api/redeem":
                key, record = redeem(get_store(), str(payload.get("provider", "")), str(payload.get("credential", "")), str(payload.get("install_id", "")))
                return self.json_response({"active": True, "license_key": key, "credits": record.credits, "source": record.source})
            if self.path == "/api/checkout":
                import stripe
                stripe.api_key = os.environ["STRIPE_SECRET_KEY"]
                target = public_origin(f"http://{self.headers.get('Host')}")
                session = stripe.checkout.Session.create(mode="payment", line_items=[{"price": os.environ["STRIPE_PRICE_LIFETIME"], "quantity": 1}], success_url=f"{target}/?checkout=success&session_id={{CHECKOUT_SESSION_ID}}", cancel_url=f"{target}/?checkout=cancelled", metadata={"app": "story-spark-studio"})
                return self.json_response({"url": session.url})
        except ValueError as exc:
            return self.json_response({"error": str(exc)}, 422)
        except Exception:
            return self.json_response({"error": "Request failed."}, 500)
        self.send_error(404)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=8810)
    args = parser.parse_args()
    ThreadingHTTPServer(("127.0.0.1", args.port), Handler).serve_forever()

