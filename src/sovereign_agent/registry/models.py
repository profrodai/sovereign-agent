"""Versioned seat, instance, and local runtime-address contracts."""

from __future__ import annotations

import re
from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
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
from sovereign_agent.contracts.ids import SeatId, SeatInstanceId

REGISTRY_SCHEMA_VERSION = 1
_ADDRESS = re.compile(r"^local://([A-Za-z0-9](?:[A-Za-z0-9._:/-]{0,126}[A-Za-z0-9])?)$")


def validate_runtime_identifier(value: str, label: str) -> None:
    """Reject traversal-shaped logical IDs even though they never become paths."""
    if "\\" in value or any(part in {".", ".."} for part in value.split("/")):
        raise ValueError(f"{label} must not contain traversal segments")


class SeatLifecycle(StrEnum):
    REGISTERED = "registered"
    STARTING = "starting"
    RUNNING = "running"
    STOPPING = "stopping"
    STOPPED = "stopped"
    FAILED = "failed"


@dataclass(frozen=True, order=True)
class RuntimeAddress:
    """A validated address for a local registered seat instance."""

    value: str

    def __post_init__(self) -> None:
        match = _ADDRESS.fullmatch(self.value)
        if match is None:
            raise ValueError("runtime address must be local://<seat-instance-id>")
        SeatInstanceId(match.group(1))
        validate_runtime_identifier(match.group(1), "runtime address")

    @classmethod
    def for_instance(cls, instance_id: SeatInstanceId | str) -> RuntimeAddress:
        instance = (
            instance_id if isinstance(instance_id, SeatInstanceId) else SeatInstanceId(instance_id)
        )
        return cls(f"local://{instance.value}")

    @property
    def instance_id(self) -> SeatInstanceId:
        return SeatInstanceId(self.value.removeprefix("local://"))

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True)
class Seat:
    """A logical seat type, separate from any running instance."""

    seat_id: SeatId
    description: str = ""
    schema_version: int = REGISTRY_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if not isinstance(self.seat_id, SeatId):
            object.__setattr__(self, "seat_id", SeatId(str(self.seat_id)))
        validate_runtime_identifier(self.seat_id.value, "seat_id")
        if self.schema_version != REGISTRY_SCHEMA_VERSION:
            raise ValueError("unsupported seat schema version")


@dataclass(frozen=True)
class SeatInstance:
    """Immutable identity plus mutable operational metadata snapshot."""

    instance_id: SeatInstanceId
    seat_id: SeatId
    provider: str
    backend: str
    capabilities: tuple[str, ...]
    address: RuntimeAddress
    registered_at: datetime
    updated_at: datetime
    heartbeat_at: datetime
    lifecycle: SeatLifecycle = SeatLifecycle.REGISTERED
    status: FrozenDict = field(default_factory=FrozenDict)
    schema_version: int = REGISTRY_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if not isinstance(self.instance_id, SeatInstanceId):
            object.__setattr__(self, "instance_id", SeatInstanceId(str(self.instance_id)))
        if not isinstance(self.seat_id, SeatId):
            object.__setattr__(self, "seat_id", SeatId(str(self.seat_id)))
        validate_runtime_identifier(self.instance_id.value, "instance_id")
        validate_runtime_identifier(self.seat_id.value, "seat_id")
        if not self.provider or not self.backend:
            raise ValueError("provider and backend must be non-empty")
        if any(not isinstance(item, str) or not item for item in self.capabilities):
            raise ValueError("capabilities must be non-empty strings")
        if len(set(self.capabilities)) != len(self.capabilities):
            raise ValueError("capabilities must be unique")
        if not isinstance(self.address, RuntimeAddress):
            object.__setattr__(self, "address", RuntimeAddress(str(self.address)))
        if self.address.instance_id != self.instance_id:
            raise ValueError("runtime address does not match instance ID")
        for name in ("registered_at", "updated_at", "heartbeat_at"):
            value = getattr(self, name)
            if value.tzinfo is None or value.utcoffset() is None:
                raise ValueError(f"{name} must be timezone-aware")
            object.__setattr__(self, name, value.astimezone(UTC))
        if not isinstance(self.lifecycle, SeatLifecycle):
            object.__setattr__(self, "lifecycle", SeatLifecycle(self.lifecycle))
        frozen = freeze_json(self.status, path="status")
        if not isinstance(frozen, FrozenDict):
            raise ValueError("status must be a JSON object")
        object.__setattr__(self, "status", frozen)
        if self.schema_version != REGISTRY_SCHEMA_VERSION:
            raise ValueError("unsupported seat-instance schema version")

    def is_stale(self, now: datetime, threshold: timedelta | float) -> bool:
        seconds = threshold.total_seconds() if isinstance(threshold, timedelta) else threshold
        if seconds < 0:
            raise ValueError("stale threshold must be non-negative")
        return (now.astimezone(UTC) - self.heartbeat_at).total_seconds() > seconds

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "instance_id": self.instance_id.value,
            "seat_id": self.seat_id.value,
            "provider": self.provider,
            "backend": self.backend,
            "capabilities": list(self.capabilities),
            "address": self.address.value,
            "registered_at": format_datetime(self.registered_at, "registered_at"),
            "updated_at": format_datetime(self.updated_at, "updated_at"),
            "heartbeat_at": format_datetime(self.heartbeat_at, "heartbeat_at"),
            "lifecycle": self.lifecycle.value,
            "status": thaw_json(self.status),
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> SeatInstance:
        capabilities = data["capabilities"]
        if not isinstance(capabilities, list) or any(
            not isinstance(item, str) for item in capabilities
        ):
            raise ValueError("capabilities must be an array of strings")
        return cls(
            schema_version=int(data["schema_version"]),
            instance_id=SeatInstanceId(require_string(data["instance_id"], "instance_id")),
            seat_id=SeatId(require_string(data["seat_id"], "seat_id")),
            provider=require_string(data["provider"], "provider"),
            backend=require_string(data["backend"], "backend"),
            capabilities=tuple(capabilities),
            address=RuntimeAddress(require_string(data["address"], "address")),
            registered_at=parse_datetime(data["registered_at"], "registered_at"),
            updated_at=parse_datetime(data["updated_at"], "updated_at"),
            heartbeat_at=parse_datetime(data["heartbeat_at"], "heartbeat_at"),
            lifecycle=SeatLifecycle(str(data["lifecycle"])),
            status=freeze_json(data.get("status", {})),
        )


__all__ = [
    "REGISTRY_SCHEMA_VERSION",
    "RuntimeAddress",
    "Seat",
    "SeatInstance",
    "SeatLifecycle",
    "validate_runtime_identifier",
]
