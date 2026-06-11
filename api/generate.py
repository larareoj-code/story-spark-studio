from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from api.common import JsonHandler  # noqa: E402
from story_spark.ai import generate_ai_story  # noqa: E402
from story_spark.generator import generate_free_story  # noqa: E402
from story_spark.models import StoryRequest  # noqa: E402
from story_spark.store import get_store  # noqa: E402


class handler(JsonHandler):
    def do_POST(self) -> None:  # noqa: N802
        license_key = ""
        consumed = False
        try:
            payload = self.read_json()
            request = StoryRequest.model_validate(payload.get("story") or payload)
            if not request.premium:
                return self.respond(generate_free_story(request).model_dump())

            license_key = str(payload.get("license_key", ""))
            install_id = str(payload.get("install_id", ""))
            if not license_key or not install_id:
                return self.respond({"error": "Premium generation requires an active license."}, 403)
            store = get_store()
            remaining = store.consume_credit(license_key, install_id)
            consumed = True
            result = generate_ai_story(request)
            result.credits_remaining = remaining
            self.respond(result.model_dump())
        except ValueError as exc:
            if consumed:
                get_store().restore_credit(license_key)
            self.respond({"error": str(exc)}, 422)
        except Exception:
            if consumed:
                get_store().restore_credit(license_key)
            self.respond({"error": "Premium story generation is temporarily unavailable. Your credit was restored.", "fallback": True}, 502)

