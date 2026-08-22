"""Native, argv-only Git repository execution."""

from __future__ import annotations

import hashlib
import os
import re
import subprocess
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit

from sovereign_agent.contracts import ExecutionId, RepositoryId
from sovereign_agent.contracts.redaction import REDACTED, redact_text
from sovereign_agent.runtime import RuntimeRoot

from .errors import (
    RepositoryCommandError,
    RepositoryConfigurationError,
    RepositoryDirtyError,
    RepositoryLockLost,
    RepositoryValidationError,
)
from .locking import RepositoryLease, RepositoryLockManager
from .models import (
    DeliveryFailureReason,
    DeliveryResult,
    DeliveryState,
    DirtyWorktreePolicy,
    GitEvidence,
    RepositoryConfig,
    RepositoryExecution,
    RepositoryIdentity,
)

_SAFE_GIT_NAME = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._/-]{0,199}$")
_SAFE_REMOTE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,99}$")
_FORBIDDEN_REF_PARTS = ("..", "@{", "//", "\\")
_URL_USERINFO = re.compile(r"(?i)([a-z][a-z0-9+.-]*://)[^/@\s]+@")


class RepositoryManager:
    """Resolve governed repositories and isolate executions in Git worktrees."""

    def __init__(self, runtime: RuntimeRoot, repositories: tuple[RepositoryConfig, ...]) -> None:
        self.runtime = runtime.initialize()
        self._repositories = {item.repository_id: item for item in repositories}
        if len(self._repositories) != len(repositories):
            raise RepositoryConfigurationError("duplicate repository_id")
        self._locks = RepositoryLockManager(self.runtime.locks_dir / "repositories")

    def resolve(self, repository_id: RepositoryId) -> RepositoryConfig:
        try:
            config = self._repositories[repository_id]
        except KeyError as exc:
            raise RepositoryConfigurationError(
                f"repository is not governed: {repository_id}"
            ) from exc
        checkout = config.checkout
        if checkout.is_symlink():
            raise RepositoryValidationError("configured checkout must not be a symlink")
        try:
            resolved = checkout.resolve(strict=True)
        except FileNotFoundError as exc:
            raise RepositoryConfigurationError("configured checkout does not exist") from exc
        if not resolved.is_dir():
            raise RepositoryConfigurationError("configured checkout is not a directory")
        result = _git(
            resolved, "rev-parse", "--is-inside-work-tree", operation="validate repository"
        )
        if result.stdout.strip() != b"true":
            raise RepositoryValidationError("configured checkout is not a Git worktree")
        return RepositoryConfig(
            repository_id=config.repository_id,
            checkout=resolved,
            default_remote=config.default_remote,
            protected_branches=config.protected_branches,
        )

    def prepare(
        self,
        repository_id: RepositoryId,
        execution_id: ExecutionId,
        *,
        base_ref: str = "HEAD",
        dirty_policy: DirtyWorktreePolicy = DirtyWorktreePolicy.FAIL,
        lock_timeout: float = 30.0,
        lease_seconds: float = 60.0,
    ) -> RepositoryExecution:
        config = self.resolve(repository_id)
        _validate_ref(base_ref, "base_ref")
        _validate_remote(config.default_remote)
        lock_key = hashlib.sha256(str(repository_id).encode()).hexdigest()
        lease = self._locks.acquire(
            lock_key,
            timeout=lock_timeout,
            lease_seconds=lease_seconds,
            owner=str(execution_id),
        )
        try:
            status = _git(
                config.checkout,
                "status",
                "--porcelain=v1",
                "-z",
                operation="inspect operator checkout",
            ).stdout
            if status and dirty_policy is DirtyWorktreePolicy.FAIL:
                raise RepositoryDirtyError("operator checkout is dirty (policy=fail)")

            base_sha = (
                _git(
                    config.checkout,
                    "rev-parse",
                    "--verify",
                    "--end-of-options",
                    f"{base_ref}^{{commit}}",
                    operation="resolve base ref",
                )
                .stdout.decode("ascii")
                .strip()
            )
            branch = _execution_branch(repository_id, execution_id, base_sha)
            relative = (
                Path("repository-worktrees")
                / hashlib.sha256(f"{repository_id}\0{execution_id}".encode()).hexdigest()[:24]
            )
            worktree = self.runtime.executions_dir / relative
            _assert_beneath(worktree, self.runtime.executions_dir)
            worktree.parent.mkdir(mode=0o700, parents=True, exist_ok=True)

            if worktree.exists():
                existing_sha = (
                    _git(worktree, "rev-parse", "HEAD", operation="inspect existing worktree")
                    .stdout.decode("ascii")
                    .strip()
                )
                existing_branch = (
                    _git(
                        worktree,
                        "symbolic-ref",
                        "--short",
                        "HEAD",
                        operation="inspect existing branch",
                    )
                    .stdout.decode()
                    .strip()
                )
                if existing_sha != base_sha or existing_branch != branch:
                    raise RepositoryValidationError("execution worktree collision")
            else:
                branch_exists = (
                    _git_optional(
                        config.checkout,
                        "show-ref",
                        "--verify",
                        "--quiet",
                        f"refs/heads/{branch}",
                    ).returncode
                    == 0
                )
                args = (
                    ("worktree", "add", str(worktree), branch)
                    if branch_exists
                    else ("worktree", "add", "-b", branch, str(worktree), base_sha)
                )
                _git(config.checkout, *args, operation="create execution worktree")
            return RepositoryExecution(
                repository_id=repository_id,
                execution_id=execution_id,
                source_checkout=config.checkout,
                worktree_path=worktree,
                base_ref=base_ref,
                base_sha=base_sha,
                branch=branch,
                lock_token=lease.token,
            )
        except BaseException:
            lease.release()
            raise

    def heartbeat(self, execution: RepositoryExecution) -> None:
        self._lease(execution).heartbeat()

    def resume(
        self,
        execution: RepositoryExecution,
        *,
        lock_timeout: float = 30.0,
        lease_seconds: float = 60.0,
    ) -> RepositoryExecution:
        """Revalidate an existing worktree and recover its lease generation."""
        config = self.resolve(execution.repository_id)
        try:
            self.heartbeat(execution)
            return execution
        except RepositoryLockLost:
            pass
        if execution.source_checkout.resolve() != config.checkout.resolve():
            raise RepositoryValidationError("execution source checkout mapping changed")
        if not execution.worktree_path.is_dir():
            raise RepositoryValidationError("execution worktree is missing during recovery")
        branch = (
            _git(
                execution.worktree_path,
                "symbolic-ref",
                "--short",
                "HEAD",
                operation="recover execution branch",
            )
            .stdout.decode()
            .strip()
        )
        if branch != execution.branch:
            raise RepositoryValidationError("execution branch changed during recovery")
        lock_key = hashlib.sha256(str(execution.repository_id).encode()).hexdigest()
        lease = self._locks.acquire(
            lock_key,
            timeout=lock_timeout,
            lease_seconds=lease_seconds,
            owner=str(execution.execution_id),
        )
        return RepositoryExecution(
            repository_id=execution.repository_id,
            execution_id=execution.execution_id,
            source_checkout=execution.source_checkout,
            worktree_path=execution.worktree_path,
            base_ref=execution.base_ref,
            base_sha=execution.base_sha,
            branch=execution.branch,
            lock_token=lease.token,
        )

    def resolve_relative_path(
        self, execution: RepositoryExecution, relative_path: str | Path
    ) -> Path:
        rel = Path(relative_path)
        if rel.is_absolute() or any(part in {"", ".", ".."} for part in rel.parts):
            raise RepositoryValidationError("path must be a normalized relative path")
        current = execution.worktree_path
        for part in rel.parts:
            current = current / part
            if current.is_symlink():
                raise RepositoryValidationError("repository path traverses a symlink")
        _assert_beneath(current, execution.worktree_path)
        return current

    def capture_evidence(
        self,
        execution: RepositoryExecution,
        *,
        artifact_references: tuple[str, ...] = (),
    ) -> GitEvidence:
        self.heartbeat(execution)
        config = self.resolve(execution.repository_id)
        head = (
            _git(execution.worktree_path, "rev-parse", "HEAD", operation="capture HEAD")
            .stdout.decode("ascii")
            .strip()
        )
        status = _git(
            execution.worktree_path,
            "status",
            "--porcelain=v1",
            "-z",
            "--untracked-files=all",
            operation="capture status",
        ).stdout
        committed_paths = _nul_paths(
            _git(
                execution.worktree_path,
                "diff",
                "--name-only",
                "-z",
                f"{execution.base_sha}..HEAD",
                operation="capture committed paths",
            ).stdout
        )
        local_paths = _nul_paths(
            _git(
                execution.worktree_path,
                "diff",
                "--name-only",
                "-z",
                "HEAD",
                operation="capture local paths",
            ).stdout
        )
        untracked_paths = _nul_paths(
            _git(
                execution.worktree_path,
                "ls-files",
                "--others",
                "--exclude-standard",
                "-z",
                operation="capture untracked paths",
            ).stdout
        )
        changed_paths = tuple(sorted(set(committed_paths + local_paths + untracked_paths)))
        patch = _git(
            execution.worktree_path,
            "diff",
            "--binary",
            "--no-ext-diff",
            execution.base_sha,
            operation="capture patch",
        ).stdout
        digest = hashlib.sha256()
        digest.update(patch)
        for path_text in sorted(untracked_paths):
            path = self.resolve_relative_path(execution, path_text)
            digest.update(b"\0untracked\0")
            digest.update(os.fsencode(path_text))
            digest.update(b"\0")
            digest.update(path.read_bytes())
        diff_stat = _git(
            execution.worktree_path,
            "diff",
            "--stat",
            "--no-color",
            execution.base_sha,
            operation="capture diff stat",
        ).stdout
        commits_raw = _git(
            execution.worktree_path,
            "log",
            "--format=%H",
            f"{execution.base_sha}..HEAD",
            operation="capture commits",
        ).stdout
        remote_url = _git_optional(config.checkout, "remote", "get-url", config.default_remote)
        return GitEvidence(
            identity=RepositoryIdentity(
                repository_id=execution.repository_id,
                checkout=str(config.checkout),
                remote_name=config.default_remote if remote_url.returncode == 0 else None,
                remote_url=(
                    _redact_remote(remote_url.stdout.decode(errors="replace").strip())
                    if remote_url.returncode == 0
                    else None
                ),
            ),
            base_ref=execution.base_ref,
            base_sha=execution.base_sha,
            execution_branch=execution.branch,
            head_sha=head,
            status_porcelain=status,
            changed_paths=changed_paths,
            diff_stat=diff_stat,
            patch_sha256=digest.hexdigest(),
            commits=tuple(line for line in commits_raw.decode("ascii").splitlines() if line),
            worktree_path=str(execution.worktree_path),
            artifact_references=tuple(artifact_references),
        )

    def deliver(
        self,
        execution: RepositoryExecution,
        *,
        enabled: bool = False,
        remote: str | None = None,
        remote_branch: str | None = None,
    ) -> DeliveryResult:
        self.heartbeat(execution)
        head = (
            _git(execution.worktree_path, "rev-parse", "HEAD", operation="resolve delivery SHA")
            .stdout.decode("ascii")
            .strip()
        )
        if not enabled:
            return DeliveryResult(True, DeliveryState.NOT_REQUESTED, head)
        config = self.resolve(execution.repository_id)
        selected_remote = remote or config.default_remote
        selected_branch = remote_branch or execution.branch
        try:
            _validate_remote(selected_remote)
            _validate_ref(selected_branch, "remote_branch")
        except RepositoryValidationError as exc:
            return DeliveryResult(
                True,
                DeliveryState.FAILED,
                head,
                selected_remote,
                failure_reason=DeliveryFailureReason.INVALID_REMOTE,
                detail=str(exc),
            )
        protected = set(config.protected_branches)
        if selected_branch in protected or selected_branch != execution.branch:
            return DeliveryResult(
                True,
                DeliveryState.FAILED,
                head,
                selected_remote,
                f"refs/heads/{selected_branch}",
                failure_reason=DeliveryFailureReason.PROTECTED_BRANCH,
            )
        remote_ref = f"refs/heads/{selected_branch}"
        push = _git_optional(
            execution.worktree_path,
            "push",
            "--porcelain",
            selected_remote,
            f"refs/heads/{execution.branch}:{remote_ref}",
        )
        if push.returncode != 0:
            return DeliveryResult(
                True,
                DeliveryState.FAILED,
                head,
                selected_remote,
                remote_ref,
                failure_reason=DeliveryFailureReason.PUSH_REJECTED,
                detail=_redact_diagnostic(push.stderr.decode(errors="replace").strip()),
            )
        verify = _git_optional(
            execution.worktree_path,
            "ls-remote",
            "--refs",
            selected_remote,
            remote_ref,
        )
        records = verify.stdout.decode("ascii", errors="replace").splitlines()
        remote_sha = next(
            (
                line.split()[0]
                for line in records
                if len(line.split()) == 2 and line.split()[1] == remote_ref
            ),
            None,
        )
        if remote_sha is None:
            reason = DeliveryFailureReason.REMOTE_REF_MISSING
        elif remote_sha != head:
            reason = DeliveryFailureReason.REMOTE_SHA_MISMATCH
        else:
            return DeliveryResult(
                True,
                DeliveryState.VERIFIED,
                head,
                selected_remote,
                remote_ref,
                remote_sha,
            )
        return DeliveryResult(
            True,
            DeliveryState.FAILED,
            head,
            selected_remote,
            remote_ref,
            remote_sha,
            reason,
        )

    def cleanup(self, execution: RepositoryExecution, *, delete_branch: bool = True) -> bool:
        lease = self._lease(execution)
        if not execution.worktree_path.exists() and not lease.metadata_path.exists():
            return False
        lease.heartbeat()
        removed = False
        try:
            if execution.worktree_path.exists():
                result = _git_optional(
                    execution.source_checkout,
                    "worktree",
                    "remove",
                    "--force",
                    str(execution.worktree_path),
                )
                if result.returncode != 0:
                    raise RepositoryCommandError(
                        "remove execution worktree",
                        result.stderr.decode(errors="replace").strip(),
                        result.returncode,
                    )
                removed = True
            _git_optional(execution.source_checkout, "worktree", "prune")
            if delete_branch:
                _git_optional(
                    execution.source_checkout,
                    "branch",
                    "-D",
                    "--",
                    execution.branch,
                )
            return removed
        finally:
            lease.release()

    def release(self, execution: RepositoryExecution) -> None:
        """Release only the execution lease, preserving its evidence worktree."""
        self._lease(execution).release()

    def _lease(self, execution: RepositoryExecution) -> RepositoryLease:
        key = hashlib.sha256(str(execution.repository_id).encode()).hexdigest()
        return RepositoryLease(
            self.runtime.locks_dir / "repositories" / key,
            execution.lock_token,
            str(execution.execution_id),
            60.0,
        )


