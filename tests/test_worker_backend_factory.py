"""v0.3 Module 4a — worker_factory.make_worker_backend tests.

Eight tests covering:
  - bare backend selection (with advance_fn) returns BareWorker
  - bare backend without advance_fn raises ValidationError
  - subprocess backend on a host with a real policy returns SubprocessWorker
  - subprocess backend with no policy raises SovereignError fail-loud
  - docker backend returns DockerWorker stub
  - unknown backend name raises ValidationError
  - DockerWorker satisfies the WorkerBackend Protocol
  - DockerWorker.run_session raises NotImplementedError

stdlib only.
"""

from __future__ import annotations

from unittest.mock import patch

import pytest

from sovereign_agent.config import Config
from sovereign_agent.errors import SovereignError, ValidationError
from sovereign_agent.orchestrator.worker import (
    BareWorker,
    DockerWorker,
    SubprocessWorker,
    WorkerBackend,
)
from sovereign_agent.orchestrator.worker_factory import make_worker_backend


async def _noop_advance(session_id, session_dir):
    """A placeholder advance_fn for BareWorker construction tests."""
    return None  # type: ignore[return-value]


def test_bare_backend_with_advance_fn_returns_bare_worker():
    cfg = Config(worker_backend="bare")
    backend = make_worker_backend(cfg, advance_fn=_noop_advance)
    assert isinstance(backend, BareWorker)
    assert backend.name == "bare"


def test_bare_backend_without_advance_fn_raises():
    cfg = Config(worker_backend="bare")
    with pytest.raises(ValidationError) as exc:
        make_worker_backend(cfg, advance_fn=None)
    assert exc.value.code == "SA_VAL_BAD_TYPE"
    assert "requires advance_fn" in exc.value.message


def test_subprocess_backend_on_supported_platform_returns_subprocess_worker():
    """When detect_best_policy returns a real policy, factory returns
    SubprocessWorker. We patch the policy detection so this test runs
    on any host (including CI runners without sandboxing primitives)."""

    class FakePolicy:
        name = "fake-policy"

    cfg = Config(worker_backend="subprocess")
    with patch(
        "sovereign_agent.orchestrator.worker_factory.detect_best_policy",
        return_value=FakePolicy(),
    ):
        backend = make_worker_backend(cfg)
    assert isinstance(backend, SubprocessWorker)
    assert backend.name == "subprocess"


def test_subprocess_backend_on_unsupported_platform_raises_sovereign_error():
    """The fail-loud security boundary: operators who ask for sandboxing
    must get sandboxing, not silent degradation."""

    class NoOpStub:
        name = "noop"

    cfg = Config(worker_backend="subprocess")
    with patch(
        "sovereign_agent.orchestrator.worker_factory.detect_best_policy",
        return_value=NoOpStub(),
    ):
        with pytest.raises(SovereignError) as exc:
            make_worker_backend(cfg)
    assert exc.value.code == "SA_SYS_NO_SANDBOX_PRIMITIVE"
    assert "subprocess" in exc.value.message
    assert "Landlock" in exc.value.message or "sandbox-exec" in exc.value.message


def test_docker_backend_returns_docker_worker_stub():
    cfg = Config(worker_backend="docker")
    backend = make_worker_backend(cfg)
    assert isinstance(backend, DockerWorker)
    assert backend.name == "docker"


def test_unknown_backend_name_raises_validation_error():
    cfg = Config()
    cfg.worker_backend = "kubernetes"  # type: ignore[assignment]
    with pytest.raises(ValidationError) as exc:
        make_worker_backend(cfg, advance_fn=_noop_advance)
    assert exc.value.code == "SA_VAL_BAD_TYPE"
    assert "unknown worker_backend" in exc.value.message


def test_docker_worker_satisfies_worker_backend_protocol():
    """DockerWorker is a stub but must structurally satisfy the protocol —
    operators selecting worker_backend='docker' get the right shape."""
    backend = DockerWorker()
    assert isinstance(backend, WorkerBackend)
    assert backend.name == "docker"


def test_docker_worker_run_session_raises_not_implemented():
    """Calling DockerWorker.run_session must fail explicitly with a
    message pointing the operator at SubprocessWorker."""
    import asyncio
    from pathlib import Path

    backend = DockerWorker()

    async def _call():
        return await backend.run_session("sess_x", Path("/tmp/sess_x"))

    with pytest.raises(NotImplementedError) as exc:
        asyncio.run(_call())
    assert "v0.4" in str(exc.value) or "subprocess" in str(exc.value).lower()
