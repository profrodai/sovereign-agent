"""Small cross-platform advisory file-lock primitive."""

from __future__ import annotations

import os
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from threading import Lock

try:
    import fcntl
except ImportError:  # pragma: no cover - Windows
    fcntl = None  # type: ignore[assignment]

try:
    import msvcrt
except ImportError:  # pragma: no cover - POSIX
    msvcrt = None  # type: ignore[assignment]

_local_locks_guard = Lock()
_local_locks: dict[str, tuple[Lock, int]] = {}


@contextmanager
def _local_file_lock(path: Path) -> Iterator[None]:
    """Serialize threads before taking the process-level lock.

    Windows CRT byte-range locks do not reliably fence overlapping locks
    acquired by threads in the same process. Without this guard, one thread
    can release the byte range while another still believes it owns it, and
    the second ``LK_UNLCK`` then fails with ``PermissionError``.
    """
    key = os.path.normcase(str(path.resolve(strict=False)))
    with _local_locks_guard:
        lock, users = _local_locks.get(key, (Lock(), 0))
        _local_locks[key] = (lock, users + 1)
    try:
        with lock:
            yield
    finally:
        with _local_locks_guard:
            current_lock, users = _local_locks[key]
            if users == 1:
                del _local_locks[key]
            else:
                _local_locks[key] = (current_lock, users - 1)


@contextmanager
def exclusive_file_lock(path: Path) -> Iterator[None]:
    """Lock one byte until the context exits."""
    with _local_file_lock(path):
        flags = os.O_CREAT | os.O_RDWR | getattr(os, "O_BINARY", 0)
        fd = os.open(path, flags, 0o600)
        locked = False
        try:
            if fcntl is not None:
                fcntl.flock(fd, fcntl.LOCK_EX)
            elif msvcrt is not None:  # pragma: no cover - Windows
                if os.fstat(fd).st_size == 0:
                    os.write(fd, b"\0")
                os.lseek(fd, 0, os.SEEK_SET)
                msvcrt.locking(fd, msvcrt.LK_LOCK, 1)
            else:  # pragma: no cover
                raise RuntimeError("no cross-process file locking implementation is available")
            locked = True
            yield
        finally:
            try:
                if locked and fcntl is not None:
                    fcntl.flock(fd, fcntl.LOCK_UN)
                elif locked and msvcrt is not None:  # pragma: no cover - Windows
                    os.lseek(fd, 0, os.SEEK_SET)
                    msvcrt.locking(fd, msvcrt.LK_UNLCK, 1)
            finally:
                os.close(fd)


__all__ = ["exclusive_file_lock"]
