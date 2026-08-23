from __future__ import annotations

from pathlib import Path

import pytest

from sovereign_agent.config import Config
from sovereign_agent.contracts import (
    EvidenceLevel,
    ExecutionId,
    FrozenDict,
    InvocationId,
    ProviderSessionId,
    RuntimeCapabilityManifest,
)
from sovereign_agent.orchestrator.lifecycle import (
    CloseResult,
    ExecResult,
    InvocationSpec,
    RuntimeHandle,
    WorkerRequest,
)
from sovereign_agent.providers import (
    AgentProvider,
    ClaudeCodeProvider,
    CodexCliProvider,
    InvocationRequest,
    ProviderUnavailable,
)

FIXTURES = Path(__file__).parents[1] / "fixtures" / "providers"


class FakeBackend:
    name = "fake-process"

    def __init__(
        self,
        *,
        help_stdout: str,
        invocation_stdout: str = "",
        invocation_stderr: str = "",
        invocation_returncode: int = 0,
        version_returncode: int = 0,
    ) -> None:
        self.help_stdout = help_stdout
        self.invocation_stdout = invocation_stdout
        self.invocation_stderr = invocation_stderr
        self.invocation_returncode = invocation_returncode
        self.version_returncode = version_returncode
        self.specs: list[InvocationSpec] = []

    def capabilities(self) -> RuntimeCapabilityManifest:
        return RuntimeCapabilityManifest(capabilities=FrozenDict())

    async def prepare(self, request: WorkerRequest) -> RuntimeHandle:
        return RuntimeHandle(request=request, invocation=InvocationSpec())

    async def execute(
        self, handle: RuntimeHandle, invocation: InvocationSpec | None = None
    ) -> ExecResult:
        assert invocation is not None
        self.specs.append(invocation)
        command = invocation.command
        if "--version" in command:
            return ExecResult(
                returncode=self.version_returncode,
                stdout="provider 1.2.3\n" if self.version_returncode == 0 else "",
                stderr="not found" if self.version_returncode else "",
                started=self.version_returncode == 0,
            )
        if "--help" in command:
            return ExecResult(returncode=0, stdout=self.help_stdout)
        return ExecResult(
            returncode=self.invocation_returncode,
            stdout=self.invocation_stdout,
            stderr=self.invocation_stderr,
        )

    async def close(self, handle: RuntimeHandle, preserve: bool = False) -> CloseResult:
        handle.closed = True
        return CloseResult(closed=True, preserved=preserve)


def request(
    fresh_session,
    *,
    provider_session_id: str | None = None,
    fork_provider_session: bool = False,
    context: FrozenDict | None = None,
) -> InvocationRequest:
    return InvocationRequest(
        execution_id=ExecutionId("exec-cli-1"),
        invocation_id=InvocationId("invoke-cli-1"),
        task="fix the tests",
        session=fresh_session,
        context=context or FrozenDict(),
        provider_session_id=(
            ProviderSessionId(provider_session_id) if provider_session_id is not None else None
        ),
        fork_provider_session=fork_provider_session,
    )


def fixture(name: str) -> str:
    return (FIXTURES / name).read_text(encoding="utf-8")


def test_codex_command_construction_distinguishes_fresh_and_resume(fresh_session) -> None:
    provider = CodexCliProvider(
        executable="/opt/codex",
        backend=FakeBackend(help_stdout=""),
        environment={"PATH": "/bin"},
    )
    fresh = provider.invocation_spec(request(fresh_session))
    resumed = provider.invocation_spec(
        request(fresh_session, provider_session_id="codex-session-1")
    )
    assert fresh.command == (
        "/opt/codex",
        "exec",
        "--json",
        "--skip-git-repo-check",
        "fix the tests",
    )
    assert resumed.command == (
        "/opt/codex",
        "exec",
        "resume",
        "--json",
        "codex-session-1",
        "fix the tests",
    )
    assert fresh.environment == {"PATH": "/bin"}
    assert fresh.cwd == fresh_session.directory


def test_cli_provider_uses_admitted_repository_worktree(fresh_session, tmp_path: Path) -> None:
    worktree = tmp_path / "worktree"
    worktree.mkdir()
    context = FrozenDict((("repository_worktree", str(worktree.resolve())),))
    codex = CodexCliProvider(backend=FakeBackend(help_stdout=""))
    claude = ClaudeCodeProvider(backend=FakeBackend(help_stdout=""))

    assert codex.invocation_spec(request(fresh_session, context=context)).cwd == worktree
    assert claude.invocation_spec(request(fresh_session, context=context)).cwd == worktree


