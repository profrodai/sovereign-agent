"""v0.3 Module 1 — end-to-end: adapter -> router -> session directory.

These tests exercise the whole inbound path with real components: a real
CliChannelAdapter, a real InboundRouter, real session directories on disk.
The SessionQueue is faked so the test does not need a running orchestrator
loop or an LLM — it asserts that the *plumbing* is correct: a socket
message becomes a session with an inbox and a binding file.

The final tests validate the orchestrator patch from this module: that
`Orchestrator(config, adapters=[...])` constructs and registers channels,
and that a bare `Orchestrator()` keeps v0.2 behaviour.
"""

from __future__ import annotations

import asyncio
import json
import os
import shutil
import tempfile
from pathlib import Path

import pytest

from sovereign_agent.channels.cli import CliChannelAdapter
from sovereign_agent.channels.router import InboundRouter
from sovereign_agent.session.directory import list_sessions


# See test_channels_cli.py for the rationale: macOS AF_UNIX paths are
# capped at ~104 bytes and pytest's tmp_path lives under a long
# /private/var/folders/... prefix, which exceeds the limit when you
# append "cli.sock". Bind sockets under a short base instead.
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


async def _wait_for_session(sessions_dir, *, attempts: int = 100, delay: float = 0.02):
    for _ in range(attempts):
        sessions = list_sessions(sessions_dir=sessions_dir)
        if sessions:
            return sessions[0]
        await asyncio.sleep(delay)
    return None


def test_message_creates_session_with_inbox_and_binding(tmp_path, sock_path):
    async def _run() -> None:
        sessions_dir = tmp_path / "sessions"
        router = InboundRouter(FakeQueue(), sessions_dir=sessions_dir)
        adapter = CliChannelAdapter(socket_path=sock_path)
        await adapter.setup(router)
        try:
            reader, writer = await asyncio.open_unix_connection(path=str(sock_path))
            writer.write((json.dumps({"text": "hello agent"}) + "\n").encode())
            await writer.drain()

            session = await _wait_for_session(sessions_dir)
            assert session is not None

            # 1. the inbound message landed in the session inbox
            events = session.iter_inbox_events()
            assert events and events[0]["text"] == "hello agent"

            # 2. the binding file was written *inside* the session directory
            binding_file = session.directory / "inbox" / "binding.json"
            assert binding_file.exists()
            binding = json.loads(binding_file.read_text(encoding="utf-8"))
            assert binding["channel_type"] == "cli"
            assert binding["platform_id"] == "cli-main"

            # 3. the router knows where to deliver this session's reply
            assert router.reply_target_for(session.session_id) == ("cli", "cli-main", None)
            writer.close()
        finally:
            await adapter.teardown()

    asyncio.run(_run())


def test_admin_to_retargets_and_reply_to_redirects(tmp_path, sock_path):
    """`to` binds the message as another channel; `reply_to` keeps the
    reply pointed back at the CLI client. This is the admin/test transport."""

    async def _run() -> None:
        sessions_dir = tmp_path / "sessions"
        router = InboundRouter(FakeQueue(), sessions_dir=sessions_dir)
        adapter = CliChannelAdapter(socket_path=sock_path)
        await adapter.setup(router)
        try:
            reader, writer = await asyncio.open_unix_connection(path=str(sock_path))
            payload = {
                "text": "pretend I am on telegram",
                "to": {"channel_type": "telegram", "platform_id": "tg-7"},
                "reply_to": True,
            }
            writer.write((json.dumps(payload) + "\n").encode())
            await writer.drain()

            session = await _wait_for_session(sessions_dir)
            assert session is not None

            # bound as telegram...
            binding = json.loads(
                (session.directory / "inbox" / "binding.json").read_text(encoding="utf-8")
            )
            assert binding["channel_type"] == "telegram"
            assert binding["platform_id"] == "tg-7"

            # ...but the reply is redirected back to the CLI client
            assert router.reply_target_for(session.session_id) == ("cli", "cli-main", None)
            writer.close()
        finally:
            await adapter.teardown()

    asyncio.run(_run())


def test_orchestrator_accepts_adapters(tmp_path):
    """Validates the orchestrator/main.py patch: the `adapters=` parameter,
    the ChannelRegistry, and the InboundRouter are all wired in.

    This test does NOT bind the socket (no setup() call), so it can keep
    using tmp_path for the socket path without hitting the AF_UNIX limit.
    """
    from sovereign_agent.config import Config
    from sovereign_agent.orchestrator import Orchestrator

    config = Config(sessions_dir=tmp_path / "sessions")
    adapter = CliChannelAdapter(socket_path=tmp_path / "cli.sock")
    orch = Orchestrator(config, adapters=[adapter])

    assert "cli" in orch.channels
    assert orch.channels.get("cli") is adapter
    assert orch.router is not None
    assert orch.router.sessions_dir == config.sessions_dir


def test_bare_orchestrator_has_no_adapters(tmp_path):
    """A bare Orchestrator (no adapters=) keeps v0.2 behaviour: an empty
    channel registry, but a router still available for later add_adapter()."""
    from sovereign_agent.config import Config
    from sovereign_agent.orchestrator import Orchestrator

    orch = Orchestrator(Config(sessions_dir=tmp_path / "sessions"))
    assert len(orch.channels) == 0
    assert orch.router is not None