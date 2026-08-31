"""Tests for the OpenAI-compatible (Ollama) provider.

The default suite never touches the network: the HTTP call is monkeypatched.
One `live` test actually hits a local endpoint and is deselected by default
(`addopts = -m 'not live'`).
"""

from __future__ import annotations

import json
import urllib.error

import pytest

from sovereign_agent.providers import PROVIDERS, get_provider
from sovereign_agent.providers import openai_compatible as oc
from sovereign_agent.providers.base import InvocationRequest


def test_registered_as_first_class_provider() -> None:
    assert "ollama" in PROVIDERS
    assert get_provider("ollama") is PROVIDERS["ollama"]


def test_probe_is_available_and_offline(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("SOVEREIGN_AGENT_LLM_BASE_URL", raising=False)
    monkeypatch.delenv("SOVEREIGN_AGENT_LLM_MODEL", raising=False)
    caps = oc.OpenAICompatibleProvider().probe()
    assert caps.available is True
    # Reports the resolved defaults, without any network call.
    assert oc.DEFAULT_MODEL in caps.version
    assert oc.DEFAULT_BASE_URL in caps.version


def test_resolve_config_defaults_and_alias(monkeypatch: pytest.MonkeyPatch) -> None:
    for name in oc.LLM_ENVIRONMENT:
        monkeypatch.delenv(name, raising=False)
    base, model, api_key = oc.resolve_config()
    assert (base, model, api_key) == (oc.DEFAULT_BASE_URL, oc.DEFAULT_MODEL, "")
    # EXECUTOR_MODEL is honored as a documented alias when MODEL is unset.
    monkeypatch.setenv("SOVEREIGN_AGENT_LLM_EXECUTOR_MODEL", "llama3.1")
    assert oc.resolve_config()[1] == "llama3.1"
    # MODEL wins over the alias.
    monkeypatch.setenv("SOVEREIGN_AGENT_LLM_MODEL", "qwen3.6:35b")
    assert oc.resolve_config()[1] == "qwen3.6:35b"


def test_build_invocation_forwards_only_documented_env(
    monkeypatch: pytest.MonkeyPatch, tmp_path
) -> None:
    monkeypatch.setenv("SOVEREIGN_AGENT_LLM_BASE_URL", "http://localhost:11434/v1")
    monkeypatch.setenv("SOVEREIGN_AGENT_LLM_MODEL", "qwen3")
    monkeypatch.setenv("SOVEREIGN_AGENT_LLM_API_KEY", "secret-token")
    monkeypatch.setenv("UNRELATED_SECRET", "must-not-leak")
    spec = oc.OpenAICompatibleProvider().build_invocation(
        InvocationRequest(workspace=tmp_path, output=tmp_path / "out", prompt="hi")
    )
    assert spec.argv[:3] == ["python", "-m", "sovereign_agent.providers.openai_compatible"]
    assert spec.env["SOVEREIGN_AGENT_LLM_MODEL"] == "qwen3"
    assert spec.env["SOVEREIGN_AGENT_LLM_API_KEY"] == "secret-token"
    assert "UNRELATED_SECRET" not in spec.env


def test_run_llm_report_parses_a_proposal(monkeypatch: pytest.MonkeyPatch, tmp_path) -> None:
    def fake_chat(base, model, api_key, messages, timeout):
        return json.dumps(
            {
                "status": "completed",
                "proposed_restock_units": 4,
                "proposed_checks": ["inventory_at_or_above_reorder_point"],
                "notes": "ok",
            }
        )

    monkeypatch.setattr(oc, "_chat", fake_chat)
    report = oc.run_llm_report(tmp_path, prompt="restock the vanilla")
    assert report.status == "completed"
    assert report.proposed_restock_units == 4
    written = json.loads((tmp_path / "report.json").read_text())
    assert written["proposed_restock_units"] == 4
    assert (tmp_path / "artifacts.json").exists()


def test_run_llm_report_tolerates_prose_around_json(
    monkeypatch: pytest.MonkeyPatch, tmp_path
) -> None:
    def fake_chat(base, model, api_key, messages, timeout):
        return (
            'Sure! Here is my proposal:\n{"status":"completed","proposed_restock_units":2}\nThanks.'
        )

    monkeypatch.setattr(oc, "_chat", fake_chat)
    report = oc.run_llm_report(tmp_path, prompt="{}")
    assert report.proposed_restock_units == 2


def test_run_llm_report_fails_honestly_when_unreachable(
    monkeypatch: pytest.MonkeyPatch, tmp_path
) -> None:
    def boom(base, model, api_key, messages, timeout):
        raise urllib.error.URLError("connection refused")

    monkeypatch.setattr(oc, "_chat", boom)
    report = oc.run_llm_report(tmp_path, prompt="{}")
    # An unreachable endpoint is an honest failure, never a fabricated success.
    assert report.status == "failed"
    assert report.proposed_restock_units is None
    assert "OpenAI-compatible endpoint" in report.notes and "failed" in report.notes


def test_run_llm_report_coerces_non_integer_units(
    monkeypatch: pytest.MonkeyPatch, tmp_path
) -> None:
    def fake_chat(base, model, api_key, messages, timeout):
        return json.dumps({"status": "completed", "proposed_restock_units": "not-a-number"})

    monkeypatch.setattr(oc, "_chat", fake_chat)
    report = oc.run_llm_report(tmp_path, prompt="{}")
    assert report.proposed_restock_units is None


@pytest.mark.live
def test_live_local_openai_compatible_endpoint(tmp_path) -> None:
    """Hits a real OpenAI-compatible endpoint (default local Ollama). Deselected
    by default; run with `-m live` and a reachable SOVEREIGN_AGENT_LLM_BASE_URL."""
    report = oc.run_llm_report(
        tmp_path,
        prompt=json.dumps(
            {"statement_of_work": {"scope": "Replenish vanilla to its reorder point."}}
        ),
    )
    assert report.status in {"completed", "blocked", "failed"}
