from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from api.common import JsonHandler  # noqa: E402
from story_spark.licenses import redeem  # noqa: E402
from story_spark.store import get_store  # noqa: E402


class handler(JsonHandler):
    def do_POST(self) -> None:  # noqa: N802
        try:
            payload = self.read_json(4_000)
            provider = str(payload.get("provider", ""))
            credential = str(payload.get("credential", "")).strip()
            install_id = str(payload.get("install_id", ""))
            if not credential or not install_id.startswith("browser_"):
                raise ValueError("Enter a valid purchase key and browser installation ID.")
            license_key, record = redeem(get_store(), provider, credential, install_id)
            self.respond({"active": True, "license_key": license_key, "source": record.source, "credits": record.credits, "activations": len(record.activations)})
        except ValueError as exc:
            self.respond({"active": False, "error": str(exc)}, 422)
        except Exception:
            self.respond({"active": False, "error": "Purchase verification is temporarily unavailable."}, 502)

