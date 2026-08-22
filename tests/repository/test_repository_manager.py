from __future__ import annotations

import json
import os
import subprocess
import time
from pathlib import Path

import pytest

from sovereign_agent.contracts import ExecutionId, RepositoryId
from sovereign_agent.repository import (
    DeliveryFailureReason,
    DeliveryState,
    DirtyWorktreePolicy,
    RepositoryConfig,
    RepositoryDirtyError,
    RepositoryLockManager,
    RepositoryLockTimeout,
    RepositoryManager,
    RepositoryValidationError,
)
from sovereign_agent.runtime import RuntimeRoot


def git(path: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ("git", "-C", str(path), *args),
        check=True,
        capture_output=True,
        text=True,
        env={
            **os.environ,
            "GIT_AUTHOR_NAME": "Test",
            "GIT_AUTHOR_EMAIL": "test@example.invalid",
            "GIT_COMMITTER_NAME": "Test",
            "GIT_COMMITTER_EMAIL": "test@example.invalid",
            "LC_ALL": "C",
        },
    )


@pytest.fixture
def repository(tmp_path: Path) -> tuple[Path, Path]:
    bare = tmp_path / "remote.git"
    subprocess.run(("git", "init", "--bare", str(bare)), check=True, capture_output=True)
    checkout = tmp_path / "checkout"
    subprocess.run(("git", "init", "-b", "main", str(checkout)), check=True, capture_output=True)
    (checkout / "tracked.txt").write_text("base\n")
    git(checkout, "add", "tracked.txt")
    git(checkout, "commit", "-m", "base")
    git(checkout, "remote", "add", "origin", str(bare))
    git(checkout, "push", "-u", "origin", "main")
    return checkout, bare


def manager(tmp_path: Path, checkout: Path) -> RepositoryManager:
    return RepositoryManager(
        RuntimeRoot(tmp_path / "runtime"),
        (RepositoryConfig(RepositoryId("repo"), checkout),),
    )


def test_clean_prepare_isolated_and_cleanup_idempotent(
    tmp_path: Path, repository: tuple[Path, Path]
) -> None:
    checkout, _ = repository
    subject = manager(tmp_path, checkout)
    execution = subject.prepare(RepositoryId("repo"), ExecutionId("exec-1"))
    assert execution.worktree_path != checkout
    assert execution.worktree_path.is_dir()
    assert git(checkout, "branch", "--show-current").stdout.strip() == "main"
    (execution.worktree_path / "tracked.txt").write_text("changed\n")
    assert (checkout / "tracked.txt").read_text() == "base\n"
    assert subject.cleanup(execution)
    assert not subject.cleanup(execution)


def test_dirty_checkout_fails_closed_but_can_be_explicitly_allowed(
    tmp_path: Path, repository: tuple[Path, Path]
) -> None:
    checkout, _ = repository
    (checkout / "tracked.txt").write_text("operator change\n")
    subject = manager(tmp_path, checkout)
    with pytest.raises(RepositoryDirtyError):
        subject.prepare(RepositoryId("repo"), ExecutionId("fail"))
    execution = subject.prepare(
        RepositoryId("repo"),
        ExecutionId("allow"),
        dirty_policy=DirtyWorktreePolicy.ALLOW,
    )
    assert (execution.worktree_path / "tracked.txt").read_text() == "base\n"
    subject.cleanup(execution)


@pytest.mark.parametrize(
    "bad_ref", ["--upload-pack=evil", "../main", "main..evil", "x@{0}", "x y", "/main"]
)
def test_malicious_refs_are_rejected(
    tmp_path: Path, repository: tuple[Path, Path], bad_ref: str
) -> None:
    checkout, _ = repository
    with pytest.raises(RepositoryValidationError):
        manager(tmp_path, checkout).prepare(
            RepositoryId("repo"), ExecutionId("bad"), base_ref=bad_ref
        )


def test_path_traversal_and_symlink_escape_rejected(
    tmp_path: Path, repository: tuple[Path, Path]
) -> None:
    checkout, _ = repository
    subject = manager(tmp_path, checkout)
    execution = subject.prepare(RepositoryId("repo"), ExecutionId("paths"))
    with pytest.raises(RepositoryValidationError):
        subject.resolve_relative_path(execution, "../outside")
    (execution.worktree_path / "escape").symlink_to(tmp_path)
    with pytest.raises(RepositoryValidationError):
        subject.resolve_relative_path(execution, "escape/file")
    subject.cleanup(execution)


def test_lock_wait_is_bounded_and_release_explicit(tmp_path: Path) -> None:
    locks = RepositoryLockManager(tmp_path / "locks")
    first = locks.acquire("repo", timeout=0.1)
    with pytest.raises(RepositoryLockTimeout):
        locks.acquire("repo", timeout=0.05, poll_interval=0.01)
    assert first.release()
    assert not first.release()
    assert locks.acquire("repo", timeout=0.1).release()


def test_stale_takeover_is_fenced_from_old_release(tmp_path: Path) -> None:
    locks = RepositoryLockManager(tmp_path / "locks")
    old = locks.acquire("repo", lease_seconds=0.01)
    metadata = json.loads(old.metadata_path.read_text())
    metadata["heartbeat_ns"] = time.time_ns() - 10_000_000_000
    old.metadata_path.write_text(json.dumps(metadata))
    new = locks.acquire("repo", timeout=0.2, lease_seconds=0.01)
    assert old.release() is False
    new.heartbeat()
    assert new.release()


