"""Codex CLI adapter. Capabilities come from live --help probes."""

from __future__ import annotations

from sovereign_agent.providers.base import (
    InvocationRequest,
    InvocationSpec,
    ProviderCapabilities,
    ProviderEvent,
    capture,
    look_up,
    parse_json_line,
    require_proven,
)


class CodexProvider:
    name = "codex"
    executable = "codex"

    def probe(self) -> ProviderCapabilities:
        if look_up(self.executable) is None:
            return ProviderCapabilities(available=False)
        version = capture(self.executable, "--version").strip().splitlines()
        help_text = capture(self.executable, "--help").lower()
        exec_help = capture(self.executable, "exec", "--help").lower()
        text = f"{help_text}\n{exec_help}"
        return ProviderCapabilities(
            available=True,
            version=version[0] if version else "",
            streaming="--json" in text,
            resume="--resume" in text,
            sandbox="--sandbox" in text,
            usage="--json" in text,
        )

    def build_invocation(self, request: InvocationRequest) -> InvocationSpec:
        caps = self.probe()
        require_proven(
            caps,
            request,
            missing="codex",
            inspect="codex exec --help",
            next_command="Install Codex CLI or bind the actor to scripted.",
        )
        argv = [self.executable, "exec", "--json"]
        if caps.sandbox:
            argv.extend(["--sandbox", "workspace-write"])
        if request.provider_session_id and caps.resume:
            argv.extend(["--resume", request.provider_session_id])
        argv.append(request.prompt)
        return InvocationSpec(argv=argv, cwd=request.workspace)

    def parse_event(self, line: str) -> ProviderEvent | None:
        return parse_json_line(line)
