"""v0.4 protocol envelope, version negotiation, and typed refusals."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, ClassVar

from sovereign_agent.contracts._core import (
    ContractValidationError,
    FrozenDict,
    format_datetime,
    freeze_json,
    merge_unknown,
    parse_datetime,
    require_object,
    require_string,
    split_known,
    thaw_json,
)

PROTOCOL_NAME = "sovereign-agent"
PROTOCOL_VERSION = "1.0"
SUPPORTED_MAJOR = 1
SUPPORTED_MINOR_MIN = 0
SUPPORTED_MINOR_MAX = 0
SUPPORTED_VERSION_RANGE = ">=1.0,<2.0"

_REQUIRED = frozenset(
    {
        "protocol",
        "protocol_version",
        "message_id",
        "correlation_id",
        "causation_id",
        "sent_at",
        "sender",
        "recipient",
        "kind",
        "body",
        "auth",
    }
)
_AUTH_REQUIRED = frozenset({"scheme", "key_id", "signature"})


class ProtocolError(ValueError):
    """A protocol envelope cannot be accepted."""

    def __init__(
        self, reason: str, *, detail: str = "", supported_range: str = SUPPORTED_VERSION_RANGE
    ):
        super().__init__(detail or reason)
        self.reason = reason
        self.detail = detail or reason
        self.supported_range = supported_range

    def to_dict(self) -> dict[str, Any]:
        return {
            "reason": self.reason,
            "detail": self.detail,
            "supported_version_range": self.supported_range,
        }


def parse_protocol_version(value: str) -> tuple[int, int]:
    text = require_string(value, "protocol_version")
    parts = text.split(".")
    if len(parts) != 2 or not all(part.isdigit() for part in parts):
        raise ProtocolError(
            "unsupported-version", detail="protocol_version must be <major>.<minor>"
        )
    return int(parts[0]), int(parts[1])


def negotiate_version(value: str) -> str:
    major, minor = parse_protocol_version(value)
    if major != SUPPORTED_MAJOR:
        raise ProtocolError(
            "unsupported-version",
            detail=f"major protocol mismatch: received {value}",
        )
    if minor < SUPPORTED_MINOR_MIN:
        raise ProtocolError(
            "unsupported-version",
            detail=f"protocol_version {value} is below supported range",
        )
    if minor > SUPPORTED_MINOR_MAX:
        # Additive minors are accepted only when no unknown required fields exist.
        # Callers still must fail closed on required_fields.
        return value
    return value


@dataclass(frozen=True)
class EnvelopeAuth:
    scheme: str
    key_id: str
    signature: str
    unknown_fields: FrozenDict = field(default_factory=FrozenDict, repr=False)

    _KNOWN: ClassVar[frozenset[str]] = _AUTH_REQUIRED

    def __post_init__(self) -> None:
        if self.scheme != "hmac-sha256":
            raise ProtocolError(
                "unsupported-auth", detail=f"unsupported auth scheme {self.scheme!r}"
            )
        if not self.key_id:
            raise ProtocolError("unauthenticated", detail="auth.key_id is required")

    def to_dict(self, *, include_signature: bool = True) -> dict[str, Any]:
        known: dict[str, Any] = {
            "scheme": self.scheme,
            "key_id": self.key_id,
            "signature": self.signature if include_signature else "",
        }
        return merge_unknown(known, self.unknown_fields)

    @classmethod
    def from_dict(cls, data: object) -> EnvelopeAuth:
        mapping = require_object(data, "auth")
        missing = _AUTH_REQUIRED - mapping.keys()
        if missing:
            raise ProtocolError(
                "unauthenticated",
                detail=f"auth missing required fields: {sorted(missing)}",
            )
        values, unknown = split_known(mapping, cls._KNOWN)
        return cls(
            scheme=require_string(values["scheme"], "auth.scheme"),
            key_id=require_string(values["key_id"], "auth.key_id"),
            signature=require_string(values["signature"], "auth.signature", allow_empty=True),
            unknown_fields=unknown,
        )


@dataclass(frozen=True)
class ProtocolEnvelope:
    """One authenticated v0.4 wire message."""

    protocol: str
    protocol_version: str
    message_id: str
    correlation_id: str
    causation_id: str
    sent_at: datetime
    sender: str
    recipient: str
    kind: str
    body: FrozenDict
    auth: EnvelopeAuth
    required_fields: tuple[str, ...] = ()
    unknown_fields: FrozenDict = field(default_factory=FrozenDict, repr=False)

    _KNOWN: ClassVar[frozenset[str]] = _REQUIRED | frozenset({"required_fields"})

    def __post_init__(self) -> None:
        if self.protocol != PROTOCOL_NAME:
            raise ProtocolError("unsupported-protocol", detail=f"protocol {self.protocol!r}")
        negotiate_version(self.protocol_version)
        for name in (
            "message_id",
            "correlation_id",
            "causation_id",
            "sender",
            "recipient",
            "kind",
        ):
            require_string(getattr(self, name), name)
        if not isinstance(self.body, FrozenDict):
            object.__setattr__(self, "body", freeze_json(self.body, path="body"))
            if not isinstance(self.body, FrozenDict):
                raise ProtocolError("malformed-body", detail="body must be a JSON object")

    def to_dict(self, *, include_signature: bool = True) -> dict[str, Any]:
        known: dict[str, Any] = {
            "protocol": self.protocol,
            "protocol_version": self.protocol_version,
            "message_id": self.message_id,
            "correlation_id": self.correlation_id,
            "causation_id": self.causation_id,
            "sent_at": format_datetime(self.sent_at, "sent_at"),
            "sender": self.sender,
            "recipient": self.recipient,
            "kind": self.kind,
            "body": thaw_json(self.body),
            "auth": self.auth.to_dict(include_signature=include_signature),
        }
        if self.required_fields:
            known["required_fields"] = list(self.required_fields)
        return merge_unknown(known, self.unknown_fields)

    def unsigned_dict(self) -> dict[str, Any]:
        return self.to_dict(include_signature=False)

    @classmethod
    def from_dict(cls, data: Mapping[str, Any] | object) -> ProtocolEnvelope:
        mapping = require_object(data, "envelope")
        missing = _REQUIRED - mapping.keys()
        if missing:
            raise ProtocolError(
                "malformed-envelope",
                detail=f"missing required fields: {sorted(missing)}",
            )
        declared = mapping.get("required_fields", ())
        if declared is None:
            declared = ()
        if not isinstance(declared, (list, tuple)) or any(
            not isinstance(item, str) for item in declared
        ):
            raise ProtocolError(
                "malformed-envelope", detail="required_fields must be an array of strings"
            )
        unknown_required = [
            name for name in declared if name not in cls._KNOWN and name not in mapping
        ]
        if unknown_required:
            raise ProtocolError(
                "unknown-required-field",
                detail=f"unknown required fields: {unknown_required}",
            )
        unexplained = [name for name in declared if name not in cls._KNOWN]
        if unexplained:
            raise ProtocolError(
                "unknown-required-field",
                detail=f"unsupported required fields: {unexplained}",
            )
        values, unknown = split_known(mapping, cls._KNOWN)
        body = freeze_json(values["body"], path="body")
        if not isinstance(body, FrozenDict):
            raise ProtocolError("malformed-body", detail="body must be a JSON object")
        try:
            return cls(
                protocol=require_string(values["protocol"], "protocol"),
                protocol_version=require_string(values["protocol_version"], "protocol_version"),
                message_id=require_string(values["message_id"], "message_id"),
                correlation_id=require_string(values["correlation_id"], "correlation_id"),
                causation_id=require_string(values["causation_id"], "causation_id"),
                sent_at=parse_datetime(values["sent_at"], "sent_at"),
                sender=require_string(values["sender"], "sender"),
                recipient=require_string(values["recipient"], "recipient"),
                kind=require_string(values["kind"], "kind"),
                body=body,
                auth=EnvelopeAuth.from_dict(values["auth"]),
                required_fields=tuple(declared),
                unknown_fields=unknown,
            )
        except ContractValidationError as exc:
            raise ProtocolError("malformed-envelope", detail=str(exc)) from exc
        except ProtocolError:
            raise
        except ValueError as exc:
            raise ProtocolError("malformed-envelope", detail=str(exc)) from exc
