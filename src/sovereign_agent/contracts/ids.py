"""Validated, non-interchangeable identifiers used by execution contracts."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import ClassVar

from ._core import ContractValidationError

_ID_PATTERN = re.compile(r"^[A-Za-z0-9](?:[A-Za-z0-9._:/-]{0,126}[A-Za-z0-9])?$")


@dataclass(frozen=True, order=True)
class _ValidatedId:
    value: str
    kind: ClassVar[str] = "identifier"

    def __post_init__(self) -> None:
        if not isinstance(self.value, str):
            raise ContractValidationError(f"{self.kind} must be a string")
        if not _ID_PATTERN.fullmatch(self.value):
            raise ContractValidationError(
                f"{self.kind} must be 1-128 visible identifier characters "
                "(letters, digits, '.', '_', ':', '/', or '-')"
            )

    def __str__(self) -> str:
        return self.value


class SeatInstanceId(_ValidatedId):
    kind = "seat_instance_id"


class SovereignSessionId(_ValidatedId):
    kind = "sovereign_session_id"


class ExecutionId(_ValidatedId):
    kind = "execution_id"


class InvocationId(_ValidatedId):
    kind = "invocation_id"


class ProviderSessionId(_ValidatedId):
    kind = "provider_session_id"


class WorkerHandleId(_ValidatedId):
    kind = "worker_handle_id"


class RepositoryId(_ValidatedId):
    kind = "repository_id"


__all__ = [
    "ExecutionId",
    "InvocationId",
    "ProviderSessionId",
    "RepositoryId",
    "SeatInstanceId",
    "SovereignSessionId",
    "WorkerHandleId",
]
