import pytest

from story_spark.store import MemoryLicenseStore, hash_license, persistent_store_configured


def test_license_hash_is_not_plaintext():
    assert hash_license("secret-key") != "secret-key"
    assert len(hash_license("secret-key")) == 64


def test_activation_limit_and_credit_accounting():
    store = MemoryLicenseStore()
    key = "SSS-license"
    for index in range(3):
        store.activate(key, "stripe", f"browser_{index:016d}")
    with pytest.raises(ValueError):
        store.activate(key, "stripe", "browser_9999999999999999")
    assert store.consume_credit(key, "browser_0000000000000000") == 24
    assert store.restore_credit(key) == 25


def test_duplicate_activation_does_not_consume_slot():
    store = MemoryLicenseStore()
    record = store.activate("SSS-license", "gumroad", "browser_0000000000000000")
    record = store.activate("SSS-license", "gumroad", "browser_0000000000000000")
    assert len(record.activations) == 1


def test_exhausted_credits_fail():
    store = MemoryLicenseStore()
    record = store.activate("SSS-license", "payhip", "browser_0000000000000000")
    record.credits = 0
    with pytest.raises(ValueError):
        store.consume_credit("SSS-license", "browser_0000000000000000")


def test_persistent_store_requires_both_credentials(monkeypatch):
    monkeypatch.delenv("UPSTASH_REDIS_REST_URL", raising=False)
    monkeypatch.delenv("UPSTASH_REDIS_REST_TOKEN", raising=False)
    assert persistent_store_configured() is False
    monkeypatch.setenv("UPSTASH_REDIS_REST_URL", "https://example.invalid")
    assert persistent_store_configured() is False
    monkeypatch.setenv("UPSTASH_REDIS_REST_TOKEN", "token")
    assert persistent_store_configured() is True