def test_claude_command_construction_distinguishes_fresh_and_resume(fresh_session) -> None:
    provider = ClaudeCodeProvider(
        executable="/opt/claude",
        backend=FakeBackend(help_stdout=""),
        environment={"HOME": "/home/test"},
    )
    fresh = provider.invocation_spec(request(fresh_session))
    resumed = provider.invocation_spec(
        request(fresh_session, provider_session_id="claude-session-1")
    )
    assert fresh.command[-1] == "fix the tests"
    assert "--resume" not in fresh.command
    assert resumed.command[-3:] == (
        "--resume",
        "claude-session-1",
        "fix the tests",
    )
    assert resumed.environment == {"HOME": "/home/test"}


def test_claude_fork_resumes_parent_without_mutating_request(fresh_session) -> None:
    provider = ClaudeCodeProvider(
        executable="/opt/claude",
        backend=FakeBackend(help_stdout=""),
    )
    parent = ProviderSessionId("claude-parent-1")
    fork_request = request(
        fresh_session,
        provider_session_id=str(parent),
        fork_provider_session=True,
    )

    spec = provider.invocation_spec(fork_request)

    assert spec.command[-4:] == (
        "--resume",
        str(parent),
        "--fork-session",
        "fix the tests",
    )
    assert fork_request.provider_session_id == parent
    assert fork_request.fork_provider_session is True


def test_codex_fixture_parses_ordered_evidence(fresh_session) -> None:
    provider = CodexCliProvider(backend=FakeBackend(help_stdout=""))
    events = provider.parse_output(fixture("codex_success.jsonl"), request(fresh_session))
    assert [event.sequence for event in events] == list(range(len(events)))
    assert [event.event_type for event in events] == [
        "provider_session",
        "raw",
        "tool_call",
        "tool_result",
        "text",
        "usage",
    ]
    assert events[-1].to_dict()["total_tokens"] == 18


def test_codex_schema_constrained_answer_emits_structured_result(fresh_session) -> None:
    provider = CodexCliProvider(backend=FakeBackend(help_stdout=""))
    stdout = (
        '{"type":"item.completed","item":{"type":"agent_message",'
        '"text":"{\\"answer\\":\\"done\\"}"}}\n'
    )
    events = provider.parse_output(
        stdout,
        request(
            fresh_session,
            context=FrozenDict((("require_structured_result", True),)),
        ),
    )
    assert [event.event_type for event in events] == ["text", "structured_result"]
    assert events[-1].to_dict()["result"] == {"answer": "done"}


def test_claude_fixture_parses_all_normalized_forms(fresh_session) -> None:
    provider = ClaudeCodeProvider(backend=FakeBackend(help_stdout=""))
    events = provider.parse_output(fixture("claude_success.jsonl"), request(fresh_session))
    assert [event.sequence for event in events] == list(range(len(events)))
    assert [event.event_type for event in events] == [
        "provider_session",
        "text",
        "tool_call",
        "tool_result",
        "text",
        "structured_result",
        "usage",
    ]


def test_claude_single_json_result_preserves_text_and_evidence(fresh_session) -> None:
    provider = ClaudeCodeProvider(backend=FakeBackend(help_stdout=""))
    events = provider.parse_output(fixture("claude_result.json"), request(fresh_session))
    assert [event.event_type for event in events] == [
        "provider_session",
        "text",
        "usage",
    ]
    assert events[1].to_dict()["text"] == "Claude JSON answer"


@pytest.mark.parametrize(
    ("provider_type", "fixture_name", "warning_count"),
    [
        (CodexCliProvider, "codex_malformed.jsonl", 2),
        (ClaudeCodeProvider, "claude_truncated.jsonl", 1),
    ],
)
def test_malformed_and_truncated_lines_become_explicit_warnings(
    fresh_session, provider_type, fixture_name: str, warning_count: int
) -> None:
    provider = provider_type(backend=FakeBackend(help_stdout=""))
    events = provider.parse_output(fixture(fixture_name), request(fresh_session))
    warnings = [event for event in events if event.event_type == "warning"]
    assert len(warnings) == warning_count
    assert all(event.to_dict()["code"] == "malformed_provider_line" for event in warnings)
    assert [event.sequence for event in events] == list(range(len(events)))


