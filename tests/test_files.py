"""Behavioral proofs for the file boundary."""

from __future__ import annotations

import os
import threading
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from unittest.mock import patch

import pytest

from sovereign_agent.files import atomic_write


def test_atomic_write_replaces_the_target_and_removes_its_tempfile(tmp_path: Path) -> None:
    target = tmp_path / "state.json"
    target.write_bytes(b"old")

    atomic_write(target, b"new")

    assert target.read_bytes() == b"new"
    assert list(tmp_path.glob(".state.json.*.tmp")) == []


def test_atomic_write_preserves_the_old_value_when_replace_fails(tmp_path: Path) -> None:
    target = tmp_path / "state.json"
    target.write_bytes(b"old")

    with patch("sovereign_agent.files.os.replace", side_effect=OSError("injected failure")):
        with pytest.raises(OSError, match="injected failure"):
            atomic_write(target, b"new")

    assert target.read_bytes() == b"old"
    assert list(tmp_path.glob(".state.json.*.tmp")) == []


def test_concurrent_atomic_writers_never_share_a_tempfile_or_tear_bytes(
    tmp_path: Path,
) -> None:
    target = tmp_path / "state.json"
    payloads = (b"A" * 100_000, b"B" * 100_000)
    barrier = threading.Barrier(2)
    sources: list[Path] = []
    sources_lock = threading.Lock()
    real_replace = os.replace

    def synchronized_replace(source: Path, destination: Path) -> None:
        with sources_lock:
            sources.append(Path(source))
        barrier.wait()
        real_replace(source, destination)

    with patch("sovereign_agent.files.os.replace", side_effect=synchronized_replace):
        with ThreadPoolExecutor(max_workers=2) as pool:
            list(pool.map(lambda payload: atomic_write(target, payload), payloads))

    assert len(set(sources)) == 2
    assert target.read_bytes() in payloads
    assert list(tmp_path.glob(".state.json.*.tmp")) == []
