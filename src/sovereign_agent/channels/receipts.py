"""Normalized inbound events and outbound delivery receipts."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass
class AttachmentRef:
    uri: str
    sha256: str
    content_type: str | None = None


@dataclass
class NormalizedInbound:
    channel_type: str
    account_id: str
    platform_message_id: str
    platform_thread_id: str | None
    sender_id: str
    sender_trust: str
    timestamp: datetime
    is_mention: bool
    is_direct_message: bool
    text: str
    attachments: tuple[AttachmentRef, ...] = ()
    dedup_key: str = ""

    def __post_init__(self) -> None:
        if not self.dedup_key:
            self.dedup_key = "|".join(
                (
                    self.channel_type,
                    self.account_id,
                    self.platform_message_id,
                    self.platform_thread_id or "",
                )
            )


@dataclass
class DeliveryReceipt:
    attempt: int
    destination: str
    status: str
    provider_response_id: str | None = None
    failure_category: str | None = None
    extras: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "attempt": self.attempt,
            "destination": self.destination,
            "status": self.status,
            "provider_response_id": self.provider_response_id,
            "failure_category": self.failure_category,
            **self.extras,
        }
