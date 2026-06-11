from __future__ import annotations

import hashlib
import json
import os
import threading
import time
import urllib.request
from dataclasses import dataclass, field
from typing import Protocol


def hash_license(value: str) -> str:
    secret = os.getenv("LICENSE_SECRET", "local-development-secret")
    return hashlib.sha256(f"{secret}:{value}".encode()).hexdigest()


@dataclass
class LicenseRecord:
    source: str
    credits: int = 25
    activations: set[str] = field(default_factory=set)
    created_at: int = field(default_factory=lambda: int(time.time()))
    updated_at: int = field(default_factory=lambda: int(time.time()))


class LicenseStore(Protocol):
    def activate(self, license_key: str, source: str, install_id: str) -> LicenseRecord: ...
    def get(self, license_key: str, install_id: str) -> LicenseRecord | None: ...
    def consume_credit(self, license_key: str, install_id: str) -> int: ...
    def restore_credit(self, license_key: str) -> int: ...


class MemoryLicenseStore:
    def __init__(self) -> None:
        self.records: dict[str, LicenseRecord] = {}
        self.lock = threading.Lock()

    def activate(self, license_key: str, source: str, install_id: str) -> LicenseRecord:
        with self.lock:
            key = hash_license(license_key)
            record = self.records.setdefault(key, LicenseRecord(source=source))
            if install_id not in record.activations and len(record.activations) >= 3:
                raise ValueError("This license is already active in three browsers.")
            record.activations.add(install_id)
            record.updated_at = int(time.time())
            return record

    def get(self, license_key: str, install_id: str) -> LicenseRecord | None:
        record = self.records.get(hash_license(license_key))
        return record if record and install_id in record.activations else None

    def consume_credit(self, license_key: str, install_id: str) -> int:
        with self.lock:
            record = self.get(license_key, install_id)
            if not record or record.credits <= 0:
                raise ValueError("No AI story credits remain for this license.")
            record.credits -= 1
            record.updated_at = int(time.time())
            return record.credits

    def restore_credit(self, license_key: str) -> int:
        with self.lock:
            record = self.records.get(hash_license(license_key))
            if not record:
                raise ValueError("License not found.")
            record.credits = min(25, record.credits + 1)
            record.updated_at = int(time.time())
            return record.credits


class UpstashLicenseStore:
    def __init__(self) -> None:
        self.url = os.environ["UPSTASH_REDIS_REST_URL"].rstrip("/")
        self.token = os.environ["UPSTASH_REDIS_REST_TOKEN"]

    def _command(self, *parts: object) -> object:
        request = urllib.request.Request(self.url, data=json.dumps(list(parts)).encode(), headers={"Authorization": f"Bearer {self.token}", "Content-Type": "application/json"})
        with urllib.request.urlopen(request, timeout=8) as response:
            payload = json.load(response)
        if payload.get("error"):
            raise RuntimeError(payload["error"])
        return payload.get("result")

    def _key(self, license_key: str) -> str:
        return f"sss:license:{hash_license(license_key)}"

    def activate(self, license_key: str, source: str, install_id: str) -> LicenseRecord:
        key = self._key(license_key)
        script = """local exists=redis.call('SISMEMBER',KEYS[2],ARGV[1]); local count=redis.call('SCARD',KEYS[2]); if exists==0 and count>=3 then return {-1,count} end; redis.call('SADD',KEYS[2],ARGV[1]); redis.call('HSETNX',KEYS[1],'credits',25); redis.call('HSETNX',KEYS[1],'source',ARGV[2]); redis.call('HSETNX',KEYS[1],'created_at',ARGV[3]); redis.call('HSET',KEYS[1],'updated_at',ARGV[3]); return {tonumber(redis.call('HGET',KEYS[1],'credits')),redis.call('SCARD',KEYS[2])}"""
        result = self._command("EVAL", script, 2, key, f"{key}:activations", install_id, source, int(time.time()))
        if result[0] == -1:
            raise ValueError("This license is already active in three browsers.")
        return self.get(license_key, install_id)  # type: ignore[return-value]

    def get(self, license_key: str, install_id: str) -> LicenseRecord | None:
        key = self._key(license_key)
        if int(self._command("SISMEMBER", f"{key}:activations", install_id) or 0) != 1:
            return None
        values = self._command("HMGET", key, "source", "credits", "created_at", "updated_at")
        activations = set(self._command("SMEMBERS", f"{key}:activations") or [])
        return LicenseRecord(source=values[0], credits=int(values[1]), activations=activations, created_at=int(values[2]), updated_at=int(values[3]))

    def consume_credit(self, license_key: str, install_id: str) -> int:
        key = self._key(license_key)
        script = """if redis.call('SISMEMBER',KEYS[2],ARGV[1])==0 then return -2 end; local credits=tonumber(redis.call('HGET',KEYS[1],'credits') or '0'); if credits<=0 then return -1 end; return redis.call('HINCRBY',KEYS[1],'credits',-1)"""
        result = int(self._command("EVAL", script, 2, key, f"{key}:activations", install_id))
        if result < 0:
            raise ValueError("No AI story credits remain for this license." if result == -1 else "License is not active in this browser.")
        return result

    def restore_credit(self, license_key: str) -> int:
        key = self._key(license_key)
        script = """local credits=tonumber(redis.call('HGET',KEYS[1],'credits') or '0'); if credits<25 then return redis.call('HINCRBY',KEYS[1],'credits',1) end; return credits"""
        return int(self._command("EVAL", script, 1, key))


_memory_store = MemoryLicenseStore()


def get_store() -> LicenseStore:
    if os.getenv("UPSTASH_REDIS_REST_URL") and os.getenv("UPSTASH_REDIS_REST_TOKEN"):
        return UpstashLicenseStore()
    return _memory_store

