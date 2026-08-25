"""Opt-in live probes. Never submit prompts. Excluded from default pytest."""

from __future__ import annotations

import pytest

from sovereign_agent.providers import PROVIDERS

pytestmark = pytest.mark.live


@pytest.mark.parametrize("name", ["claude", "codex", "cursor"])
def test_installed_cli_probe_does_not_submit_work(name: str) -> None:
    provider = PROVIDERS[name]
    caps = provider.probe()
    if not caps.available:
        pytest.skip(f"{provider.executable} is not on PATH")
    assert caps.available
