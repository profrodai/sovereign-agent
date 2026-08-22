"""Durable lease locks with fenced stale-owner recovery."""

from __future__ import annotations

import json
import os
import secrets
import shutil
import socket
import time
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path

from sovereign_agent._internal.atomic import atomic_write_json

from .errors import RepositoryLockLost, RepositoryLockTimeout

try:
    import fcntl
except ImportError:  # pragma: no cover - exercised on Windows
    fcntl = None  # type: ignore[assignment]

try:
    import msvcrt
except ImportError:  # pragma: no cover - exercised on POSIX
    msvcrt = None  # type: ignore[assignment]


@dataclass(frozen=True)
class RepositoryLease:
    """Ownership handle. Its random token is the fencing generation."""

    path: Path
    token: str
    owner: str
    lease_seconds: float

    @property
    def metadata_path(self) -> Path:
        return self.path / "owner.json"

    def heartbeat(self) -> None:
        with _guard(self.path):
            try:
                metadata = _read_metadata(self.metadata_path)
            except (FileNotFoundError, ValueError) as exc:
                raise RepositoryLockLost("repository lock no longer exists") from exc
            if metadata.get("token") != self.token:
                raise RepositoryLockLost("repository lock ownership changed")
            metadata["heartbeat_ns"] = time.time_ns()
            atomic_write_json(self.metadata_path, metadata)

    def release(self) -> bool:
        """Release only this generation; an old owner cannot remove a successor."""
        with _guard(self.path):
            try:
                metadata = _read_metadata(self.metadata_path)
            except (FileNotFoundError, ValueError):
                return False
            if metadata.get("token") != self.token:
                return False
            tombstone = self.path.with_name(f".released-{self.token}")
            try:
                self.path.rename(tombstone)
            except FileNotFoundError:
                return False
        shutil.rmtree(tombstone, ignore_errors=True)
        return True

    def __enter__(self) -> RepositoryLease:
        return self

    def __exit__(self, *_args: object) -> None:
        self.release()


class RepositoryLockManager:
    def __init__(self, locks_root: Path) -> None:
        self._root = Path(locks_root)

    def acquire(
        self,
        key: str,
        *,
        timeout: float = 30.0,
        lease_seconds: float = 60.0,
        poll_interval: float = 0.05,
        owner: str | None = None,
    ) -> RepositoryLease:
        if not key or "/" in key or "\\" in key or key in {".", ".."}:
            raise ValueError("lock key must be one safe path component")
        if timeout < 0 or lease_seconds <= 0 or poll_interval <= 0:
            raise ValueError("invalid lock timing")
        self._root.mkdir(mode=0o700, parents=True, exist_ok=True)
        lock_path = self._root / key
        deadline = time.monotonic() + timeout
        owner_name = owner or f"{socket.gethostname()}:{os.getpid()}"

        while True:
            token = secrets.token_hex(16)
            acquired = False
            with _guard(lock_path):
                try:
                    lock_path.mkdir(mode=0o700)
                    acquired = True
                except FileExistsError:
                    self._recover_if_stale(lock_path, lease_seconds)
                if acquired:
                    metadata = {
                        "token": token,
                        "owner": owner_name,
                        "pid": os.getpid(),
                        "hostname": socket.gethostname(),
                        "acquired_ns": time.time_ns(),
                        "heartbeat_ns": time.time_ns(),
                        "lease_seconds": lease_seconds,
                    }
                    try:
                        atomic_write_json(lock_path / "owner.json", metadata)
                    except BaseException:
                        shutil.rmtree(lock_path, ignore_errors=True)
                        raise
            if not acquired:
                if time.monotonic() >= deadline:
                    raise RepositoryLockTimeout(f"timed out acquiring repository lock {key!r}")
                time.sleep(min(poll_interval, max(0.0, deadline - time.monotonic())))
                continue
            return RepositoryLease(lock_path, token, owner_name, lease_seconds)

    @staticmethod
    def _recover_if_stale(lock_path: Path, lease_seconds: float) -> bool:
        try:
            metadata = _read_metadata(lock_path / "owner.json")
            heartbeat_value = metadata["heartbeat_ns"]
            if not isinstance(heartbeat_value, int):
                raise TypeError("heartbeat_ns is not an integer")
            heartbeat_ns = heartbeat_value
            token = str(metadata["token"])
            owner_lease = metadata.get("lease_seconds")
            if (
                not isinstance(owner_lease, (int, float))
                or isinstance(owner_lease, bool)
                or owner_lease <= 0
            ):
                raise TypeError("lease_seconds is not positive")
        except (FileNotFoundError, KeyError, TypeError, ValueError, json.JSONDecodeError):
            # A newly-created lock may not have metadata yet; its mtime gets one lease.
            try:
                stale = time.time() - lock_path.stat().st_mtime > lease_seconds
            except FileNotFoundError:
                return True
            token = "incomplete"
        else:
            stale = time.time_ns() - heartbeat_ns > int(owner_lease * 1_000_000_000)
        if not stale:
            return False
        tombstone = lock_path.with_name(f".stale-{token}-{secrets.token_hex(4)}")
        try:
            lock_path.rename(tombstone)
        except FileNotFoundError:
            return True
        shutil.rmtree(tombstone, ignore_errors=True)
        return True


def _read_metadata(path: Path) -> dict[str, object]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("lock metadata is not an object")
    return data


@contextmanager
def _guard(lock_path: Path) -> Iterator[None]:
    """Serialize generation transitions without making the guard itself ownership."""
    guard_path = lock_path.with_suffix(lock_path.suffix + ".guard")
    guard_path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    fd = os.open(guard_path, os.O_CREAT | os.O_RDWR, 0o600)
    try:
        _lock_fd(fd)
        yield
    finally:
        _unlock_fd(fd)
        os.close(fd)


def _lock_fd(fd: int) -> None:
    if fcntl is not None:
        fcntl.flock(fd, fcntl.LOCK_EX)
        return
    if msvcrt is None:  # pragma: no cover - supported Python platforms provide one
        raise RuntimeError("no cross-process file locking implementation is available")
    if os.fstat(fd).st_size == 0:
        os.write(fd, b"\0")
    os.lseek(fd, 0, os.SEEK_SET)
    msvcrt.locking(fd, msvcrt.LK_LOCK, 1)


def _unlock_fd(fd: int) -> None:
    if fcntl is not None:
        fcntl.flock(fd, fcntl.LOCK_UN)
        return
    if msvcrt is None:  # pragma: no cover
        return
    os.lseek(fd, 0, os.SEEK_SET)
    msvcrt.locking(fd, msvcrt.LK_UNLCK, 1)


__all__ = ["RepositoryLease", "RepositoryLockManager"]