@pytest.mark.asyncio
async def test_probe_publishes_evidence_and_invocation_uses_backend(fresh_session) -> None:
    backend = FakeBackend(help_stdout="Usage: codex exec [--json] [--output-schema FILE] resume")
    provider = CodexCliProvider(backend=backend)
    evidence = await provider.probe(request(fresh_session))
    assert evidence.version == "provider 1.2.3"
    assert evidence.capabilities.evidence_level is EvidenceLevel.PROBED
    assert evidence.capabilities.resume is True
    assert evidence.capabilities.structured_result is True
    assert backend.specs[:2][0].command == ("codex", "--version")
    assert backend.specs[:2][1].command == ("codex", "exec", "--help")


@pytest.mark.asyncio
async def test_unavailable_executable_is_refused_before_invocation(fresh_session) -> None:
    backend = FakeBackend(help_stdout="--json resume", version_returncode=127)
    provider = CodexCliProvider(backend=backend)
    with pytest.raises(ProviderUnavailable, match="not proven"):
        await provider.invoke(request(fresh_session))
    assert len(backend.specs) == 2


@pytest.mark.asyncio
async def test_unproven_resume_is_refused_before_invocation(fresh_session) -> None:
    backend = FakeBackend(help_stdout="--output-format stream-json")
    provider = ClaudeCodeProvider(backend=backend)
    with pytest.raises(ProviderUnavailable, match="resume support"):
        await provider.invoke(request(fresh_session, provider_session_id="claude-session-1"))
    assert len(backend.specs) == 2


@pytest.mark.asyncio
async def test_unproven_fork_is_refused_before_invocation(fresh_session) -> None:
    backend = FakeBackend(help_stdout="--output-format stream-json --resume")
    provider = ClaudeCodeProvider(backend=backend)
    with pytest.raises(ProviderUnavailable, match="fork support"):
        await provider.invoke(
            request(
                fresh_session,
                provider_session_id="claude-session-1",
                fork_provider_session=True,
            )
        )
    assert len(backend.specs) == 2


@pytest.mark.asyncio
async def test_proven_fork_invokes_claude_with_fork_flag(fresh_session) -> None:
    backend = FakeBackend(
        help_stdout="--output-format stream-json --resume --fork-session",
        invocation_stdout=fixture("claude_result.json"),
    )
    provider = ClaudeCodeProvider(backend=backend)

    result = await provider.invoke(
        request(
            fresh_session,
            provider_session_id="claude-parent-1",
            fork_provider_session=True,
        )
    )

    assert result.success is True
    assert provider.capabilities.fork is True
    assert "--fork-session" in backend.specs[-1].command


@pytest.mark.asyncio
async def test_fresh_session_id_is_only_emitted_when_observed(fresh_session) -> None:
    backend = FakeBackend(
        help_stdout="--output-format stream-json --resume",
        invocation_stdout='{"type":"assistant","message":{"content":[{"type":"text","text":"ok"}]}}\n',
    )
    provider = ClaudeCodeProvider(backend=backend)
    result = await provider.invoke(request(fresh_session))
    assert all(event.event_type != "provider_session" for event in result.events)


@pytest.mark.asyncio
async def test_stderr_nonzero_and_callback_failure_are_contained(fresh_session) -> None:
    backend = FakeBackend(
        help_stdout="--json resume",
        invocation_stdout=fixture("codex_success.jsonl"),
        invocation_stderr="provider diagnostic",
        invocation_returncode=2,
    )
    provider = CodexCliProvider(backend=backend)
    observed: list[int] = []

    def broken(event) -> None:
        observed.append(event.sequence)
        raise RuntimeError("observer failed")

    result = await provider.invoke(request(fresh_session), observers=[broken])
    assert result.success is False
    assert [event.to_dict().get("code") for event in result.events[-2:]] == [
        "provider_stderr",
        "provider_nonzero_exit",
    ]
    assert observed == list(range(len(result.events)))
    assert len(provider.last_observer_failures) == len(result.events)


def test_cli_providers_conform_and_config_is_selectable() -> None:
    assert isinstance(CodexCliProvider(backend=FakeBackend(help_stdout="")), AgentProvider)
    assert isinstance(ClaudeCodeProvider(backend=FakeBackend(help_stdout="")), AgentProvider)
    config = Config.from_env(
        {
            "SOVEREIGN_AGENT_AGENT_PROVIDER": "codex",
            "SOVEREIGN_AGENT_CODEX_EXECUTABLE": "/tools/codex",
        }
    )
    assert config.agent_provider == "codex"
    assert config.codex_executable == "/tools/codex"
