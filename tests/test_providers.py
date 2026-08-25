from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from sovereign_agent.errors import Refusal
from sovereign_agent.providers import PROVIDERS, get_provider
from sovereign_agent.providers.base import (
    InvocationRequest,
    ProbeEvidence,
    ProviderCapabilities,
    capture,
)
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


def _caps(**changes: bool) -> ProviderCapabilities:
    values = {
        "available": True,
        "print_mode": True,
        "streaming": True,
        "resume": True,
        "verbose": True,
    }
    values.update(changes)
    return ProviderCapabilities(**values)


def test_registry_names_are_equal_adapters() -> None:
    assert list(PROVIDERS) == ["scripted", "claude", "codex", "cursor"]
    with pytest.raises(Refusal, match="Unknown provider"):
        get_provider("sonnet")


def test_offline_success_fixtures_capture_terminal_session_and_usage() -> None:
    claude_lines = (FIXTURES / "claude.stream-json.jsonl").read_text().splitlines()
    codex_lines = (FIXTURES / "codex.exec-json.jsonl").read_text().splitlines()
    cursor_lines = (FIXTURES / "cursor.stream-json.jsonl").read_text().splitlines()
    claude = [ClaudeProvider().parse_event(line) for line in claude_lines]
    codex = [CodexProvider().parse_event(line) for line in codex_lines]
    cursor = [CursorProvider().parse_event(line) for line in cursor_lines]
    assert claude[0] is not None and claude[0].session_id == "ses_offline"
    assert claude[-1] is not None and claude[-1].terminal and claude[-1].succeeded
    assert cursor[0] is not None and cursor[0].session_id == "cursor_offline"
    assert cursor[-1] is not None and cursor[-1].terminal and cursor[-1].succeeded
    assert codex[0] is not None and codex[0].session_id == "thread_offline"
    assert codex[-1] is not None and codex[-1].terminal and codex[-1].succeeded
    assert codex[-1].usage["input_tokens"] == 12


def test_malformed_and_unknown_events_are_distinct() -> None:
    malformed = CodexProvider().parse_event("not json")
    unknown = CodexProvider().parse_event('{"type":"future.event","value":1}')
    assert malformed is not None and malformed.malformed
    assert malformed.kind == "malformed"
    assert unknown is not None and not unknown.malformed
    assert unknown.kind == "future.event"


def test_chapter_exercise_preserves_actor_identity(tmp_path: Path) -> None:
    import importlib.util

    path = Path(__file__).resolve().parent.parent / "book/ch03_actor_is_not_a_model/solution.py"
    spec = importlib.util.spec_from_file_location("ch03_solution", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    result = module.run_exercise(tmp_path / "chapter", "scripted")
    assert result["identity_unchanged"] is True
    assert result["before"] == result["after"]


def test_missing_executable_is_unavailable(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("sovereign_agent.providers.claude.look_up", lambda _: None)
    assert ClaudeProvider().probe().available is False


def test_unproven_streaming_is_refused(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    provider = CursorProvider()
    monkeypatch.setattr(
        provider,
        "probe",
        lambda: _caps(streaming=False),
    )
    with pytest.raises(Refusal, match="streaming"):
        provider.build_invocation(_request(tmp_path))


def test_unproven_resume_is_refused(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    provider = ClaudeProvider()
    monkeypatch.setattr(
        provider,
        "probe",
        lambda: _caps(resume=False),
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


def test_session_id_without_resume_intent_is_refused(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    provider = ClaudeProvider()
    monkeypatch.setattr(provider, "probe", _caps)
    request = InvocationRequest(
        workspace=tmp_path,
        output=tmp_path / "out",
        prompt="hi",
        provider_session_id="ses_1",
    )
    with pytest.raises(Refusal, match="without resume intent"):
        provider.build_invocation(request)


def test_proven_flags_are_the_only_ones_on_argv(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    claude = ClaudeProvider()
    monkeypatch.setattr(
        claude,
        "probe",
        _caps,
    )
    spec = claude.build_invocation(_request(tmp_path))
    assert spec.argv[:4] == ["claude", "-p", "--output-format", "stream-json"]
    assert "--verbose" in spec.argv

    cursor = CursorProvider()
    monkeypatch.setattr(
        cursor,
        "probe",
        _caps,
    )
    spec = cursor.build_invocation(_request(tmp_path))
    assert spec.argv == ["agent", "-p", "--output-format", "stream-json", "replenish tea"]
    assert spec.cwd == tmp_path
    assert cursor.probe().sandbox is False

    codex = CodexProvider()
    monkeypatch.setattr(
        codex,
        "probe",
        lambda: _caps(sandbox=True),
    )
    spec = codex.build_invocation(_request(tmp_path))
    assert spec.argv == ["codex", "exec", "--json", "replenish tea"]


def test_cursor_workspace_flag_requires_exact_probe(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    provider = CursorProvider()
    monkeypatch.setattr(provider, "probe", lambda: _caps(workspace_selection=True))
    spec = provider.build_invocation(_request(tmp_path))
    assert spec.argv[-3:-1] == ["--workspace", str(tmp_path)]
    assert spec.cwd == tmp_path


def test_requested_sandbox_must_be_proven(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    provider = CodexProvider()
    request = InvocationRequest(
        workspace=tmp_path,
        output=tmp_path / "out",
        prompt="bounded write",
        require_sandbox=True,
    )
    monkeypatch.setattr(provider, "probe", lambda: _caps(sandbox=False))
    with pytest.raises(Refusal, match="sandbox"):
        provider.build_invocation(request)
    monkeypatch.setattr(provider, "probe", lambda: _caps(sandbox=True))
    assert provider.build_invocation(request).argv == [
        "codex",
        "exec",
        "--json",
        "--sandbox",
        "workspace-write",
        "bounded write",
    ]


def test_codex_resume_has_subcommand_shape(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    provider = CodexProvider()
    monkeypatch.setattr(provider, "probe", _caps)
    request = InvocationRequest(
        workspace=tmp_path,
        output=tmp_path / "out",
        prompt="continue",
        require_resume=True,
        provider_session_id="thread_123",
    )
    assert provider.build_invocation(request).argv == [
        "codex",
        "exec",
        "resume",
        "--json",
        "thread_123",
        "continue",
    ]


def test_codex_probes_resume_subcommand_exactly(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[tuple[str, ...]] = []
    monkeypatch.setattr("sovereign_agent.providers.codex.look_up", lambda _: "/fake/codex")

    def fake_capture(executable: str, *args: str) -> ProbeEvidence:
        command = (executable, *args)
        calls.append(command)
        stdout = {
            ("--version",): "codex 1.0",
            ("exec", "--help"): "--json --sandbox",
            ("exec", "resume", "--help"): "Usage: codex exec resume --json",
        }[args]
        return ProbeEvidence(command=command, exit_code=0, stdout=stdout)

    monkeypatch.setattr("sovereign_agent.providers.codex.capture", fake_capture)
    caps = CodexProvider().probe()
    assert calls[-1] == ("codex", "exec", "resume", "--help")
    assert caps.resume
    assert caps.evidence[-1].command == calls[-1]


def test_probe_timeout_is_degraded_not_an_exception(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr("sovereign_agent.providers.base.look_up", lambda _: "/fake/claude")

    def timeout(*args: object, **kwargs: object) -> subprocess.CompletedProcess[str]:
        raise subprocess.TimeoutExpired(["claude", "--help"], 10)

    monkeypatch.setattr(subprocess, "run", timeout)
    evidence = capture("claude", "--help")
    assert evidence.exit_code is None
    assert evidence.error is not None
