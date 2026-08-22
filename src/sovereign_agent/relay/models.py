"""Immutable relay envelopes and fenced delivery records."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any

from sovereign_agent.contracts._core import (
    FrozenDict,
    format_datetime,
    freeze_json,
    parse_datetime,
    require_string,
    thaw_json,
)
from sovereign_agent.contracts.ids import RelayMessageId
from sovereign_agent.registry import RuntimeAddress
from sovereign_agent.registry.models import validate_runtime_identifier

RELAY_SCHEMA_VERSION = 1


class DeliveryStatus(StrEnum):
    PENDING = "pending"
    CLAIMED = "claimed"
    ACKNOWLEDGED = "acknowledged"
    DEAD_LETTERED = "dead_lettered"


@dataclass(frozen=True)
class RelayMessage:
    message_id: RelayMessageId
    sender: RuntimeAddress
    recipient: RuntimeAddress
    kind: str
    payload: FrozenDict
    created_at: datetime
    correlation_id: str | None = None
    causation_id: RelayMessageId | None = None
    schema_version: int = RELAY_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if not isinstance(self.message_id, RelayMessageId):
            object.__setattr__(self, "message_id", RelayMessageId(str(self.message_id)))
        validate_runtime_identifier(self.message_id.value, "message_id")
        if not isinstance(self.sender, RuntimeAddress):
            object.__setattr__(self, "sender", RuntimeAddress(str(self.sender)))
        if not isinstance(self.recipient, RuntimeAddress):
            object.__setattr__(self, "recipient", RuntimeAddress(str(self.recipient)))
        if not isinstance(self.kind, str) or not self.kind:
            raise ValueError("message kind must be non-empty")
        frozen = freeze_json(self.payload, path="payload")
        if not isinstance(frozen, FrozenDict):
            raise ValueError("payload must be a JSON object")
        object.__setattr__(self, "payload", frozen)
        if self.created_at.tzinfo is None or self.created_at.utcoffset() is None:
            raise ValueError("created_at must be timezone-aware")
        object.__setattr__(self, "created_at", self.created_at.astimezone(UTC))
        if self.correlation_id is not None and not self.correlation_id:
            raise ValueError("correlation_id must not be empty")
        if self.causation_id is not None and not isinstance(self.causation_id, RelayMessageId):
            object.__setattr__(self, "causation_id", RelayMessageId(str(self.causation_id)))
        if self.causation_id is not None:
            validate_runtime_identifier(self.causation_id.value, "causation_id")
        if self.schema_version != RELAY_SCHEMA_VERSION:
            raise ValueError("unsupported relay schema version")

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "message_id": self.message_id.value,
            "sender": self.sender.value,
            "recipient": self.recipient.value,
            "kind": self.kind,
            "correlation_id": self.correlation_id,
            "causation_id": self.causation_id.value if self.causation_id else None,
            "created_at": format_datetime(self.created_at, "created_at"),
            "payload": thaw_json(self.payload),
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> RelayMessage:
        causation = data.get("causation_id")
        payload = freeze_json(data["payload"], path="payload")
        if not isinstance(payload, FrozenDict):
            raise ValueError("payload must be an object")
        return cls(
            schema_version=int(data["schema_version"]),
            message_id=RelayMessageId(require_string(data["message_id"], "message_id")),
            sender=RuntimeAddress(require_string(data["sender"], "sender")),
            recipient=RuntimeAddress(require_string(data["recipient"], "recipient")),
            kind=require_string(data["kind"], "kind"),
            correlation_id=None
            if data.get("correlation_id") is None
            else require_string(data["correlation_id"], "correlation_id"),
            causation_id=None
            if causation is None
            else RelayMessageId(require_string(causation, "causation_id")),
            created_at=parse_datetime(data["created_at"], "created_at"),
            payload=payload,
        )


@dataclass(frozen=True)
class DeliveryRecord:
    message: RelayMessage
    status: DeliveryStatus = DeliveryStatus.PENDING
    attempt_count: int = 0
    available_at: datetime | None = None
    lease_owner: str | None = None
    lease_token: str | None = None
    lease_expires_at: datetime | None = None
    last_error: str | None = None
    acknowledged_at: datetime | None = None
    acknowledged_by: str | None = None
    acknowledgement_token: str | None = None
    dead_lettered_at: datetime | None = None
    schema_version: int = RELAY_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if not isinstance(self.status, DeliveryStatus):
            object.__setattr__(self, "status", DeliveryStatus(self.status))
        if self.attempt_count < 0:
            raise ValueError("attempt_count must be non-negative")
        for name in (
            "available_at",
            "lease_expires_at",
            "acknowledged_at",
            "dead_lettered_at",
        ):
            value = getattr(self, name)
            if value is not None:
                if value.tzinfo is None or value.utcoffset() is None:
                    raise ValueError(f"{name} must be timezone-aware")
                object.__setattr__(self, name, value.astimezone(UTC))
        if self.status is DeliveryStatus.CLAIMED and not all(
            (self.lease_owner, self.lease_token, self.lease_expires_at)
        ):
            raise ValueError("claimed records require complete lease metadata")
        if self.status is DeliveryStatus.ACKNOWLEDGED and not all(
            (self.acknowledged_at, self.acknowledged_by, self.acknowledgement_token)
        ):
            raise ValueError("acknowledged records require acknowledgement metadata")
        if self.schema_version != RELAY_SCHEMA_VERSION:
            raise ValueError("unsupported delivery schema version")

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "message": self.message.to_dict(),
            "status": self.status.value,
            "attempt_count": self.attempt_count,
            "available_at": _format_optional(self.available_at),
            "lease_owner": self.lease_owner,
            "lease_token": self.lease_token,
            "lease_expires_at": _format_optional(self.lease_expires_at),
            "last_error": self.last_error,
            "acknowledged_at": _format_optional(self.acknowledged_at),
            "acknowledged_by": self.acknowledged_by,
            "acknowledgement_token": self.acknowledgement_token,
            "dead_lettered_at": _format_optional(self.dead_lettered_at),
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> DeliveryRecord:
        message = data["message"]
        if not isinstance(message, Mapping):
            raise ValueError("message must be an object")
        return cls(
            schema_version=int(data["schema_version"]),
            message=RelayMessage.from_dict(message),
            status=DeliveryStatus(str(data["status"])),
            attempt_count=int(data["attempt_count"]),
            available_at=_parse_optional(data.get("available_at"), "available_at"),
            lease_owner=_optional_string(data.get("lease_owner")),
            lease_token=_optional_string(data.get("lease_token")),
            lease_expires_at=_parse_optional(data.get("lease_expires_at"), "lease_expires_at"),
            last_error=_optional_string(data.get("last_error")),
            acknowledged_at=_parse_optional(data.get("acknowledged_at"), "acknowledged_at"),
            acknowledged_by=_optional_string(data.get("acknowledged_by")),
            acknowledgement_token=_optional_string(data.get("acknowledgement_token")),
            dead_lettered_at=_parse_optional(data.get("dead_lettered_at"), "dead_lettered_at"),
        )


@dataclass(frozen=True)
class ClaimedMessage:
    record: DeliveryRecord
    lease_token: str

    @property
    def message(self) -> RelayMessage:
        return self.record.message

    @property
    def attempt_count(self) -> int:
        return self.record.attempt_count


@dataclass(frozen=True)
class Acknowledgement:
    message_id: RelayMessageId
    recipient: RuntimeAddress
    lease_owner: str
    lease_token: str
    acknowledged_at: datetime
    attempt_count: int
    schema_version: int = RELAY_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if not isinstance(self.message_id, RelayMessageId):
            object.__setattr__(self, "message_id", RelayMessageId(str(self.message_id)))
        if not isinstance(self.recipient, RuntimeAddress):
            object.__setattr__(self, "recipient", RuntimeAddress(str(self.recipient)))
        if not self.lease_owner or not self.lease_token:
            raise ValueError("acknowledgement lease identity must be non-empty")
        if self.acknowledged_at.tzinfo is None or self.acknowledged_at.utcoffset() is None:
            raise ValueError("acknowledged_at must be timezone-aware")
        object.__setattr__(self, "acknowledged_at", self.acknowledged_at.astimezone(UTC))
        if self.attempt_count <= 0:
            raise ValueError("acknowledgement attempt_count must be positive")
        if self.schema_version != RELAY_SCHEMA_VERSION:
            raise ValueError("unsupported acknowledgement schema version")

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "message_id": self.message_id.value,
            "recipient": self.recipient.value,
            "lease_owner": self.lease_owner,
            "lease_token": self.lease_token,
            "acknowledged_at": format_datetime(self.acknowledged_at, "acknowledged_at"),
            "attempt_count": self.attempt_count,
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> Acknowledgement:
        return cls(
            schema_version=int(data["schema_version"]),
            message_id=RelayMessageId(require_string(data["message_id"], "message_id")),
            recipient=RuntimeAddress(require_string(data["recipient"], "recipient")),
            lease_owner=require_string(data["lease_owner"], "lease_owner"),
            lease_token=require_string(data["lease_token"], "lease_token"),
            acknowledged_at=parse_datetime(data["acknowledged_at"], "acknowledged_at"),
            attempt_count=int(data["attempt_count"]),
        )


def _format_optional(value: datetime | None) -> str | None:
    return None if value is None else format_datetime(value, "timestamp")


def _parse_optional(value: object, name: str) -> datetime | None:
    return None if value is None else parse_datetime(value, name)


def _optional_string(value: object) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str):
        raise ValueError("expected optional string")
    return value


__all__ = [
    "RELAY_SCHEMA_VERSION",
    "Acknowledgement",
    "ClaimedMessage",
    "DeliveryRecord",
    "DeliveryStatus",
    "RelayMessage",
]