def test_contender_cannot_shorten_current_owners_lease(tmp_path: Path) -> None:
    locks = RepositoryLockManager(tmp_path / "locks")
    owner = locks.acquire("repo", lease_seconds=1.0)
    metadata = json.loads(owner.metadata_path.read_text())
    metadata["heartbeat_ns"] = time.time_ns() - 50_000_000
    owner.metadata_path.write_text(json.dumps(metadata))
    with pytest.raises(RepositoryLockTimeout):
        locks.acquire(
            "repo",
            timeout=0.03,
            lease_seconds=0.01,
            poll_interval=0.005,
        )
    assert owner.release()


def test_evidence_is_deterministic_and_redacts_remote_credentials(
    tmp_path: Path, repository: tuple[Path, Path]
) -> None:
    checkout, _ = repository
    git(checkout, "remote", "set-url", "origin", "https://user:secret@example.invalid/repo.git")
    subject = manager(tmp_path, checkout)
    execution = subject.prepare(RepositoryId("repo"), ExecutionId("evidence"))
    (execution.worktree_path / "new.txt").write_bytes(b"stable\n")
    first = subject.capture_evidence(execution)
    second = subject.capture_evidence(execution)
    assert first == second
    assert first.changed_paths == ("new.txt",)
    assert first.patch_sha256 == second.patch_sha256
    assert first.identity.remote_url == "https://example.invalid/repo.git"
    subject.cleanup(execution)


def test_push_verifies_exact_execution_ref(tmp_path: Path, repository: tuple[Path, Path]) -> None:
    checkout, bare = repository
    subject = manager(tmp_path, checkout)
    execution = subject.prepare(RepositoryId("repo"), ExecutionId("push"))
    (execution.worktree_path / "tracked.txt").write_text("delivery\n")
    git(execution.worktree_path, "add", "tracked.txt")
    git(execution.worktree_path, "commit", "-m", "delivery")
    result = subject.deliver(execution, enabled=True)
    assert result.state is DeliveryState.VERIFIED
    assert result.verified_sha == result.local_sha
    assert (
        git(bare, "rev-parse", f"refs/heads/{execution.branch}").stdout.strip() == result.local_sha
    )
    subject.cleanup(execution)


@pytest.mark.parametrize(
    ("hook_body", "reason"),
    [
        (
            'while read -r old new ref; do git update-ref "$ref" "$(git rev-parse refs/heads/main)"; done\n',
            DeliveryFailureReason.REMOTE_SHA_MISMATCH,
        ),
        (
            'while read -r old new ref; do git update-ref -d "$ref"; done\n',
            DeliveryFailureReason.REMOTE_REF_MISSING,
        ),
    ],
)
def test_delivery_detects_wrong_or_missing_remote_ref(
    tmp_path: Path,
    repository: tuple[Path, Path],
    hook_body: str,
    reason: DeliveryFailureReason,
) -> None:
    checkout, bare = repository
    hook = bare / "hooks" / "post-receive"
    hook.write_text("#!/bin/sh\n" + hook_body)
    hook.chmod(0o700)
    subject = manager(tmp_path, checkout)
    execution = subject.prepare(RepositoryId("repo"), ExecutionId(f"verify-{reason}"))
    (execution.worktree_path / "tracked.txt").write_text("delivery\n")
    git(execution.worktree_path, "add", "tracked.txt")
    git(execution.worktree_path, "commit", "-m", "delivery")
    assert subject.deliver(execution, enabled=True).failure_reason is reason
    subject.cleanup(execution)


def test_delivery_defaults_off_and_refuses_protected_branch(
    tmp_path: Path, repository: tuple[Path, Path]
) -> None:
    checkout, _ = repository
    subject = manager(tmp_path, checkout)
    execution = subject.prepare(RepositoryId("repo"), ExecutionId("protected"))
    assert subject.deliver(execution).state is DeliveryState.NOT_REQUESTED
    refused = subject.deliver(execution, enabled=True, remote_branch="main")
    assert refused.failure_reason is DeliveryFailureReason.PROTECTED_BRANCH
    subject.cleanup(execution)


def test_non_fast_forward_push_is_refused_without_force(
    tmp_path: Path, repository: tuple[Path, Path]
) -> None:
    checkout, bare = repository
    subject = manager(tmp_path, checkout)
    execution = subject.prepare(RepositoryId("repo"), ExecutionId("nff"))
    git(execution.worktree_path, "push", "origin", f"HEAD:refs/heads/{execution.branch}")
    other = tmp_path / "other"
    subprocess.run(("git", "clone", str(bare), str(other)), check=True, capture_output=True)
    git(other, "checkout", execution.branch)
    (other / "other.txt").write_text("remote\n")
    git(other, "add", "other.txt")
    git(other, "commit", "-m", "remote advance")
    git(other, "push", "origin", execution.branch)
    (execution.worktree_path / "local.txt").write_text("local\n")
    git(execution.worktree_path, "add", "local.txt")
    git(execution.worktree_path, "commit", "-m", "local divergence")
    result = subject.deliver(execution, enabled=True)
    assert result.failure_reason is DeliveryFailureReason.PUSH_REJECTED
    assert git(bare, "show", f"{execution.branch}:other.txt").stdout == "remote\n"
    subject.cleanup(execution)