def _git(cwd: Path, *args: str, operation: str) -> subprocess.CompletedProcess[bytes]:
    result = _git_optional(cwd, *args)
    if result.returncode:
        raise RepositoryCommandError(
            operation,
            _redact_diagnostic(result.stderr.decode(errors="replace").strip()),
            result.returncode,
        )
    return result


def _git_optional(cwd: Path, *args: str) -> subprocess.CompletedProcess[bytes]:
    return subprocess.run(
        ("git", "-C", os.fspath(cwd), *args),
        stdin=subprocess.DEVNULL,
        capture_output=True,
        check=False,
        shell=False,
        env={**os.environ, "GIT_TERMINAL_PROMPT": "0", "LC_ALL": "C"},
    )


def _validate_ref(value: str, label: str) -> None:
    if (
        not value
        or value.startswith("-")
        or value.startswith("/")
        or value.endswith(("/", "."))
        or not _SAFE_GIT_NAME.fullmatch(value)
        or any(part in value for part in _FORBIDDEN_REF_PARTS)
        or any(char in value for char in " ~^:?*[")
    ):
        raise RepositoryValidationError(f"unsafe {label}: {value!r}")


def _validate_remote(value: str) -> None:
    if not _SAFE_REMOTE.fullmatch(value) or value in {".", ".."}:
        raise RepositoryValidationError(f"unsafe remote name: {value!r}")


