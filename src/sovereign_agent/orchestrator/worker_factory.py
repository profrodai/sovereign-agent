"""Worker backend factory (v0.3, Module 4a).

`make_worker_backend(config, *, advance_fn) -> WorkerBackend` chooses
the right backend based on `config.worker_backend`. Three values:

  - "bare"       : in-process, no isolation. v0.2 default behaviour.
  - "subprocess" : sandboxed via Landlock (Linux) or sandbox-exec (macOS).
                   Fails loud at construction time if the host has
                   neither primitive available.
  - "docker"     : unavailable placeholder; raises NotImplementedError
                   on use and is not advertised as a supported backend.

## Fail-loud philosophy

If an operator sets `worker_backend='subprocess'` on a platform without
a usable isolation primitive (Windows, pre-5.13 Linux, headless macOS
without sandbox-exec on PATH), `make_worker_backend()` raises
SovereignError(code="SA_SYS_NO_SANDBOX_PRIMITIVE") immediately. The agent
never starts. This is deliberate: an operator who asks for sandboxing
must GET sandboxing, never silent degradation to inline execution. The
README's eighth decision says prompts are advisory and registries are
physics; the same applies to security: an opted-in security boundary
must not become advisory at the discretion of the framework.

If you want graceful degradation, use detect_best_policy() and pick
'bare' explicitly when no policy is available. The factory will not
make that decision for you.

## The advance_fn parameter

BareWorker needs a function to call — the "raw step" of advancing one
session by one tick. The orchestrator binds this from its own
`advance_session_once` so config/llm/tools propagate correctly. The
factory takes it as a kwarg because BareWorker is the only backend
that needs it; SubprocessWorker and DockerWorker spawn fresh
interpreters that re-import everything.

## What this does NOT do

  - No global state. Each call constructs a fresh backend instance.
  - No caching. If you want one backend across many sessions, hold the
    return value yourself. The Orchestrator does exactly that.
  - No automatic policy selection for SubprocessWorker. The factory
    calls detect_best_policy() and uses whatever it returns. If you
    need a specific policy (e.g. force LandlockPolicy() in tests),
    construct SubprocessWorker yourself.
"""

from __future__ import annotations

import logging
import sys
from collections.abc import Awaitable, Callable
from pathlib import Path

from sovereign_agent._internal.isolation import detect_best_policy
from sovereign_agent.config import Config
from sovereign_agent.errors import SystemError, ValidationError
from sovereign_agent.orchestrator.worker import (
    BareWorker,
    DockerWorker,
    SubprocessWorker,
    WorkerBackend,
    WorkerOutcome,
)

log = logging.getLogger(__name__)


# Type alias for the advance function BareWorker needs.
AdvanceFn = Callable[[str, Path], Awaitable[WorkerOutcome]]


def make_worker_backend(
    config: Config,
    *,
    advance_fn: AdvanceFn | None = None,
) -> WorkerBackend:
    """Build the right WorkerBackend for `config.worker_backend`.

    Parameters
    ----------
    config:
        The Config whose `worker_backend` field selects the backend.
    advance_fn:
        Required when worker_backend='bare'. The async function
        BareWorker calls to advance a session by one step.
        SubprocessWorker and DockerWorker don't use it (they spawn
        fresh interpreters).

    Raises
    ------
    SovereignError(code="SA_SYS_NO_SANDBOX_PRIMITIVE")
        When worker_backend='subprocess' but no kernel-level isolation
        primitive is available. Fail-loud security boundary.
    ValidationError(code="SA_VAL_BAD_TYPE")
        When worker_backend is not one of "bare", "subprocess", "docker",
        or when worker_backend='bare' but advance_fn was not provided.
    """
    name = config.worker_backend

    if name == "bare":
        if advance_fn is None:
            raise ValidationError(
                code="SA_VAL_BAD_TYPE",
                message=(
                    "worker_backend='bare' requires advance_fn — the "
                    "orchestrator binds this from its own advance_session_once. "
                    "If you're calling make_worker_backend() directly, pass an "
                    "async (session_id, session_dir) -> WorkerOutcome callable."
                ),
            )
        return BareWorker(advance_fn=advance_fn)

    if name == "subprocess":
        policy = detect_best_policy()
        if policy.name == "noop":
            raise SystemError(
                code="SA_SYS_NO_SANDBOX_PRIMITIVE",
                message=(
                    f"worker_backend='subprocess' requires Landlock (Linux >=5.13) "
                    f"or sandbox-exec (macOS). Your platform ({sys.platform}) "
                    f"offers neither. Use worker_backend='bare' for unsandboxed "
                    f"in-process execution, or run on a supported platform."
                ),
                context={"platform": sys.platform, "policy": policy.name},
            )
        log.info("worker backend: subprocess with policy %r", policy.name)
        return SubprocessWorker(isolation_policy=policy)

    if name == "docker":
        return DockerWorker()

    raise ValidationError(
        code="SA_VAL_BAD_TYPE",
        message=(
            f"unknown worker_backend {name!r}; expected one of: 'bare', 'subprocess', 'docker'"
        ),
        context={"got": name},
    )


__all__ = ["AdvanceFn", "make_worker_backend"]
