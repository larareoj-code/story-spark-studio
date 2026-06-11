from __future__ import annotations

import sys
from pathlib import Path
from urllib.parse import parse_qs, urlparse

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from api.common import JsonHandler  # noqa: E402
from story_spark.store import get_store  # noqa: E402


class handler(JsonHandler):
    def do_GET(self) -> None:  # noqa: N802
        query = parse_qs(urlparse(self.path).query)
        license_key = query.get("license_key", [""])[0]
        install_id = query.get("install_id", [""])[0]
        record = get_store().get(license_key, install_id) if license_key and install_id else None
        self.respond({"active": bool(record), "credits": record.credits if record else 0, "source": record.source if record else None})

