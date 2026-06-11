from __future__ import annotations

import os
import sys
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from api.common import JsonHandler  # noqa: E402


def public_origin(request_origin: str) -> str:
    configured = os.getenv("APP_URL", "").strip().rstrip("/")
    parsed = urlparse(configured or request_origin)
    if parsed.scheme == "https" and parsed.netloc:
        return f"{parsed.scheme}://{parsed.netloc}"
    if parsed.scheme == "http" and parsed.hostname in {"localhost", "127.0.0.1"}:
        return f"{parsed.scheme}://{parsed.netloc}"
    raise ValueError("APP_URL must be configured before checkout is enabled.")


class handler(JsonHandler):
    def do_POST(self) -> None:  # noqa: N802
        try:
            payload = self.read_json(2_000)
            install_id = str(payload.get("install_id", ""))
            if not install_id.startswith("browser_") or len(install_id) > 96:
                raise ValueError("A valid browser installation ID is required.")
            import stripe

            stripe.api_key = os.environ["STRIPE_SECRET_KEY"]
            target = public_origin(f"{self.headers.get('x-forwarded-proto', 'https')}://{self.headers.get('host', '')}")
            session = stripe.checkout.Session.create(
                mode="payment",
                line_items=[{"price": os.environ["STRIPE_PRICE_LIFETIME"], "quantity": 1}],
                allow_promotion_codes=True,
                success_url=f"{target}/?checkout=success&session_id={{CHECKOUT_SESSION_ID}}",
                cancel_url=f"{target}/?checkout=cancelled",
                metadata={"app": "story-spark-studio", "license": "25-ai-stories", "install_id": install_id},
            )
            self.respond({"url": session.url})
        except ValueError as exc:
            self.respond({"error": str(exc)}, 422)
        except Exception:
            self.respond({"error": "Checkout could not be started."}, 502)

