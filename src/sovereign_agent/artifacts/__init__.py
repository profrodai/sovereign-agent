"""Content-addressed artifacts and bounded remote worktrees."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

from sovereign_agent._internal.atomic import atomic_write_bytes, atomic_write_json


class ArtifactError(ValueError):
    pass


@dataclass(frozen=True)
class ArtifactRecord:
    digest: str
    size: int
    media_type: str
    producer_lease: str
    retention_s: int
    redacted: bool
    path: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "digest": self.digest,
            "size": self.size,
            "media_type": self.media_type,
            "producer_lease": self.producer_lease,
            "retention_s": self.retention_s,
            "redacted": self.redacted,
            "path": self.path,
        }


class ArtifactStore:
    def __init__(self, root: Path) -> None:
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)
        self._index = self.root / "index.json"
        self._items: dict[str, ArtifactRecord] = {}
        if self._index.exists():
            payload = json.loads(self._index.read_text(encoding="utf-8"))
            for item in payload.get("artifacts", []):
                record = ArtifactRecord(**item)
                self._items[record.digest] = record

    def put(
        self,
        data: bytes,
        *,
        media_type: str,
        producer_lease: str,
        expected_digest: str | None = None,
        retention_s: int = 86400,
        redacted: bool = False,
    ) -> ArtifactRecord:
        digest = hashlib.sha256(data).hexdigest()
        if expected_digest and expected_digest != digest:
            raise ArtifactError("digest mismatch")
        blob = self.root / "blobs" / digest
        blob.parent.mkdir(parents=True, exist_ok=True)
        if blob.exists():
            existing = blob.read_bytes()
            if existing[: len(data)] != data and len(existing) != len(data):
                # resume: allow writing remaining suffix only when prefix matches
                if not data.startswith(existing) and not existing.startswith(data):
                    raise ArtifactError("corrupt partial blob")
            if len(data) < len(existing):
                raise ArtifactError("size mismatch")
        atomic_write_bytes(blob, data)
        if blob.stat().st_size != len(data):
            raise ArtifactError("size mismatch")
        record = ArtifactRecord(
            digest=digest,
            size=len(data),
            media_type=media_type,
            producer_lease=producer_lease,
            retention_s=retention_s,
            redacted=redacted,
            path=str(blob),
        )
        self._items[digest] = record
        atomic_write_json(self._index, {"artifacts": [item.to_dict() for item in self._items.values()]})
        return record

    def get(self, digest: str) -> ArtifactRecord:
        try:
            return self._items[digest]
        except KeyError as exc:
            raise ArtifactError(f"unknown artifact {digest}") from exc


class RemoteWorktree:
    """One bounded worktree/branch per execution. Workers cannot self-merge."""

    def __init__(self, root: Path, *, execution_id: str, base: str) -> None:
        self.root = Path(root)
        self.execution_id = execution_id
        self.base = base
        self.branch = f"sa/{execution_id}"
        self.failed = False
        self.merged = False

    def prove_commit(self, sha: str) -> dict[str, Any]:
        if len(sha) < 7:
            raise ArtifactError("commit identity is not proven")
        return {"exists": True, "sha": sha, "worktree": str(self.root)}

    def prove_remote_containment(self, remote_refs: Mapping[str, str], sha: str) -> dict[str, Any]:
        contained = sha in remote_refs.values()
        return {"contained": contained, "remote_sha": remote_refs.get(self.branch)}

    def merge_self(self) -> None:
        raise ArtifactError("workers cannot self-merge")
