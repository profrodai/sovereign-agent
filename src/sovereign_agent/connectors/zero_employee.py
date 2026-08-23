"""Serialized Zero Employee connector. No Python imports across repositories."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from sovereign_agent.contracts import ExecutionReceipt, GovernedExecutionRequest
from sovereign_agent.contracts._core import canonical_json_bytes
from sovereign_agent.execution.engine import (
    AdmissionRejected,
    ExecutionNotFound,
    GovernedExecutionEngine,
)


class ConnectorError(ValueError):
    pass


@dataclass(frozen=True)
class TransportAck:
    execution_id: str
    request_sha256: str
    acknowledged: bool = True
    receipt_path: str | None = None
    receipt_sha256: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "acknowledged": self.acknowledged,
            "execution_id": self.execution_id,
            "request_sha256": self.request_sha256,
            "receipt_path": self.receipt_path,
            "receipt_sha256": self.receipt_sha256,
        }


class ZeroEmployeeConnector:
    """Accept request bytes or an immutable path; emit receipts as artifacts."""

    def __init__(self, engine: GovernedExecutionEngine) -> None:
        self.engine = engine
        self._pending = engine.runtime.ensure_directory("api") / "connector-inbox"
        self._pending.mkdir(mode=0o700, parents=True, exist_ok=True)

    def probe(self) -> dict[str, Any]:
        return {
            "ok": True,
            "boundary": "serialized-contracts",
            "imports_zero_employee": False,
            "schema": "governed-execution-request.schema.json",
        }

    def load_request(self, source: Path | bytes | str) -> GovernedExecutionRequest:
        if isinstance(source, (bytes, bytearray)):
            payload = json.loads(bytes(source).decode("utf-8"))
        else:
            path = Path(source)
            if not path.is_file() or path.is_symlink():
                raise ConnectorError("request artifact must be a regular file")
            payload = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(payload, dict):
            raise ConnectorError("request must be a JSON object")
        if payload.get("kind") == "governed-execution-request" and isinstance(
            payload.get("body"), dict
        ):
            payload = payload["body"].get("request", payload["body"])
        try:
            return GovernedExecutionRequest.from_dict(payload)
        except (TypeError, ValueError) as exc:
            raise ConnectorError(f"unsupported or malformed governance request: {exc}") from exc

    def submit(self, source: Path | bytes | str) -> TransportAck:
        request = self.load_request(source)
        raw = canonical_json_bytes(request.to_dict())
        digest = hashlib.sha256(raw).hexdigest()
        path = self._pending / f"{digest}.json"
        if not path.exists():
            path.write_bytes(raw)
        return TransportAck(execution_id=str(request.execution_id), request_sha256=digest)

    async def execute(self, source: Path | bytes | str) -> tuple[TransportAck, ExecutionReceipt]:
        request = self.load_request(source)
        ack = self.submit(source)
        try:
            receipt = await self.engine.run(request)
        except AdmissionRejected as exc:
            raise ConnectorError(f"refused before execution: {exc.reason}: {exc.detail}") from exc
        receipt_path = (
            self.engine.runtime.receipts_dir
            / f"{hashlib.sha256(str(request.execution_id).encode()).hexdigest()}.json"
        )
        digest = None
        if receipt_path.exists():
            digest = hashlib.sha256(receipt_path.read_bytes()).hexdigest()
        ack = TransportAck(
            execution_id=ack.execution_id,
            request_sha256=ack.request_sha256,
            receipt_path=str(receipt_path) if receipt_path.exists() else None,
            receipt_sha256=digest,
        )
        return ack, receipt

    def status(self, execution_id: str) -> dict[str, Any]:
        try:
            return self.engine.status(execution_id).to_dict()
        except ExecutionNotFound as exc:
            raise ConnectorError(str(exc)) from exc

    def export_receipt(self, execution_id: str) -> dict[str, Any]:
        receipt = self.engine.receipt(execution_id)
        if receipt is None:
            raise ConnectorError(f"receipt not found: {execution_id}")
        return receipt.to_dict()

    @staticmethod
    def verify_receipt(data: dict[str, Any] | Path) -> dict[str, Any]:
        if isinstance(data, Path):
            payload = json.loads(data.read_text(encoding="utf-8"))
        else:
            payload = data
        receipt = ExecutionReceipt.from_dict(payload)
        ok = receipt.verify_evidence()
        return {
            "valid": ok,
            "execution_id": str(receipt.execution_id),
            "status": receipt.status.value,
            "evidence_sha256": receipt.evidence_sha256,
        }
