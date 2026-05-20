"""v0.3 Module 1 — InboundRouter: find-or-create, idempotency, cold start.

The router is the seam between "a message arrived" and "a session runs".
These tests pin the four behaviours that make it trustworthy:

  * a new conversation creates a session,
  * a continuing conversation reuses it,
  * a duplicate delivery is dropped (idempotency),
  * a cold-started router rediscovers bindings from disk,
  * a terminal session is not revived — a fresh one is created.

Tests are sync; async work runs via asyncio.run(). The SessionQueue is
faked so the tests assert on enqueue calls without a live orchestrator.
"""

from __future__ import annotations

import asyncio
from datetime import datetime, timezone

from sovereign_agent.channels.adapter import InboundEvent
from sovereign_agent.channels.router import InboundRouter
from sovereign_agent.session.directory import load_session


class FakeQueue:
    """Records enqueue_planner calls; that is all the router needs."""

    def __init__(self) -> None:
        self.enqueued: list[str] = []

    async def enqueue_planner(self, session_id: str) -> None:
        self.enqueued.append(session_id)


def _event(text: str, *, ts: datetime | None = None, platform: str = "cli-main") -> InboundEvent:
    return InboundEvent(
        channel_type="cli",
        platform_id=platform,
        thread_id=None,
        sender_id="cli:local",
        text=text,
        timestamp=ts or datetime(2026, 5, 1, 12, 0, 0, tzinfo=timezone.utc),
    )


def test_route_creates_a_session(tmp_path):
    queue = FakeQueue()
    router = InboundRouter(queue, sessions_dir=tmp_path)

    session_id = asyncio.run(router.route(_event("first message")))

    assert session_id.startswith("sess_")
    assert queue.enqueued == [session_id]
    session = load_session(session_id, sessions_dir=tmp_path)
    inbox = session.iter_inbox_events()
    assert len(inbox) == 1
    assert inbox[0]["text"] == "first message"


def test_route_reuses_session_for_same_binding(tmp_path):
    queue = FakeQueue()
    router = InboundRouter(queue, sessions_dir=tmp_path)

    sid1 = asyncio.run(
        router.route(_event("one", ts=datetime(2026, 5, 1, 12, 0, 0, tzinfo=timezone.utc)))
    )
    sid2 = asyncio.run(
        router.route(_event("two", ts=datetime(2026, 5, 1, 12, 0, 1, tzinfo=timezone.utc)))
    )

    assert sid1 == sid2
    session = load_session(sid1, sessions_dir=tmp_path)
    assert [e["text"] for e in session.iter_inbox_events()] == ["one", "two"]


def test_route_is_idempotent_on_exact_duplicate(tmp_path):
    queue = FakeQueue()
    router = InboundRouter(queue, sessions_dir=tmp_path)
    event = _event("retry me", ts=datetime(2026, 5, 1, 12, 0, 0, tzinfo=timezone.utc))

    sid1 = asyncio.run(router.route(event))
    sid2 = asyncio.run(router.route(event))  # identical event, e.g. an adapter retry

    assert sid1 == sid2
    # exactly one enqueue and one inbox event despite two route() calls
    assert queue.enqueued == [sid1]
    session = load_session(sid1, sessions_dir=tmp_path)
    assert len(session.iter_inbox_events()) == 1


def test_cold_start_router_recovers_binding_from_disk(tmp_path):
    # First router instance creates the session + binding.json.
    sid = asyncio.run(
        InboundRouter(FakeQueue(), sessions_dir=tmp_path).route(
            _event("before restart", ts=datetime(2026, 5, 1, 12, 0, 0, tzinfo=timezone.utc))
        )
    )
    # A fresh router instance — as if the orchestrator restarted — must
    # rediscover the binding by scanning sessions/*/inbox/binding.json.
    fresh = InboundRouter(FakeQueue(), sessions_dir=tmp_path)
    sid_after = asyncio.run(
        fresh.route(_event("after restart", ts=datetime(2026, 5, 1, 13, 0, 0, tzinfo=timezone.utc)))
    )
    assert sid_after == sid


def test_terminal_session_gets_a_fresh_one(tmp_path):
    queue = FakeQueue()
    router = InboundRouter(queue, sessions_dir=tmp_path)
    sid1 = asyncio.run(
        router.route(_event("old convo", ts=datetime(2026, 5, 1, 12, 0, 0, tzinfo=timezone.utc)))
    )

    # Drive the bound session to a terminal state.
    session = load_session(sid1, sessions_dir=tmp_path)
    session.update_state(state="executing")
    session.mark_complete({"final_answer": "done"})

    # Forward-only: a new message must NOT revive it.
    sid2 = asyncio.run(
        router.route(_event("new convo", ts=datetime(2026, 5, 1, 14, 0, 0, tzinfo=timezone.utc)))
    )
    assert sid2 != sid1


def test_reply_target_defaults_to_binding(tmp_path):
    router = InboundRouter(FakeQueue(), sessions_dir=tmp_path)
    sid = asyncio.run(router.route(_event("hi")))
    assert router.reply_target_for(sid) == ("cli", "cli-main", None)
    # An unknown session id has no reply target.
    assert router.reply_target_for("sess_does_not_exist") is None
