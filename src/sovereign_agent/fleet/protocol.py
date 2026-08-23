"""Versioned worker protocol, fencing tokens, and sequenced acknowledgements."""

from __future__ import annotations

import json
import secrets
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any, Mapping

PROTOCOL_VERSION = "1.0"
PROTOCOL_VERSIONS_SUPPORTED = frozenset({"1.0"})
MAX_FRAME_BYTES = 8 * 1024 * 1024


class ProtocolError(ValueError):
    """A worker protocol frame is invalid, stale, or out of sequence."""


class MessageKind(StrEnum):
    REGISTER = "register"
    PROBE = "probe"
    DISPATCH = "dispatch"
    HEARTBEAT = "heartbeat"
    EVENT = "event"
    ARTIFACT = "artifact"
    COMPLETION = "completion"
    CANCEL = "cancel"
    ACK = "ack"


class ChannelClass(StrEnum):
    CANONICAL = "canonical"
    QUARANTINE = "quarantine"


@dataclass(frozen=True)
class FencingToken:
    generation: int
    nonce: str

    def __post_init__(self) -> None:
        if self.generation < 1:
            raise ProtocolError("fencing generation must be >= 1")
        if not self.nonce:
            raise ProtocolError("fencing nonce must be non-empty")

    def next_token(self) -> FencingToken:
        return FencingToken(generation=self.generation + 1, nonce=secrets.token_hex(16))

    def dominates(self, other: FencingToken) -> bool:
        return self.generation > other.generation

    def to_dict(self) -> dict[str, Any]:
        return {"generation": self.generation, "nonce": self.nonce}

    @classmethod
    def mint(cls, generation: int = 1) -> FencingToken:
        return cls(generation=generation, nonce=secrets.token_hex(16))

    @classmethod
    def from_dict(cls, value: Mapping[str, Any]) -> FencingToken:
        return cls(generation=int(value["generation"]), nonce=str(value["nonce"]))

    from_dict = from_dict


@dataclass(frozen=True)
class WorkerIdentity:
    worker_id: str
    process_instance: str
    host: str
    backend: str
    package_version: str
    protocol_version: str = PROTOCOL_VERSION
    fencing: FencingToken = field(default_factory=FencingToken.mint)

    def __post_init__(self) -> None:
        if self.protocol_version not in PROTOCOL_VERSIONS_SUPPORTED:
            raise ProtocolError(f"unsupported protocol version {self.protocol_version}")
        for name in ("worker_id", "process_instance", "host", "backend", "package_version"):
            if not getattr(self, name):
                raise ProtocolError(f"{name} must be non-empty")

    def to_dict(self) -> dict[str, Any]:
        return {
            "worker_id": self.worker_id,
            "process_instance": self.process_instance,
            "host": self.host,
            "backend": self.backend,
            "package_version": self.package_version,
            "protocol_version": self.protocol_version,
            "fencing": self.fencing.to_dict(),
        }

    @classmethod
    def from_dict(cls, value: Mapping[str, Any]) -> WorkerIdentity:
        return cls(
            worker_id=str(value["worker_id"]),
            process_instance=str(value["process_instance"]),
            host=str(value["host"]),
            backend=str(value["backend"]),
            package_version=str(value["package_version"]),
            protocol_version=str(value.get("protocol_version", PROTOCOL_VERSION)),
            fencing=FencingToken.from_dict(value["fencing"]),
        )


@dataclass(frozen=True)
class WorkerLease:
    lease_id: str
    execution_id: str
    worker_id: str
    fencing: FencingToken
    expires_at_s: float

    def to_dict(self) -> dict[str, Any]:
        return {
            "lease_id": self.lease_id,
            "execution_id": self.execution_id,
            "worker_id": self.worker_id,
            "fencing": self.fencing.to_dict(),
            "expires_at_s": self.expires_at_s,
        }

    @classmethod
    def from_dict(cls, value: Mapping[str, Any]) -> WorkerLease:
        return cls(
            lease_id=str(value["lease_id"]),
            execution_id=str(value["execution_id"]),
            worker_id=str(value["worker_id"]),
            fencing=FencingToken.from_dict(value["fencing"]),
            expires_at_s=float(value["expires_at_s"]),
        )


