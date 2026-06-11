from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from api.common import JsonHandler  # noqa: E402
from story_spark.analytics import record_event  # noqa: E402


class handler(JsonHandler):
    def do_POST(self) -> None:  # noqa: N802
        try:
            payload = self.read_json(2_000)
            record_event(str(payload.get("event", "")), payload.get("properties") if isinstance(payload.get("properties"), dict) else {})
            self.respond({"recorded": True})
        except ValueError as exc:
            self.respond({"error": str(exc)}, 422)
        except Exception:
            self.respond({"recorded": False}, 202)

