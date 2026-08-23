"""Persistent seat-instance registration and local runtime addressing."""

from .errors import (
    RegistrationConflict,
    RegistryCorruptionError,
    RegistryError,
    RegistryValidationError,
    SeatInstanceNotFound,
)
from .manager import SeatRegistry
from .models import (
    REGISTRY_SCHEMA_VERSION,
    RuntimeAddress,
    Seat,
    SeatInstance,
    SeatLifecycle,
)

__all__ = [
    "REGISTRY_SCHEMA_VERSION",
    "RegistrationConflict",
    "RegistryCorruptionError",
    "RegistryError",
    "RegistryValidationError",
    "RuntimeAddress",
    "Seat",
    "SeatInstance",
    "SeatInstanceNotFound",
    "SeatLifecycle",
    "SeatRegistry",
]
