from __future__ import annotations

from api.common import JsonHandler
from story_spark.store import persistent_store_configured



class handler(JsonHandler):
    def do_GET(self) -> None:  # noqa: N802
        self.respond(
            {
                "status": "ok",
                "product": "story-spark-studio",
                "version": 1,
                "premium_ready": persistent_store_configured(),
            }
        )
