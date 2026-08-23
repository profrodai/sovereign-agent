"""Opt-in, zero-token provider CLI capability probes.

Enable with ``SOVEREIGN_AGENT_LIVE_PROVIDER_PROBES=1``. These tests execute
only ``--version`` and ``--help``; they never submit a prompt or require a
credential. Credentialed provider invocations remain outside this suite.
"""

from __future__ import annotations

import os
import shutil

import pytest

from sovereign_agent.contracts import EvidenceLevel, ExecutionId, InvocationId
from sovereign_agent.providers import ClaudeCodeProvider, CodexCliProvider, InvocationRequest

pytestmark = pytest.mark.network


def _enabled() -> bool:
    return os.environ.get("SOVEREIGN_AGENT_LIVE_PROVIDER_PROBES") == "1"


@pytest.mark.parametrize(
    ("executable", "provider_type"),
    [
        ("codex", CodexCliProvider),
        ("claude", ClaudeCodeProvider),
    ],
)
@pytest.mark.asyncio
async def test_installed_provider_help_probe_is_truthful(
    executable: str, provider_type, fresh_session
) -> None:
    if not _enabled():
        pytest.skip("set SOVEREIGN_AGENT_LIVE_PROVIDER_PROBES=1 to run zero-token CLI probes")
    resolved = shutil.which(executable)
    if resolved is None:
        pytest.skip(f"{executable} is not installed")

    provider = provider_type(executable=resolved, environment={"PATH": os.environ.get("PATH", "")})
    request = InvocationRequest(
        execution_id=ExecutionId(f"exec-live-{executable}"),
        invocation_id=InvocationId(f"invoke-live-{executable}"),
        task="",
        session=fresh_session,
    )

    evidence = await provider.probe(request)

    assert evidence.executable == resolved
    assert evidence.version
    assert evidence.capabilities.available is True
    assert evidence.capabilities.evidence_level is EvidenceLevel.PROBED
