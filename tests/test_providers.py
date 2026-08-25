from __future__ import annotations

from pathlib import Path

import pytest

from sovereign_agent.errors import Refusal
from sovereign_agent.providers import PROVIDERS, get_provider
from sovereign_agent.providers.base import InvocationRequest, ProviderCapabilities
from sovereign_agent.providers.claude import ClaudeProvider
from sovereign_agent.providers.codex import CodexProvider
from sovereign_agent.providers.cursor import CursorProvider

FIXTURES = Path(__file__).resolve().parent / "fixtures" / "providers"


def _request(tmp_path: Path) -> InvocationRequest:
    return InvocationRequest(
        workspace=tmp_path,
        output=tmp_path / "out",
        prompt="replenish tea",
    )


def test_registry_names_are_equal_adapters() -> None:
    assert list(PROVIDERS) == ["scripted", "claude", "codex", "cursor"]
    with pytest.raises(Refusal, match="Unknown provider"):
        get_provider("sonnet")


def test_offline_fixtures_parse_without_executables() -> None:
    claude_lines = (FIXTURES / "claude.stream-json.jsonl").read_text().splitlines()
    codex_lines = (FIXTURES / "codex.exec-json.jsonl").read_text().splitlines()
    cursor_lines = (FIXTURES / "cursor.stream-json.jsonl").read_text().splitlines()
    claude = [ClaudeProvider().parse_event(line) for line in claude_lines]
    codex = [CodexProvider().parse_event(line) for line in codex_lines]
    cursor = [CursorProvider().parse_event(line) for line in cursor_lines]
    assert claude[0] is not None and claude[0].kind == "system"
    assert cursor[1] is not None and cursor[1].kind == "assistant"
    assert codex[2] is not None and codex[2].kind == "raw"
    assert codex[3] is not None and codex[3].kind == "usage"


def test_chapter_imports_production_registry() -> None:
    import importlib.util

    path = Path(__file__).resolve().parent.parent / "book/ch03_actor_is_not_a_model/solution.py"
    spec = importlib.util.spec_from_file_location("ch03_solution", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    assert module.PROVIDERS is PROVIDERS


def test_missing_executable_is_unavailable(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("sovereign_agent.providers.claude.look_up", lambda _: None)
    assert ClaudeProvider().probe().available is False


def test_unproven_streaming_is_refused(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    provider = CursorProvider()
    monkeypatch.setattr(
        provider,
        "probe",
        lambda: ProviderCapabilities(available=True, streaming=False, resume=True),
    )
    with pytest.raises(Refusal, match="streaming"):
        provider.build_invocation(_request(tmp_path))


def test_unproven_resume_is_refused(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    provider = ClaudeProvider()
    monkeypatch.setattr(
        provider,
        "probe",
        lambda: ProviderCapabilities(available=True, streaming=True, resume=False),
    )
    request = InvocationRequest(
        workspace=tmp_path,
        output=tmp_path / "out",
        prompt="hi",
        require_resume=True,
        provider_session_id="ses_1",
    )
    with pytest.raises(Refusal, match="resume"):
        provider.build_invocation(request)


def test_proven_flags_are_the_only_ones_on_argv(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    claude = ClaudeProvider()
    monkeypatch.setattr(
        claude,
        "probe",
        lambda: ProviderCapabilities(available=True, streaming=True, resume=True),
    )
    spec = claude.build_invocation(_request(tmp_path))
    assert spec.argv[:4] == ["claude", "-p", "--output-format", "stream-json"]
    assert "--verbose" in spec.argv

    cursor = CursorProvider()
    monkeypatch.setattr(
        cursor,
        "probe",
        lambda: ProviderCapabilities(available=True, streaming=True, sandbox=True),
    )
    spec = cursor.build_invocation(_request(tmp_path))
    assert spec.argv[:6] == [
        "agent",
        "-p",
        "--output-format",
        "stream-json",
        "--workspace",
        str(tmp_path),
    ]

    codex = CodexProvider()
    monkeypatch.setattr(
        codex,
        "probe",
        lambda: ProviderCapabilities(available=True, streaming=True, sandbox=True),
    )
    spec = codex.build_invocation(_request(tmp_path))
    assert spec.argv[:3] == ["codex", "exec", "--json"]
    assert spec.argv[3:5] == ["--sandbox", "workspace-write"]
