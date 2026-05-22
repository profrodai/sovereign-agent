"""Tests for the M4b heartbeat file behaviour.

The heartbeat content (pid, started_at) stays static after the first tick;
external observers care about the file's mtime, not its body. These tests
pin both: the body is written exactly once per process, and the mtime
advances on every subsequent tick.
"""

from __future__ import annotations

import asyncio
import json
import os
import time
from pathlib import Path

from sovereign_agent.orchestrator.liveness import HEARTBEAT_FILENAME, LivenessMonitor


def _heartbeat_path(sessions_dir: Path) -> Path:
    return sessions_dir / HEARTBEAT_FILENAME


def test_heartbeat_written_with_pid_and_started_at(tmp_path: Path) -> None:
    monitor = LivenessMonitor(
        sessions_dir=tmp_path,
        stall_threshold_s=600.0,
        poll_interval_s=60.0,
    )

    async def _one_tick() -> None:
        monitor._write_heartbeat()
        await monitor._scan_once()

    asyncio.run(_one_tick())

    path = _heartbeat_path(tmp_path)
    assert path.exists()
    body = json.loads(path.read_text())
    assert body["pid"] == os.getpid()
    assert "started_at" in body and isinstance(body["started_at"], str)


def test_heartbeat_mtime_advances_on_subsequent_tick(tmp_path: Path) -> None:
    monitor = LivenessMonitor(
        sessions_dir=tmp_path,
        stall_threshold_s=600.0,
        poll_interval_s=60.0,
    )
    monitor._write_heartbeat()
    path = _heartbeat_path(tmp_path)
    first_mtime = path.stat().st_mtime
    first_body = path.read_text()

    # File-system mtimes typically have a 1ms granularity, sometimes 1s
    # on coarse filesystems. Sleep enough to guarantee a tick.
    time.sleep(0.05)

    monitor._write_heartbeat()
    second_mtime = path.stat().st_mtime
    second_body = path.read_text()

    assert second_mtime > first_mtime
    assert second_body == first_body  # content static across ticks


def test_heartbeat_recreated_if_deleted_between_ticks(tmp_path: Path) -> None:
    # An operator deleting .orchestrator_heartbeat shouldn't leave the
    # process silently never re-arming. Second tick after delete must
    # rewrite the file fresh.
    monitor = LivenessMonitor(
        sessions_dir=tmp_path,
        stall_threshold_s=600.0,
        poll_interval_s=60.0,
    )
    monitor._write_heartbeat()
    path = _heartbeat_path(tmp_path)
    assert path.exists()

    path.unlink()
    assert not path.exists()

    monitor._write_heartbeat()  # graceful re-arm
    # Third tick should now write content again (the re-arm cleared the flag).
    monitor._write_heartbeat()
    assert path.exists()
    body = json.loads(path.read_text())
    assert body["pid"] == os.getpid()
