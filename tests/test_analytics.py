import pytest

from story_spark.analytics import record_event


def test_known_event_is_noop_without_redis(monkeypatch):
    monkeypatch.delenv("UPSTASH_REDIS_REST_URL", raising=False)
    monkeypatch.delenv("UPSTASH_REDIS_REST_TOKEN", raising=False)
    assert record_event("story_completed", {"mode": "bedtime"}) is None


def test_unknown_event_is_rejected():
    with pytest.raises(ValueError):
        record_event("child_name_entered")

