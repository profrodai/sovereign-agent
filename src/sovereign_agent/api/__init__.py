"""Versioned local API for Sovereign Agent v0.4."""

from .envelope import (
    PROTOCOL_NAME,
    PROTOCOL_VERSION,
    SUPPORTED_VERSION_RANGE,
    EnvelopeAuth,
    ProtocolEnvelope,
    ProtocolError,
    negotiate_version,
)
from .idempotency import IdempotencyConflict, IdempotencyLedger
from .server import (
    ApiDispatcher,
    ApiResponse,
    LocalTransport,
    UnixSocketApiServer,
    UnixSocketClient,
    build_local_stack,
)
from .signing import Keyring, sign, signature_for, signed_copy, verify

__all__ = [
    "PROTOCOL_NAME",
    "PROTOCOL_VERSION",
    "SUPPORTED_VERSION_RANGE",
    "ApiDispatcher",
    "ApiResponse",
    "EnvelopeAuth",
    "IdempotencyConflict",
    "IdempotencyLedger",
    "Keyring",
    "LocalTransport",
    "ProtocolEnvelope",
    "ProtocolError",
    "UnixSocketApiServer",
    "UnixSocketClient",
    "build_local_stack",
    "negotiate_version",
    "sign",
    "signature_for",
    "signed_copy",
    "verify",
]
