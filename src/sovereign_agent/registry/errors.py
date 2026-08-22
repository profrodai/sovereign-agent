"""Typed failures for the durable seat registry."""


class RegistryError(RuntimeError):
    """Base registry failure."""


class RegistryValidationError(RegistryError, ValueError):
    """A registry value or path is unsafe."""


class RegistrationConflict(RegistryError):
    """An instance ID is already bound to different immutable identity."""


class SeatInstanceNotFound(RegistryError, LookupError):
    """The requested seat instance is not registered."""


class RegistryCorruptionError(RegistryError):
    """A durable registry record is corrupt or unsupported."""


__all__ = [
    "RegistrationConflict",
    "RegistryCorruptionError",
    "RegistryError",
    "RegistryValidationError",
    "SeatInstanceNotFound",
]
