from __future__ import annotations

from api.common import JsonHandler



class handler(JsonHandler):
    def do_GET(self) -> None:  # noqa: N802
        self.respond({"status": "ok", "product": "story-spark-studio", "version": 1})
