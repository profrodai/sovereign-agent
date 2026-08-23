"""Append-only ZeoCore invocation evidence linked by execution ID."""

from __future__ import annotations

import importlib.metadata
import json
from pathlib import Path
from typing import Any

from zeo_core.contracts.capabilities.invocation import CapabilityInvocationRecord

from sovereign_agent._internal.atomic import atomic_write_json
from sovereign_agent._internal.hashed import bind_hashed
from sovereign_agent.contracts.redaction import REDACTED, redact_json, redact_text

INVOCATIONS_DIR = Path("capabilities") / "invocations"


def invocations_dir(session_dir: Path) -> Path:
    path = Path(session_dir) / INVOCATIONS_DIR
    path.mkdir(parents=True, exist_ok=True)
    return path


def persist_invocation_evidence(
    session_dir: Path,
    *,
    execution_id: str,
    record: CapabilityInvocationRecord,
    catalog_digest: str,
    schema_digest: str,
    definition_digest: str,
    effects: str,
    requirements: dict[str, Any],
    approval_id: str | None,
    lock_evidence: str | None,
    outcome: str,
) -> str:
    """Write a redacted invocation record. Returns a stable relative ref."""
    payload = {
        "execution_id": execution_id,
        "invocation_id": record.invocation_id,
        "canonical_id": record.capability_id.canonical(),
        "catalog_digest": catalog_digest,
        "schema_digest": schema_digest,
        "definition_digest": definition_digest,
        "request_digest": record.request_digest,
        "result_digest": record.result_digest,
        "outcome": outcome,
        "status": record.status.value if hasattr(record.status, "value") else str(record.status),
        "error_code": record.error_code,
        "started_at": record.started_at.isoformat(),
        "ended_at": record.ended_at.isoformat() if record.ended_at else None,
        "effects": effects,
        "requirements": redact_json(requirements),
        "approval_id": approval_id,
        "lock_evidence": lock_evidence,
        "artifact_refs": [str(ref) for ref in record.artifact_refs],
        "redactions": list(record.redactions) + [REDACTED],
        "package_versions": {
            "sovereign-agent": importlib.metadata.version("sovereign-agent"),
            "zeocore": importlib.metadata.version("zeocore"),
        },
    }
    relative = f"{INVOCATIONS_DIR.as_posix()}/{_file_name(record.invocation_id)}"
    path = bind_hashed(invocations_dir(session_dir), record.invocation_id)
    atomic_write_json(path, payload)
    return relative


def _file_name(invocation_id: str) -> str:
    return bind_hashed(Path("."), invocation_id).name


def load_invocation_evidence(session_dir: Path, invocation_id: str) -> dict[str, Any]:
    path = bind_hashed(invocations_dir(session_dir), invocation_id)
    return json.loads(path.read_text(encoding="utf-8"))


def list_invocation_refs(session_dir: Path) -> tuple[str, ...]:
    root = Path(session_dir) / INVOCATIONS_DIR
    if not root.exists():
        return ()
    refs = []
    for path in sorted(root.glob("*.json")):
        payload = json.loads(path.read_text(encoding="utf-8"))
        refs.append(f"{INVOCATIONS_DIR.as_posix()}/{path.name}")
        _ = payload
    return tuple(refs)


def verify_receipt_invocation_linkage(
    session_dir: Path,
    *,
    catalog_digest: str | None,
    invocation_refs: tuple[str, ...],
) -> None:
    for ref in invocation_refs:
        path = Path(session_dir) / ref
        if not path.is_file():
            raise FileNotFoundError(f"missing invocation evidence {ref}")
        payload = json.loads(path.read_text(encoding="utf-8"))
        if catalog_digest and payload.get("catalog_digest") != catalog_digest:
            raise ValueError("invocation catalog digest does not match receipt")
        blob = json.dumps(payload)
        if any(marker in blob.lower() for marker in ("sk-", "bearer ", "api_key=")):
            raise ValueError("invocation evidence appears to contain a secret")
        redact_text(blob)


def invocation_already_recorded(session_dir: Path, invocation_id: str) -> bool:
    return bind_hashed(invocations_dir(session_dir), invocation_id).exists()
