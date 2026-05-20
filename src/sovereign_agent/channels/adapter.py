"""Channel adapters: where a message comes from (v0.3, Module 1).

## Why this exists

v0.2 has no concept of "where a message came from". `run_task(task)` takes
a string and runs one session to completion; `Orchestrator.run()` only ever
processes sessions that were queued before it started or enqueued by some
other Python code. There is no way for a student to hold an ongoing
conversation with the agent they built — every demo in `examples/` is
one-shot, with the task hard-coded in a Python file.

A `ChannelAdapter` is the abstraction that separates *transport* (a Unix
socket, a Telegram bot, a Slack app) from *behaviour* (what the agent does
with a message). The orchestrator owns an `InboundRouter`; adapters call
`router.route(InboundEvent)` whenever a message arrives, and the router
turns that into a session.

## The protocol

A channel adapter is anything that satisfies the `ChannelAdapter` Protocol
below — no base class, no inheritance. The required surface is deliberately
tiny:

    name, channel_type, supports_threads   (declared attributes)
    setup(router)                          (called once at orchestrator start)
    teardown()                             (called once at shutdown)
    deliver(platform_id, thread_id, msg)   (send a message back out)

Optional capabilities — `open_dm`, `subscribe`, `set_typing` — are NOT part
of the Protocol. An adapter either has them or it doesn't; the router
duck-types with `hasattr()`. Presence is the signal. Keeping the mandatory
surface this small is what makes the acceptance criterion true: a 50-line
test double is a real, conforming adapter (see tests/test_channels_protocol.py).
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import TYPE_CHECKING, Protocol, runtime_checkable

from sovereign_agent.session.state import _parse_dt, now_utc

if TYPE_CHECKING:
    from sovereign_agent.channels.router import InboundRouter


@dataclass
class InboundEvent:
    """One inbound message the router will dispatch.

    `sender_id` is channel-namespaced ("cli:local", "tg:12345") so two
    channels can never collide on sender identity. `is_mention` is set by
    the adapter when it can confirm — from the platform's own mention
    semantics — that the bot was addressed. The router trusts that flag;
    it does not try to infer mentions from the text itself. (v0.3 Module 2
    builds engage modes on top of this declared flag.)
    """

    channel_type: str
    platform_id: str
    thread_id: str | None
    sender_id: str | None
    text: str
    timestamp: datetime
    is_mention: bool = False

    def to_dict(self) -> dict:
        return {
            "channel_type": self.channel_type,
            "platform_id": self.platform_id,
            "thread_id": self.thread_id,
            "sender_id": self.sender_id,
            "text": self.text,
            "timestamp": self.timestamp.isoformat(),
            "is_mention": self.is_mention,
        }

    @classmethod
    def from_dict(cls, d: dict) -> InboundEvent:
        ts = d.get("timestamp")
        return cls(
            channel_type=d["channel_type"],
            platform_id=d["platform_id"],
            thread_id=d.get("thread_id"),
            sender_id=d.get("sender_id"),
            text=d.get("text", ""),
            timestamp=_parse_dt(ts) if ts else now_utc(),
            is_mention=bool(d.get("is_mention", False)),
        )


@dataclass
class OutboundMessage:
    """A channel-agnostic message the agent wants delivered.

    `kind` is "text" | "edit" | "reaction"; `content` is a free-form
    payload whose shape depends on `kind`. For "text", content is
    `{"text": "..."}`. Adapters translate this into whatever their
    platform's wire format needs.
    """

    kind: str
    content: dict

    @classmethod
    def text(cls, text: str) -> OutboundMessage:
        """Convenience constructor for the common plain-text case."""
        return cls(kind="text", content={"text": text})


@runtime_checkable
class ChannelAdapter(Protocol):
    """The interface the orchestrator uses to talk to a channel.

    Implementations need not inherit from anything — satisfying the
    structural shape is enough. See `CliChannelAdapter` for a worked
    example and tests/test_channels_protocol.py for a tiny test double
    that conforms without a base class.
    """

    name: str
    channel_type: str
    supports_threads: bool

    async def setup(self, router: InboundRouter) -> None:
        """Start the transport (open the socket, connect the bot) and keep
        a reference to `router` so inbound messages can be dispatched."""
        ...

    async def teardown(self) -> None:
        """Stop the transport cleanly. Called during orchestrator shutdown."""
        ...

    async def deliver(
        self,
        platform_id: str,
        thread_id: str | None,
        message: OutboundMessage,
    ) -> str | None:
        """Send `message` out on this channel. Return the platform-assigned
        message id if the platform has one, else None."""
        ...


__all__ = ["ChannelAdapter", "InboundEvent", "OutboundMessage"]
