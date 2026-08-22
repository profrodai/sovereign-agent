"""v0.3 Module 1 — ChannelAdapter protocol conformance.

These tests pin the central acceptance criterion: a channel adapter is a
*structural* thing. A small class that declares the right attributes and
methods IS an adapter — no base class, no registration, no inheritance.

All tests are plain sync functions; async work is driven with
`asyncio.run()` so the suite needs no pytest-asyncio dependency.
"""

from __future__ import annotations

import asyncio
from datetime import UTC, datetime

from sovereign_agent.channels.adapter import (
    ChannelAdapter,
    InboundEvent,
    OutboundMessage,
)


class TinyAdapter:
    """A complete, conforming channel adapter in well under 50 lines.

    It inherits from nothing. Satisfying the structural shape of the
    ChannelAdapter Protocol is the entire contract.
    """

    kind = "channel"
    name = "tiny"
    channel_type = "tiny"
    supports_threads = False

    def __init__(self) -> None:
        self.router = None
        self.delivered: list = []

    async def setup(self, router) -> None:
        self.router = router

    async def teardown(self) -> None:
        self.router = None

    async def deliver(self, platform_id, thread_id, message):
        self.delivered.append((platform_id, thread_id, message))
        return "tiny-msg-1"


def test_tiny_adapter_satisfies_protocol():
    # runtime_checkable Protocol — isinstance verifies the structural shape.
    assert isinstance(TinyAdapter(), ChannelAdapter)


def test_plain_object_does_not_satisfy_protocol():
    class NotAnAdapter:
        name = "nope"

    assert not isinstance(NotAnAdapter(), ChannelAdapter)


def test_inbound_event_roundtrips_through_dict():
    event = InboundEvent(
        channel_type="tiny",
        platform_id="p1",
        thread_id=None,
        sender_id="tiny:bob",
        text="hello there",
        timestamp=datetime(2026, 5, 1, 9, 30, tzinfo=UTC),
        is_mention=True,
    )
    restored = InboundEvent.from_dict(event.to_dict())
    assert restored.text == "hello there"
    assert restored.channel_type == "tiny"
    assert restored.sender_id == "tiny:bob"
    assert restored.is_mention is True
    assert restored.timestamp == event.timestamp


def test_inbound_event_from_dict_tolerates_missing_optionals():
    restored = InboundEvent.from_dict({"channel_type": "tiny", "platform_id": "p1", "text": "hi"})
    assert restored.thread_id is None
    assert restored.sender_id is None
    assert restored.is_mention is False
    assert restored.timestamp is not None  # defaults to now


def test_outbound_message_text_helper():
    message = OutboundMessage.text("the answer is 42")
    assert message.kind == "text"
    assert message.content == {"text": "the answer is 42"}


def test_setup_teardown_cycle():
    adapter = TinyAdapter()
    asyncio.run(adapter.setup(router="ROUTER"))
    assert adapter.router == "ROUTER"
    asyncio.run(adapter.teardown())
    assert adapter.router is None


def test_deliver_returns_platform_id_or_none():
    adapter = TinyAdapter()
    result = asyncio.run(adapter.deliver("p1", None, OutboundMessage.text("hi")))
    assert result == "tiny-msg-1"
    assert len(adapter.delivered) == 1