def encode_frame(payload: Mapping[str, Any]) -> bytes:
    body = json.dumps(payload, separators=(",", ":"), sort_keys=True).encode("utf-8")
    if len(body) > MAX_FRAME_BYTES:
        raise ProtocolError("frame exceeds size bound")
    return f"{len(body):08x}".encode("ascii") + body


def decode_frame(buffer: bytes) -> tuple[dict[str, Any], bytes]:
    if len(buffer) < 8:
        return {}, buffer
    try:
        length = int(buffer[:8].decode("ascii"), 16)
    except ValueError as exc:
        raise ProtocolError("invalid frame length prefix") from exc
    if length > MAX_FRAME_BYTES:
        raise ProtocolError("frame exceeds size bound")
    if len(buffer) < 8 + length:
        return {}, buffer
    payload = json.loads(buffer[8 : 8 + length].decode("utf-8"))
    if not isinstance(payload, dict):
        raise ProtocolError("frame payload must be an object")
    return payload, buffer[8 + length :]


def _base(
    kind: MessageKind,
    *,
    seq: int,
    worker_id: str,
    channel: ChannelClass = ChannelClass.CANONICAL,
) -> dict[str, Any]:
    if seq < 0:
        raise ProtocolError("seq must be >= 0")
    return {
        "kind": kind.value,
        "protocol_version": PROTOCOL_VERSION,
        "seq": seq,
        "worker_id": worker_id,
        "channel": channel.value,
    }


