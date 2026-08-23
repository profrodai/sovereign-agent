"""Typed durable-relay failures."""


class RelayError(RuntimeError):
    """Base relay failure."""


class RelayValidationError(RelayError, ValueError):
    """A relay value, transition, or path is invalid."""


class RelayAuthenticationError(RelayError):
    """Local registry evidence does not support an endpoint."""


class DuplicateMessageConflict(RelayError):
    """A message ID was reused for a different envelope."""


class MessageNotFound(RelayError, LookupError):
    """The requested message does not exist."""


class LeaseLost(RelayError):
    """The claim token is no longer the active fencing generation."""


class RelayCorruptionError(RelayError):
    """A corrupt record was quarantined and processing stopped."""


__all__ = [
    "DuplicateMessageConflict",
    "LeaseLost",
    "MessageNotFound",
    "RelayAuthenticationError",
    "RelayCorruptionError",
    "RelayError",
    "RelayValidationError",
]
