"""Intelligence-provider contract. Adapters never use shell=True."""

from __future__ import annotations

import json
import shutil
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Protocol

from sovereign_agent.errors import Refusal


@dataclass(frozen=True)
class ProviderCapabilities:
    available: bool
    version: str = ""
    streaming: bool = False
    resume: bool = False
    fork: bool = False
    structured_result: bool = False
    sandbox: bool = False
    usage: bool = False


@dataclass(frozen=True)
class InvocationRequest:
    workspace: Path
    output: Path
    prompt: str
    require_resume: bool = False
    require_streaming: bool = True
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


class IntelligenceProvider(Protocol):
    name: str
    executable: str

    def probe(self) -> ProviderCapabilities: ...

    def build_invocation(self, request: InvocationRequest) -> InvocationSpec: ...

    def parse_event(self, line: str) -> ProviderEvent | None: ...


def look_up(executable: str) -> str | None:
    return shutil.which(executable)


def capture(executable: str, *args: str) -> str:
    located = look_up(executable)
    if located is None:
        return ""
    result = subprocess.run(
        [located, *args],
        check=False,
        capture_output=True,
        text=True,
        timeout=10,
        shell=False,
    )
    return f"{result.stdout}\n{result.stderr}"


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
    if request.require_streaming and not caps.streaming:
        raise Refusal(
            f"{missing} cannot prove streaming output.",
            "Fail closed: adapters may not hard-code unsupported flags.",
            inspect,
            next_command,
        )
    if request.require_resume and not caps.resume:
        raise Refusal(
            f"{missing} cannot prove resume.",
            "Resume is used only when the probe shows the flag.",
            inspect,
            "Run a fresh assignment instead of resuming.",
        )


def parse_json_line(line: str) -> ProviderEvent | None:
    stripped = line.strip()
    if not stripped:
        return None
    try:
        payload = json.loads(stripped)
    except json.JSONDecodeError:
        return ProviderEvent(kind="raw", payload={"text": stripped}, raw=stripped)
    if not isinstance(payload, dict):
        return ProviderEvent(kind="raw", payload={"value": payload}, raw=stripped)
    kind = str(payload.get("type") or payload.get("kind") or "raw")
    return ProviderEvent(kind=kind, payload=payload, raw=stripped)