@dataclass(frozen=True)
class RegisterMessage:
    identity: WorkerIdentity
    seq: int = 0
    manifest: Mapping[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        payload = _base(MessageKind.REGISTER, seq=self.seq, worker_id=self.identity.worker_id)
        payload["identity"] = self.identity.to_dict()
        payload["manifest"] = dict(self.manifest)
        return payload


@dataclass(frozen=True)
class ProbeMessage:
    worker_id: str
    seq: int
    claims: Mapping[str, Any]
    evidence: Mapping[str, Any]

    def to_dict(self) -> dict[str, Any]:
        payload = _base(MessageKind.PROBE, seq=self.seq, worker_id=self.worker_id)
        payload["claims"] = dict(self.claims)
        payload["evidence"] = dict(self.evidence)
        return payload


@dataclass(frozen=True)
class DispatchMessage:
    lease: WorkerLease
    seq: int
    catalog_digest: str
    invocation: Mapping[str, Any]
    constraints: Mapping[str, Any]

    def to_dict(self) -> dict[str, Any]:
        payload = _base(MessageKind.DISPATCH, seq=self.seq, worker_id=self.lease.worker_id)
        payload["lease"] = self.lease.to_dict()
        payload["catalog_digest"] = self.catalog_digest
        payload["invocation"] = dict(self.invocation)
        payload["constraints"] = dict(self.constraints)
        return payload


@dataclass(frozen=True)
class HeartbeatMessage:
    worker_id: str
    seq: int
    fencing: FencingToken
    lease_id: str | None = None

    def to_dict(self) -> dict[str, Any]:
        payload = _base(MessageKind.HEARTBEAT, seq=self.seq, worker_id=self.worker_id)
        payload["fencing"] = self.fencing.to_dict()
        payload["lease_id"] = self.lease_id
        return payload


@dataclass(frozen=True)
class EventMessage:
    worker_id: str
    seq: int
    lease: WorkerLease
    name: str
    payload: Mapping[str, Any]
    channel: ChannelClass = ChannelClass.CANONICAL

    def to_dict(self) -> dict[str, Any]:
        body = _base(
            MessageKind.EVENT, seq=self.seq, worker_id=self.worker_id, channel=self.channel
        )
        body["lease"] = self.lease.to_dict()
        body["name"] = self.name
        body["payload"] = dict(self.payload)
        return body


@dataclass(frozen=True)
class ArtifactMessage:
    worker_id: str
    seq: int
    lease: WorkerLease
    digest: str
    size: int
    media_type: str
    channel: ChannelClass = ChannelClass.CANONICAL

    def to_dict(self) -> dict[str, Any]:
        body = _base(
            MessageKind.ARTIFACT, seq=self.seq, worker_id=self.worker_id, channel=self.channel
        )
        body["lease"] = self.lease.to_dict()
        body["digest"] = self.digest
        body["size"] = self.size
        body["media_type"] = self.media_type
        return body


@dataclass(frozen=True)
class CompletionMessage:
    worker_id: str
    seq: int
    lease: WorkerLease
    status: str
    result: Mapping[str, Any]
    channel: ChannelClass = ChannelClass.CANONICAL

    def to_dict(self) -> dict[str, Any]:
        body = _base(
            MessageKind.COMPLETION, seq=self.seq, worker_id=self.worker_id, channel=self.channel
        )
        body["lease"] = self.lease.to_dict()
        body["status"] = self.status
        body["result"] = dict(self.result)
        return body


@dataclass(frozen=True)
class CancelMessage:
    worker_id: str
    seq: int
    lease: WorkerLease
    reason: str

    def to_dict(self) -> dict[str, Any]:
        payload = _base(MessageKind.CANCEL, seq=self.seq, worker_id=self.worker_id)
        payload["lease"] = self.lease.to_dict()
        payload["reason"] = self.reason
        return payload


@dataclass(frozen=True)
class Ack:
    worker_id: str
    seq: int
    last_ok_seq: int

    def to_dict(self) -> dict[str, Any]:
        payload = _base(MessageKind.ACK, seq=self.seq, worker_id=self.worker_id)
        payload["last_ok_seq"] = self.last_ok_seq
        return payload


CANONICAL_KINDS = frozenset(
    {MessageKind.EVENT.value, MessageKind.ARTIFACT.value, MessageKind.COMPLETION.value}
)


class ProtocolSession:
    """Tracks last-ack and fencing for one worker connection."""

    def __init__(self, identity: WorkerIdentity, *, now_s: float) -> None:
        self.identity = identity
        self.last_ok_seq = -1
        self.expired = False
        self.connected_at_s = now_s
        self._seen_completions: set[str] = set()

    def require_canonical(self, payload: Mapping[str, Any], lease: WorkerLease | None) -> None:
        kind = payload.get("kind")
        channel = payload.get("channel", ChannelClass.CANONICAL.value)
        if kind not in CANONICAL_KINDS:
            return
        if self.expired or channel == ChannelClass.QUARANTINE.value:
            if channel != ChannelClass.QUARANTINE.value:
                raise ProtocolError("expired worker may only use the quarantine channel")
            return
        if lease is None:
            raise ProtocolError("canonical message requires a current lease")
        fencing = FencingToken.from_dict(payload.get("lease", {}).get("fencing", {}))
        if fencing.generation != lease.fencing.generation or fencing.nonce != lease.fencing.nonce:
            raise ProtocolError("stale fencing token cannot mutate canonical state")
        if payload.get("worker_id") != lease.worker_id:
            raise ProtocolError("worker_id does not match lease")

    def observe(self, payload: Mapping[str, Any]) -> Ack:
        seq = int(payload["seq"])
        if seq != self.last_ok_seq + 1:
            raise ProtocolError(f"sequence gap: expected {self.last_ok_seq + 1}, got {seq}")
        self.last_ok_seq = seq
        return Ack(worker_id=str(payload["worker_id"]), seq=seq, last_ok_seq=seq)

    def resume_from(self, last_ok_seq: int) -> None:
        self.last_ok_seq = last_ok_seq

    def mark_expired(self) -> None:
        self.expired = True

    def note_completion(self, execution_id: str) -> None:
        if execution_id in self._seen_completions:
            raise ProtocolError("duplicate completion for execution")
        self._seen_completions.add(execution_id)


RegisterMessage = RegisterMessage
ProbeMessage = ProbeMessage
DispatchMessage = DispatchMessage
HeartbeatMessage = HeartbeatMessage
EventMessage = EventMessage
ArtifactMessage = ArtifactMessage
CompletionMessage = CompletionMessage
CancelMessage = CancelMessage
encode_frame = encode_frame
decode_frame = decode_frame
ProtocolSession = ProtocolSession
WorkerIdentity = WorkerIdentity
WorkerLease = WorkerLease
