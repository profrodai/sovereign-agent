"""v0.3 Module 4a — Orchestrator routes through WorkerBackend.

Verifies that:

  1. Orchestrator(Config()) constructs a BareWorker by default —
     preserves v0.2 behaviour bit-identical.
  2. The Orchestrator's _worker_backend attribute is populated from
     the factory, not None.
  3. Per-session override: a session with config_overrides={'worker_backend': 'bare'}
     uses a fresh BareWorker for that session, even if config.worker_backend differs.
  4. Per-session override: Session.worker_backend property reads config_overrides.
  5. Subprocess fail-loud at __init__ time when no policy available.
  6. process_session routes through the worker backend, not direct dispatch.

stdlib only; sync funcs driving asyncio via asyncio.run().
"""

from __future__ import annotations

import asyncio
from pathlib import Path
from unittest.mock import patch

import pytest

from sovereign_agent.config import Config
from sovereign_agent.errors import SovereignError
from sovereign_agent.orchestrator import Orchestrator
from sovereign_agent.orchestrator.worker import BareWorker, WorkerOutcome
from sovereign_agent.session.directory import create_session, load_session


def test_orchestrator_defaults_to_bare_worker(tmp_path):
    """v0.2 behaviour preservation: Config() with no worker_backend kwarg
    yields a BareWorker. No isolation, no surprises."""
    cfg = Config(sessions_dir=tmp_path / "sessions")
    orch = Orchestrator(cfg)
    assert isinstance(orch._worker_backend, BareWorker)
    assert orch._worker_backend.name == "bare"


def test_orchestrator_subprocess_backend_constructs_when_policy_available(tmp_path):
    """When detect_best_policy returns a real policy, the Orchestrator
    builds a SubprocessWorker. Patch the detector so this runs on any host."""
    from sovereign_agent.orchestrator.worker import SubprocessWorker

    class FakePolicy:
        name = "fake-policy"

    cfg = Config(sessions_dir=tmp_path / "sessions", worker_backend="subprocess")
    with patch(
        "sovereign_agent.orchestrator.worker_factory.detect_best_policy",
        return_value=FakePolicy(),
    ):
        orch = Orchestrator(cfg)
    assert isinstance(orch._worker_backend, SubprocessWorker)


def test_orchestrator_subprocess_fails_loud_at_init_on_unsupported_platform(tmp_path):
    """SA_NO_SANDBOX_PRIMITIVE must be raised at Orchestrator() construction
    time, not later when a session would silently run unconfined."""

    class NoOpStub:
        name = "noop"

    cfg = Config(sessions_dir=tmp_path / "sessions", worker_backend="subprocess")
    with patch(
        "sovereign_agent.orchestrator.worker_factory.detect_best_policy",
        return_value=NoOpStub(),
    ):
        with pytest.raises(SovereignError) as exc:
            Orchestrator(cfg)
    assert exc.value.code == "SA_SYS_NO_SANDBOX_PRIMITIVE"


def test_session_worker_backend_property_reads_config_overrides(tmp_path):
    """The per-session override lives under config_overrides on the
    session state — a forward-compatible vehicle for any future
    per-session config knob."""
    sessions_dir = tmp_path / "sessions"
    sessions_dir.mkdir()
    session = create_session(
        scenario="default",
        task="t",
        sessions_dir=sessions_dir,
        config_overrides={"worker_backend": "subprocess"},
    )
    assert session.worker_backend == "subprocess"

    # Reloaded from disk: same answer.
    reloaded = load_session(session.session_id, sessions_dir=sessions_dir)
    assert reloaded.worker_backend == "subprocess"


def test_session_worker_backend_property_returns_none_when_unset(tmp_path):
    """Sessions created without an override report None (orchestrator
    will inherit from config.worker_backend)."""
    sessions_dir = tmp_path / "sessions"
    sessions_dir.mkdir()
    session = create_session(scenario="default", task="t", sessions_dir=sessions_dir)
    assert session.worker_backend is None


def test_per_session_override_uses_overriden_backend(tmp_path):
    """When session.worker_backend differs from config.worker_backend,
    the orchestrator builds a fresh backend for that session — the
    files-as-source-of-truth principle applied to backend selection."""
    sessions_dir = tmp_path / "sessions"
    sessions_dir.mkdir()
    cfg = Config(sessions_dir=sessions_dir, worker_backend="bare")
    orch = Orchestrator(cfg)

    # Session has no override — _backend_for_session returns the shared backend.
    session_default = create_session(scenario="default", task="t", sessions_dir=sessions_dir)
    backend_default = orch._backend_for_session(session_default)
    assert backend_default is orch._worker_backend  # same instance

    # Session has override (also 'bare', so still bare class — the
    # override is logically a no-op here but still goes through factory).
    session_override = create_session(
        scenario="default",
        task="t",
        sessions_dir=sessions_dir,
        config_overrides={"worker_backend": "bare"},
    )
    backend_override = orch._backend_for_session(session_override)
    # Same NAMED backend, but the orchestrator's _backend_for_session
    # short-circuits when the override matches config — returns the shared.
    assert backend_override is orch._worker_backend


def test_per_session_override_to_different_backend_builds_fresh(tmp_path):
    """When override DIFFERS from config, a fresh backend is built."""
    sessions_dir = tmp_path / "sessions"
    sessions_dir.mkdir()
    cfg = Config(sessions_dir=sessions_dir, worker_backend="bare")
    orch = Orchestrator(cfg)

    # Override to docker — different from bare, so factory builds a DockerWorker.
    session = create_session(
        scenario="default",
        task="t",
        sessions_dir=sessions_dir,
        config_overrides={"worker_backend": "docker"},
    )
    backend = orch._backend_for_session(session)
    assert backend is not orch._worker_backend
    assert backend.name == "docker"


def test_process_session_calls_worker_backend_not_direct_dispatch(tmp_path):
    """The wiring change M4a delivers: process_session goes through
    backend.run_session, not direct _dispatch_loop_half. We verify by
    replacing the orchestrator's backend with a recording stub."""
    sessions_dir = tmp_path / "sessions"
    sessions_dir.mkdir()
    cfg = Config(sessions_dir=sessions_dir)
    orch = Orchestrator(cfg)

    # Create a real session.
    session = create_session(scenario="default", task="t", sessions_dir=sessions_dir)

    # Replace the orchestrator's backend with a recording stub.
    calls = []

    class RecordingBackend:
        name = "recording"

        async def run_session(self, session_id, session_dir, *, timeout_s=None):
            calls.append((session_id, session_dir, timeout_s))
            return WorkerOutcome(
                session_id=session_id,
                terminal=True,
                advanced=True,
                summary="recorded",
            )

        async def close(self):
            pass

    orch._worker_backend = RecordingBackend()  # type: ignore[assignment]

    async def _call():
        return await orch.process_session(session.session_id)

    asyncio.run(_call())

    assert len(calls) == 1
    assert calls[0][0] == session.session_id
    assert Path(calls[0][1]).name == session.session_id  # session_dir matches
