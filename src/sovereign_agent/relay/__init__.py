"""Durable local relay with fenced claims and explicit acknowledgements."""

from .errors import (
    DuplicateMessageConflict,
    LeaseLost,
    MessageNotFound,
    RelayAuthenticationError,
    RelayCorruptionError,
    RelayError,
    RelayValidationError,
)
from .manager import DurableRelay, Relay
from .models import (
    RELAY_SCHEMA_VERSION,
    Acknowledgement,
    ClaimedMessage,
    DeliveryRecord,
    DeliveryStatus,
    RelayMessage,
)

__all__ = [
    "RELAY_SCHEMA_VERSION",
    "Acknowledgement",
    "ClaimedMessage",
    "DeliveryRecord",
    "DeliveryStatus",
    "DuplicateMessageConflict",
    "DurableRelay",
    "LeaseLost",
    "MessageNotFound",
    "Relay",
    "RelayAuthenticationError",
    "RelayCorruptionError",
    "RelayError",
    "RelayMessage",
    "RelayValidationError",
]
