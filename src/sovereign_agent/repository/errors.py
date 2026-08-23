"""Typed repository subsystem failures."""

from __future__ import annotations


class RepositoryError(RuntimeError):
    """Base repository execution failure with a stable reason."""

    reason = "repository_error"


class RepositoryConfigurationError(RepositoryError):
    reason = "repository_configuration"


class RepositoryValidationError(RepositoryError, ValueError):
    reason = "repository_validation"


class RepositoryDirtyError(RepositoryError):
    reason = "dirty_worktree"


class RepositoryCommandError(RepositoryError):
    reason = "git_command_failed"

    def __init__(self, operation: str, stderr: str, returncode: int) -> None:
        self.operation = operation
        self.stderr = stderr
        self.returncode = returncode
        super().__init__(f"{operation} failed ({returncode}): {stderr}")


class RepositoryLockTimeout(RepositoryError, TimeoutError):
    reason = "lock_timeout"


class RepositoryLockLost(RepositoryError):
    reason = "lock_lost"


class RepositoryDeliveryError(RepositoryError):
    reason = "delivery_failed"


__all__ = [
    "RepositoryCommandError",
    "RepositoryConfigurationError",
    "RepositoryDeliveryError",
    "RepositoryDirtyError",
    "RepositoryError",
    "RepositoryLockLost",
    "RepositoryLockTimeout",
    "RepositoryValidationError",
]