def _execution_branch(repository_id: RepositoryId, execution_id: ExecutionId, base_sha: str) -> str:
    digest = hashlib.sha256(f"{repository_id}\0{execution_id}\0{base_sha}".encode()).hexdigest()[
        :16
    ]
    return f"sovereign-agent/{digest}"


def _assert_beneath(candidate: Path, root: Path) -> None:
    root_resolved = root.resolve()
    try:
        candidate.resolve(strict=False).relative_to(root_resolved)
    except ValueError as exc:
        raise RepositoryValidationError("path escapes governed root") from exc


def _nul_paths(value: bytes) -> tuple[str, ...]:
    return tuple(os.fsdecode(part) for part in value.split(b"\0") if part)


def _redact_remote(remote: str) -> str:
    parsed = urlsplit(remote)
    if parsed.scheme and parsed.netloc:
        hostname = parsed.hostname or ""
        if parsed.port is not None:
            hostname = f"{hostname}:{parsed.port}"
        return urlunsplit((parsed.scheme, hostname, parsed.path, "", ""))
    if "@" in remote and ":" in remote.split("@", 1)[1]:
        return remote.split("@", 1)[1]
    return remote


def _redact_diagnostic(value: str) -> str:
    return redact_text(_URL_USERINFO.sub(lambda match: f"{match.group(1)}{REDACTED}@", value))


__all__ = ["RepositoryManager"]
