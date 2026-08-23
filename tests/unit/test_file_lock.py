"""Cross-platform regression tests for the advisory file lock."""

from __future__ import annotations

import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from threading import Lock

from sovereign_agent._internal import file_lock


class _ProcessWideWindowsLock:
    """Model the CRT behavior that does not fence same-process threads."""

    LK_LOCK = 1
    LK_UNLCK = 2

    @staticmethod
    def locking(_fd: int, _mode: int, _nbytes: int) -> None:
        return


def test_windows_file_lock_serializes_threads(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr(file_lock, "fcntl", None)
    monkeypatch.setattr(file_lock, "msvcrt", _ProcessWideWindowsLock())

    state_lock = Lock()
    active = 0
    maximum_active = 0

    def guarded_work() -> None:
        nonlocal active, maximum_active
        with file_lock.exclusive_file_lock(tmp_path / "shared.lock"):
            with state_lock:
                active += 1
                maximum_active = max(maximum_active, active)
            time.sleep(0.01)
            with state_lock:
                active -= 1

    with ThreadPoolExecutor(max_workers=8) as pool:
        list(pool.map(lambda _: guarded_work(), range(20)))

    assert maximum_active == 1
