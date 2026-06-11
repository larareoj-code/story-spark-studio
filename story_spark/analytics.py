from __future__ import annotations

import datetime as dt
import json
import os
import urllib.request


ALLOWED_EVENTS = {
    "story_completed",
    "premium_attempted",
    "upgrade_clicked",
    "purchase_redeemed",
    "story_saved",
    "print_started",
    "generation_failed",
}


def record_event(event: str, properties: dict[str, str | int | bool] | None = None) -> None:
    if event not in ALLOWED_EVENTS:
        raise ValueError("Unsupported analytics event.")
    url = os.getenv("UPSTASH_REDIS_REST_URL", "").rstrip("/")
    token = os.getenv("UPSTASH_REDIS_REST_TOKEN", "")
    if not url or not token:
        return
    day = dt.datetime.now(dt.UTC).date().isoformat()
    key = f"sss:metrics:{day}"
    commands = [["HINCRBY", key, event, 1]]
    for name, value in (properties or {}).items():
        if name in {"generation", "mode", "source", "status"}:
            commands.append(["HINCRBY", key, f"{event}:{name}:{value}", 1])
    request = urllib.request.Request(f"{url}/pipeline", data=json.dumps(commands).encode(), headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"})
    with urllib.request.urlopen(request, timeout=5):
        pass

