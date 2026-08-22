"""Immutable contracts for governed repository execution."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path

from sovereign_agent.contracts import ExecutionId, RepositoryId


class DirtyWorktreePolicy(StrEnum):
    """Policy for an operator checkout that contains local changes."""

    FAIL = "fail"
    ALLOW = "allow"


class DeliveryState(StrEnum):
    """Delivery is deliberately separate from local completion."""

    NOT_REQUESTED = "not_requested"
    VERIFIED = "verified"
    FAILED = "failed"


class DeliveryFailureReason(StrEnum):
    """Stable failure reasons suitable for receipts."""

    PUSH_REJECTED = "push_rejected"
    REMOTE_REF_MISSING = "remote_ref_missing"
    REMOTE_SHA_MISMATCH = "remote_sha_mismatch"
    PROTECTED_BRANCH = "protected_branch"
    INVALID_REMOTE = "invalid_remote"


@dataclass(frozen=True)
class RepositoryConfig:
    """Governance mapping from an opaque ID to one local checkout."""

    repository_id: RepositoryId
    checkout: Path
    default_remote: str = "origin"
    protected_branches: tuple[str, ...] = ("main", "master")

    def __post_init__(self) -> None:
        object.__setattr__(self, "checkout", Path(self.checkout))
        object.__setattr__(self, "protected_branches", tuple(self.protected_branches))


@dataclass(frozen=True)
class RepositoryIdentity:
    repository_id: RepositoryId
    checkout: str
    remote_name: str | None
    remote_url: str | None


@dataclass(frozen=True)
class GitEvidence:
    """Byte-stable evidence captured at a repository boundary."""

    identity: RepositoryIdentity
    base_ref: str
    base_sha: str
    execution_branch: str
    head_sha: str
    status_porcelain: bytes
    changed_paths: tuple[str, ...]
    diff_stat: bytes
    patch_sha256: str
    commits: tuple[str, ...]
    worktree_path: str
    artifact_references: tuple[str, ...] = ()


@dataclass(frozen=True)
class RepositoryExecution:
    repository_id: RepositoryId
    execution_id: ExecutionId
    source_checkout: Path
    worktree_path: Path
    base_ref: str
    base_sha: str
    branch: str
    lock_token: str


@dataclass(frozen=True)
class DeliveryResult:
    local_complete: bool
    state: DeliveryState
    local_sha: str
    remote: str | None = None
    remote_ref: str | None = None
    verified_sha: str | None = None
    failure_reason: DeliveryFailureReason | None = None
    detail: str | None = None


__all__ = [
    "DeliveryFailureReason",
    "DeliveryResult",
    "DeliveryState",
    "DirtyWorktreePolicy",
    "GitEvidence",
    "RepositoryConfig",
    "RepositoryExecution",
    "RepositoryIdentity",
]
