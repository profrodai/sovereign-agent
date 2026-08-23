"""Filesystem idempotency ledger for authenticated mutations."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

from sovereign_agent._internal.atomic import atomic_write_bytes
from sovereign_agent._internal.file_lock import exclusive_file_lock
from sovereign_agent._internal.hashed import bind_hashed
from sovereign_agent.contracts._core import canonical_json_bytes
from sovereign_agent.runtime import RuntimeRoot

from .envelope import ProtocolError


class IdempotencyConflict(ProtocolError):
    def __init__(self, key: str) -> None:
        super().__init__(
            "idempotency-conflict", detail=f"idempotency key reused with different body: {key}"
        )


@dataclass
class IdempotencyRecord:
    key: str
    body_sha256: str
    result: dict[str, Any]
    stored_at: str


class IdempotencyLedger:
    def __init__(self, runtime_root: RuntimeRoot) -> None:
        self.runtime_root = runtime_root
        self._dir = runtime_root.ensure_directory("api") / "idempotency"
        self._dir.mkdir(mode=0o700, parents=True, exist_ok=True)
        self._lock = runtime_root.locks_dir / "idempotency.lock"

    def remember(self, key: str, body: object, result: dict[str, Any]) -> dict[str, Any]:
        if not key:
            raise ProtocolError("malformed-envelope", detail="idempotency_key is required")
        digest = _body_digest(body)
        path = bind_hashed(self._dir, key)
        with exclusive_file_lock(self._lock):
            if path.exists():
                record = json.loads(path.read_text(encoding="utf-8"))
                if record.get("body_sha256") != digest:
                    raise IdempotencyConflict(key)
                stored = record.get("result")
                if not isinstance(stored, dict):
                    raise ProtocolError("malformed-envelope", detail="corrupt idempotency record")
                return stored
            payload = {
                "key": key,
                "body_sha256": digest,
                "result": result,
                "stored_at": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
            }
            atomic_write_bytes(path, canonical_json_bytes(payload))
        return result

    def get(self, key: str) -> dict[str, Any] | None:
        path = bind_hashed(self._dir, key)
        if not path.exists():
            return None
        record = json.loads(path.read_text(encoding="utf-8"))
        result = record.get("result")
        return result if isinstance(result, dict) else None


def _body_digest(body: object) -> str:
    import hashlib

    return hashlib.sha256(canonical_json_bytes(body)).hexdigest()
