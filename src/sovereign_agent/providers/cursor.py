"""Cursor Agent CLI adapter. Equal in the registry, not a documentation bridge."""

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


class CursorProvider:
    name = "cursor"
    executable = "agent"

    def probe(self) -> ProviderCapabilities:
        if look_up(self.executable) is None:
            return ProviderCapabilities(available=False)
        version = capture(self.executable, "--version").strip().splitlines()
        help_text = capture(self.executable, "--help").lower()
        return ProviderCapabilities(
            available=True,
            version=version[0] if version else "",
            streaming="--output-format" in help_text and "stream-json" in help_text,
            resume="--resume" in help_text,
            sandbox="--workspace" in help_text,
        )

    def build_invocation(self, request: InvocationRequest) -> InvocationSpec:
        caps = self.probe()
        require_proven(
            caps,
            request,
            missing="agent (Cursor CLI)",
            inspect="agent --help",
            next_command="Install Cursor Agent CLI or bind the actor to scripted.",
        )
        argv = [
            self.executable,
            "-p",
            "--output-format",
            "stream-json",
            "--workspace",
            str(request.workspace),
        ]
        if request.provider_session_id and caps.resume:
            argv.extend(["--resume", request.provider_session_id])
        argv.append(request.prompt)
        return InvocationSpec(argv=argv, cwd=request.workspace)

    def parse_event(self, line: str) -> ProviderEvent | None:
        return parse_json_line(line)
