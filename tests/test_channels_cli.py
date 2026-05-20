"""v0.3 Module 1 — CliChannelAdapter over an in-process Unix socket.

These tests start a real adapter on a temp-path socket, connect real
clients to it, and assert on routing, file permissions, supersession, and
clean teardown. No mocking of the socket layer — the point of the CLI
channel is that the transport is real.

Tests are sync; each spins up its own event loop via asyncio.run().
"""

from __future__ import annotations

import asyncio
import json
import os
import shutil
import tempfile
from pathlib import Path

import pytest

from sovereign_agent.channels.cli import CliChannelAdapter, SUPERSEDED_NOTICE
from sovereign_agent.channels.router import InboundRouter
from sovereign_agent.session.directory import list_sessions


# ---------------------------------------------------------------------------
# Why this fixture exists
# ---------------------------------------------------------------------------
# pytest's `tmp_path` on macOS lives under
#     /private/var/folders/<hash>/T/pytest-of-<user>/pytest-N/<test-name>/
# which is ~80 chars before you add a filename. AF_UNIX sun_path is capped
# at ~104 bytes on macOS (108 on Linux), so binding `tmp_path / "cli.sock"`
# fails with `OSError: AF_UNIX path too long`. We route socket paths via a
# short base (/tmp where available) and clean up after the test.
# ---------------------------------------------------------------------------
@pytest.fixture
def sock_path() -> Path:
    base = "/tmp" if os.path.isdir("/tmp") else tempfile.gettempdir()
    d = tempfile.mkdtemp(prefix="sa_sock_", dir=base)
    try:
        yield Path(d) / "cli.sock"
    finally:
        shutil.rmtree(d, ignore_errors=True)


class FakeQueue:
    def __init__(self) -> None:
        self.enqueued: list[str] = []

    async def enqueue_planner(self, session_id: str) -> None:
        self.enqueued.append(session_id)


async def _wait_for(predicate, *, attempts: int = 100, delay: float = 0.02) -> bool:
    """Poll an async-friendly predicate until true or attempts run out."""
    for _ in range(attempts):
        if predicate():
            return True
        await asyncio.sleep(delay)
    return predicate()


def test_cli_adapter_routes_a_message(tmp_path, sock_path):
    async def _run() -> None:
        sessions_dir = tmp_path / "sessions"
        queue = FakeQueue()
        router = InboundRouter(queue, sessions_dir=sessions_dir)
        adapter = CliChannelAdapter(socket_path=sock_path)
        await adapter.setup(router)
        try:
            reader, writer = await asyncio.open_unix_connection(path=str(sock_path))
            writer.write((json.dumps({"text": "book a pub"}) + "\n").encode())
            await writer.drain()

            assert await _wait_for(lambda: bool(queue.enqueued)), "router never enqueued"
            sessions = list_sessions(sessions_dir=sessions_dir)
            assert len(sessions) == 1
            assert sessions[0].iter_inbox_events()[0]["text"] == "book a pub"
            writer.close()
        finally:
            await adapter.teardown()

    asyncio.run(_run())


def test_socket_file_is_chmod_0600(tmp_path, sock_path):
    async def _run() -> None:
        adapter = CliChannelAdapter(socket_path=sock_path)
        await adapter.setup(InboundRouter(FakeQueue(), sessions_dir=tmp_path / "s"))
        try:
            assert (sock_path.stat().st_mode & 0o777) == 0o600
        finally:
            await adapter.teardown()

    asyncio.run(_run())


def test_second_client_supersedes_the_first(tmp_path, sock_path):
    async def _run() -> None:
        adapter = CliChannelAdapter(socket_path=sock_path)
        await adapter.setup(InboundRouter(FakeQueue(), sessions_dir=tmp_path / "s"))
        try:
            reader1, writer1 = await asyncio.open_unix_connection(path=str(sock_path))
            # Let the server register the first client before the second connects.
            await asyncio.sleep(0.1)
            reader2, writer2 = await asyncio.open_unix_connection(path=str(sock_path))

            line = await asyncio.wait_for(reader1.readline(), timeout=2.0)
            notice = json.loads(line.decode())
            assert notice["text"] == SUPERSEDED_NOTICE
            writer2.close()
        finally:
            await adapter.teardown()

    asyncio.run(_run())


def test_teardown_removes_the_socket_file(tmp_path, sock_path):
    async def _run() -> None:
        adapter = CliChannelAdapter(socket_path=sock_path)
        await adapter.setup(InboundRouter(FakeQueue(), sessions_dir=tmp_path / "s"))
        assert sock_path.exists()
        await adapter.teardown()
        assert not sock_path.exists()

    asyncio.run(_run())


def test_malformed_line_is_ignored_not_fatal(tmp_path, sock_path):
    async def _run() -> None:
        queue = FakeQueue()
        adapter = CliChannelAdapter(socket_path=sock_path)
        await adapter.setup(InboundRouter(queue, sessions_dir=tmp_path / "sessions"))
        try:
            reader, writer = await asyncio.open_unix_connection(path=str(sock_path))
            writer.write(b"this is not json\n")
            await writer.drain()
            # A good message after the bad line must still route.
            writer.write((json.dumps({"text": "still works"}) + "\n").encode())
            await writer.drain()
            assert await _wait_for(lambda: bool(queue.enqueued))
            writer.close()
        finally:
            await adapter.teardown()

    asyncio.run(_run())