"""CliChannelAdapter: a conversation over a Unix socket (v0.3, Module 1).

This is the first concrete channel. It listens on a Unix domain socket and
speaks a line-delimited JSON protocol — one JSON object per line, in each
direction. It is the adapter `sovereign-agent chat` and `sovereign-agent
serve` use.

## Protocol

Client -> server (one JSON object per line):
    {"text": "book a pub near haymarket for 4"}

  Optional admin/test fields:
    {"text": "...",
     "to": {"channel_type": "telegram", "platform_id": "chat-123"},
     "reply_to": true}

  `to` re-targets the event: the router binds it as if it had arrived on
  that other channel. `reply_to` keeps the agent's reply coming back to
  *this* CLI client even so. Together they are how you test multi-channel
  routing, and how an admin injects a message on another channel's behalf,
  without a second adapter actually being connected.

Server -> client (one JSON object per agent reply):
    {"text": "I found three candidates..."}

## Single conversation, supersedable

The default CLI conversation is a single binding ("cli", "cli-main", None).
At most one client is connected to a given platform_id at a time: when a
second client connects, the first is sent
`{"text": "[superseded by a newer client]"}` and disconnected. This keeps
the teaching model simple — one terminal, one conversation — while
demonstrating a real adapter concern (who owns the connection) without a
full session-multiplexing design.

## Why a Unix socket and not stdin/stdout

A socket forces the transport/behaviour split to be real: the adapter
*serves* a socket; a separate client *connects* to it. `serve` can run the
adapter as a daemon; `chat` can be a pure client. The socket file is
created with mode 0600 — only the owning user can connect to it.
"""

from __future__ import annotations

import asyncio
import contextlib
import json
import logging
import os
from pathlib import Path
from typing import TYPE_CHECKING

from sovereign_agent._internal.paths import user_data_dir
from sovereign_agent.channels.adapter import InboundEvent, OutboundMessage
from sovereign_agent.session.state import now_utc

if TYPE_CHECKING:
    from sovereign_agent.channels.router import InboundRouter

log = logging.getLogger(__name__)

DEFAULT_PLATFORM_ID = "cli-main"
SUPERSEDED_NOTICE = "[superseded by a newer client]"


def default_socket_path() -> Path:
    """The on-by-default CLI channel socket path.

    Lives under the platform user-data dir (see _internal/paths.py) so it
    never pollutes the user's working tree.
    """
    return user_data_dir() / "channels" / "cli.sock"


class CliChannelAdapter:
    """A `ChannelAdapter` that speaks line-delimited JSON over a Unix socket."""

    # Declared adapter attributes — this is what makes isinstance() against
    # the ChannelAdapter Protocol succeed.
    # v0.3 Module 3: Plugin contract. Concrete adapters declare
    # their kind directly — Protocol class attributes do not
    # propagate to non-subclass implementations.
    kind = "channel"
    name = "cli"
    channel_type = "cli"
    supports_threads = False

    def __init__(
        self,
        *,
        socket_path: Path | None = None,
        platform_id: str = DEFAULT_PLATFORM_ID,
    ) -> None:
        self.socket_path = socket_path or default_socket_path()
        self.platform_id = platform_id
        self._router: InboundRouter | None = None
        self._server: asyncio.AbstractServer | None = None
        # The current client's writer, keyed by platform_id. At most one
        # per platform_id — a new connection supersedes the old.
        self._clients: dict[str, asyncio.StreamWriter] = {}

    # ------------------------------------------------------------------
    # Lifecycle (ChannelAdapter protocol)
    # ------------------------------------------------------------------
    async def setup(self, router: InboundRouter) -> None:
        self._router = router
        self.socket_path.parent.mkdir(parents=True, exist_ok=True)
        # A stale socket file from an unclean shutdown would block bind().
        with contextlib.suppress(FileNotFoundError):
            self.socket_path.unlink()
        self._server = await asyncio.start_unix_server(
            self._handle_client, path=str(self.socket_path)
        )
        os.chmod(self.socket_path, 0o600)
        log.info("cli channel listening on %s", self.socket_path)

    async def teardown(self) -> None:
        for writer in list(self._clients.values()):
            with contextlib.suppress(Exception):
                writer.close()
        self._clients.clear()
        if self._server is not None:
            self._server.close()
            with contextlib.suppress(Exception):
                await self._server.wait_closed()
            self._server = None
        with contextlib.suppress(FileNotFoundError):
            self.socket_path.unlink()

    async def deliver(
        self,
        platform_id: str,
        thread_id: str | None,
        message: OutboundMessage,
    ) -> str | None:
        """Send the agent's reply to whichever client owns `platform_id`."""
        writer = self._clients.get(platform_id)
        if writer is None:
            log.debug("cli channel: no connected client for %s; reply dropped", platform_id)
            return None
        if message.kind == "text":
            text = message.content.get("text", "")
        else:
            # Non-text kinds aren't rendered specially by the CLI; show raw.
            text = json.dumps(message.content)
        await self._send(writer, {"text": text})
        return None  # the CLI protocol has no platform message ids

    # ------------------------------------------------------------------
    # Socket server internals
    # ------------------------------------------------------------------
    async def _handle_client(
        self,
        reader: asyncio.StreamReader,
        writer: asyncio.StreamWriter,
    ) -> None:
        # The default CLI conversation is a single binding. A client owns
        # this adapter's platform_id; a second client supersedes the first.
        platform_id = self.platform_id
        old = self._clients.get(platform_id)
        if old is not None and old is not writer:
            with contextlib.suppress(Exception):
                await self._send(old, {"text": SUPERSEDED_NOTICE})
                old.close()
        self._clients[platform_id] = writer
        try:
            while True:
                line = await reader.readline()
                if not line:
                    break  # client disconnected
                await self._on_line(platform_id, line)
        except (ConnectionResetError, asyncio.CancelledError):
            pass
        finally:
            if self._clients.get(platform_id) is writer:
                del self._clients[platform_id]
            with contextlib.suppress(Exception):
                writer.close()

    async def _on_line(self, platform_id: str, line: bytes) -> None:
        if self._router is None:
            return
        try:
            msg = json.loads(line.decode("utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError):
            log.warning("cli channel: ignoring malformed protocol line")
            return
        if not isinstance(msg, dict):
            return
        text = str(msg.get("text", ""))
        if not text:
            return

        # `to` re-targets the event; default is this CLI channel itself.
        to = msg.get("to") or {}
        channel_type = to.get("channel_type", self.channel_type)
        target_platform = to.get("platform_id", platform_id)
        thread_id = to.get("thread_id")

        event = InboundEvent(
            channel_type=channel_type,
            platform_id=target_platform,
            thread_id=thread_id,
            sender_id=f"cli:{platform_id}",
            text=text,
            timestamp=now_utc(),
            # A CLI DM is always addressed to the agent — Module 2's
            # engage modes rely on this declared flag.
            is_mention=True,
        )

        # `reply_to` keeps the reply on THIS CLI client even when `to`
        # routed the message to another channel's binding.
        reply_to = None
        if msg.get("reply_to"):
            reply_to = (self.channel_type, platform_id, None)

        await self._router.route(event, reply_to=reply_to)

    async def _send(self, writer: asyncio.StreamWriter, obj: dict) -> None:
        writer.write((json.dumps(obj) + "\n").encode("utf-8"))
        await writer.drain()


__all__ = ["CliChannelAdapter", "DEFAULT_PLATFORM_ID", "SUPERSEDED_NOTICE", "default_socket_path"]
