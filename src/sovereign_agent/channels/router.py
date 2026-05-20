"""InboundRouter: turn inbound channel events into sessions (v0.3, Module 1).

The router is the single piece that connects "a message arrived" to "a
session runs". It is owned by the orchestrator. Adapters call
`route(InboundEvent)` and the router:

  1. Finds or creates a session for (channel_type, platform_id, thread_id).
  2. Appends the event to that session's inbox (inbox/messages.jsonl).
  3. Enqueues the session with the SessionQueue at PLANNER priority.

## Files are the source of truth

The mapping from a channel conversation to a session is persisted as
`inbox/binding.json` *inside the session directory*. There is no global
index file. On a cold start the router scans `sessions/*/inbox/binding.json`
the first time it sees a binding it doesn't recognise; after that an
in-memory cache makes lookups O(1). `rm -rf sessions/sess_xxx/` removes the
binding along with the session — nothing else breaks. That invariant (you
can delete a session directory and nothing breaks) is the spine of the
whole framework, so the router must not undermine it with side state.

## Idempotency

A retrying adapter may deliver the same message twice. The router keeps a
set of recently-seen (channel_type, platform_id, thread_id, timestamp)
tuples; a duplicate is dropped before it can create a second session or
enqueue a second time.

## Forward-only state

If the session bound to a conversation has reached a terminal state
(completed/failed/escalated), the router does NOT try to revive it — the
forward-only rule forbids that. A new message starts a *fresh* session and
re-points the binding. The conversation continues; the session is new.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path

from sovereign_agent._internal.atomic import atomic_write_json
from sovereign_agent.channels.adapter import InboundEvent
from sovereign_agent.session.directory import (
    DEFAULT_SESSIONS_DIR,
    Session,
    create_session,
    load_session,
)

log = logging.getLogger(__name__)

# A binding key uniquely identifies a channel conversation.
BindingKey = tuple[str, str, str | None]  # (channel_type, platform_id, thread_id)


class InboundRouter:
    """Routes inbound channel events to sessions. Owned by the Orchestrator."""

    def __init__(self, queue: object, *, sessions_dir: Path | None = None) -> None:
        """`queue` is the orchestrator's SessionQueue (anything with an
        async `enqueue_planner(session_id)` method — tests pass a fake)."""
        self.queue = queue
        self.sessions_dir = sessions_dir or DEFAULT_SESSIONS_DIR
        # binding key -> session id, populated lazily.
        self._cache: dict[BindingKey, str] = {}
        # session id -> binding key, the inverse, for delivery lookups.
        self._bindings: dict[str, BindingKey] = {}
        # session id -> reply target, set when a message carries `reply_to`.
        self._reply_overrides: dict[str, BindingKey] = {}
        # dedup set of (channel_type, platform_id, thread_id, timestamp).
        self._seen: set[tuple[str, str, str | None, str]] = set()
        self._scanned = False

    async def route(
        self,
        event: InboundEvent,
        *,
        reply_to: BindingKey | None = None,
    ) -> str:
        """Route one inbound event. Returns the session id it was routed to.

        `reply_to`, when given, records where this session's reply should be
        delivered if that differs from the session's own channel binding —
        an admin/test affordance (see CliChannelAdapter's `reply_to` field).
        """
        key: BindingKey = (event.channel_type, event.platform_id, event.thread_id)
        dedup = (
            event.channel_type,
            event.platform_id,
            event.thread_id,
            event.timestamp.isoformat(),
        )
        if dedup in self._seen:
            log.debug("router: dropping duplicate event %s", dedup)
            return self._cache.get(key, "")
        self._seen.add(dedup)

        session = self._resolve_session(key)
        if session is None:
            session = self._create_bound_session(key)
        session_id = session.session_id

        if reply_to is not None:
            self._reply_overrides[session_id] = reply_to

        session.append_inbox_event(event.to_dict())
        await self.queue.enqueue_planner(session_id)  # type: ignore[attr-defined]
        return session_id

    # ------------------------------------------------------------------
    # Binding resolution
    # ------------------------------------------------------------------
    def _resolve_session(self, key: BindingKey) -> Session | None:
        """Find the live session bound to `key`, or None if a fresh one is
        needed. None covers three cases: never seen, binding points at a
        deleted session, or the bound session is already terminal."""
        sid = self._cache.get(key)
        if sid is None and not self._scanned:
            self._scan_bindings()
            sid = self._cache.get(key)
        if sid is None:
            return None
        try:
            session = load_session(sid, sessions_dir=self.sessions_dir)
        except Exception:  # noqa: BLE001
            # Binding cache points at a session that's gone — forget it.
            self._forget(key, sid)
            return None
        if session.state.is_terminal():
            # Forward-only: a finished conversation gets a fresh session.
            self._forget(key, sid)
            return None
        return session

    def _scan_bindings(self) -> None:
        """One-time scan of every session's inbox/binding.json. This is the
        'files are the source of truth' recovery path: after an orchestrator
        restart the in-memory cache is empty, and we rebuild it from disk."""
        self._scanned = True
        if not self.sessions_dir.exists():
            return
        for entry in self.sessions_dir.iterdir():
            if not entry.is_dir() or not entry.name.startswith("sess_"):
                continue
            binding_file = entry / "inbox" / "binding.json"
            if not binding_file.exists():
                continue
            try:
                with open(binding_file, encoding="utf-8") as f:
                    data = json.load(f)
                key: BindingKey = (
                    data["channel_type"],
                    data["platform_id"],
                    data.get("thread_id"),
                )
            except (OSError, json.JSONDecodeError, KeyError):
                continue
            self._cache[key] = entry.name
            self._bindings[entry.name] = key

    def _create_bound_session(self, key: BindingKey) -> Session:
        """Create a new session and write its binding file."""
        channel_type, platform_id, thread_id = key
        session = create_session(
            scenario=f"channel:{channel_type}",
            task="(conversation — recent messages are in inbox/messages.jsonl)",
            sessions_dir=self.sessions_dir,
        )
        binding = {
            "channel_type": channel_type,
            "platform_id": platform_id,
            "thread_id": thread_id,
        }
        # Binding lives inside the session directory: delete the directory
        # and the binding goes with it.
        atomic_write_json(session.inbox_path.parent / "binding.json", binding)
        self._cache[key] = session.session_id
        self._bindings[session.session_id] = key
        return session

    def _forget(self, key: BindingKey, session_id: str) -> None:
        self._cache.pop(key, None)
        self._bindings.pop(session_id, None)

    # ------------------------------------------------------------------
    # Delivery lookups (used by the orchestrator)
    # ------------------------------------------------------------------
    def binding_for(self, session_id: str) -> BindingKey | None:
        """The channel binding of a session, or None if it isn't channel-bound."""
        return self._bindings.get(session_id)

    def reply_target_for(self, session_id: str) -> BindingKey | None:
        """Where the orchestrator should deliver this session's reply.

        Returns the `reply_to` override if one was recorded (admin/test
        path), otherwise the session's own channel binding. None means the
        session did not arrive via a channel — there is nothing to deliver.
        """
        override = self._reply_overrides.get(session_id)
        if override is not None:
            return override
        return self._bindings.get(session_id)


__all__ = ["BindingKey", "InboundRouter"]
