"""Intelligence-provider contract. Adapters never use shell=True."""

from __future__ import annotations

import json
import re
import shutil
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Protocol

from sovereign_agent.errors import Refusal


@dataclass(frozen=True)
class ProbeEvidence:
    command: tuple[str, ...]
    exit_code: int | None
    stdout: str = ""
    stderr: str = ""
    error: str | None = None

    @property
    def text(self) -> str:
        return f"{self.stdout}\n{self.stderr}".lower()


@dataclass(frozen=True)
class ProviderCapabilities:
    available: bool
    version: str = ""
    print_mode: bool = False
    streaming: bool = False
    resume: bool = False
    structured_result: bool = False
    sandbox: bool = False
    usage: bool = False
    workspace_selection: bool = False
    verbose: bool = False
    evidence: tuple[ProbeEvidence, ...] = ()
    degraded_reason: str | None = None


@dataclass(frozen=True)
class InvocationRequest:
    workspace: Path
    output: Path
    prompt: str
    require_print_mode: bool = True
    require_resume: bool = False
    require_streaming: bool = True
    require_structured_result: bool = False
    require_sandbox: bool = False
    require_usage: bool = False
    require_workspace_selection: bool = False
    provider_session_id: str | None = None


@dataclass(frozen=True)
class InvocationSpec:
    argv: list[str]
    cwd: Path
    env: dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class ProviderEvent:
    kind: str
    payload: dict[str, Any]
    raw: str
    malformed: bool = False
    terminal: bool = False
    succeeded: bool | None = None
    session_id: str | None = None
    usage: dict[str, int] = field(default_factory=dict)


class IntelligenceProvider(Protocol):
    name: str
    executable: str
    requires_terminal_event: bool

    def probe(self) -> ProviderCapabilities: ...

    def build_invocation(self, request: InvocationRequest) -> InvocationSpec: ...

    def parse_event(self, line: str) -> ProviderEvent | None: ...


def look_up(executable: str) -> str | None:
    return shutil.which(executable)


def has_flag(text: str, flag: str) -> bool:
    return re.search(rf"(?<![\w-]){re.escape(flag)}(?![\w-])", text) is not None


def capture(executable: str, *args: str) -> ProbeEvidence:
    command = (executable, *args)
    located = look_up(executable)
    if located is None:
        return ProbeEvidence(command=command, exit_code=None, error="executable not found")
    try:
        result = subprocess.run(
            [located, *args],
            check=False,
            capture_output=True,
            text=True,
            timeout=10,
            shell=False,
        )
    except (OSError, subprocess.TimeoutExpired) as error:
        return ProbeEvidence(command=command, exit_code=None, error=str(error))
    return ProbeEvidence(
        command=command,
        exit_code=result.returncode,
        stdout=result.stdout,
        stderr=result.stderr,
    )


def require_proven(
    caps: ProviderCapabilities,
    request: InvocationRequest,
    *,
    missing: str,
    inspect: str,
    next_command: str,
) -> None:
    if not caps.available:
        raise Refusal(
            f"{missing} is not installed.",
            "Provider CLIs are external executables, not package dependencies.",
            "sovereign-agent doctor",
            next_command,
        )
    if request.provider_session_id and not request.require_resume:
        raise Refusal(
            f"{missing} received a session id without resume intent.",
            "A session id must never be silently discarded.",
            inspect,
            "Run a fresh assignment instead of resuming.",
        )
    required = {
        "print mode": (request.require_print_mode, caps.print_mode),
        "streaming output": (request.require_streaming, caps.streaming),
        "resume": (request.require_resume, caps.resume),
        "structured result": (request.require_structured_result, caps.structured_result),
        "sandbox": (request.require_sandbox, caps.sandbox),
        "usage": (request.require_usage, caps.usage),
        "workspace selection": (
            request.require_workspace_selection,
            caps.workspace_selection,
        ),
    }
    missing_capabilities = [
        name
        for name, (wanted, proven) in required.items()
        if wanted and not proven
    ]
    if missing_capabilities:
        names = ", ".join(missing_capabilities)
        raise Refusal(
            f"{missing} cannot prove required capability: {names}.",
            "Fail closed: adapters may not hard-code unsupported flags or semantics.",
            inspect,
            next_command,
        )


def parse_json_line(line: str) -> ProviderEvent | None:
    stripped = line.strip()
    if not stripped:
        return None
    try:
        payload = json.loads(stripped)
    except json.JSONDecodeError:
        return ProviderEvent(
            kind="malformed",
            payload={"text": stripped},
            raw=stripped,
            malformed=True,
        )
    if not isinstance(payload, dict):
        return ProviderEvent(
            kind="malformed",
            payload={"value": payload},
            raw=stripped,
            malformed=True,
        )
    kind = str(payload.get("type") or payload.get("kind") or "raw")
    return ProviderEvent(kind=kind, payload=payload, raw=stripped)
