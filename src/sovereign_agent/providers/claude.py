"""Claude Code CLI adapter. Capabilities come from live --help probes."""

from __future__ import annotations

from sovereign_agent.errors import Refusal
from sovereign_agent.providers.base import (
    InvocationRequest,
    InvocationSpec,
    ProviderCapabilities,
    ProviderEvent,
    capture,
    has_flag,
    look_up,
    parse_json_line,
    require_proven,
)


class ClaudeProvider:
    name = "claude"
    executable = "claude"
    requires_terminal_event = True

    def probe(self) -> ProviderCapabilities:
        if look_up(self.executable) is None:
            return ProviderCapabilities(available=False)
        version_probe = capture(self.executable, "--version")
        help_probe = capture(self.executable, "--help")
        evidence = (version_probe, help_probe)
        failed = next((item for item in evidence if item.exit_code != 0), None)
        if failed is not None:
            return ProviderCapabilities(
                available=False,
                evidence=evidence,
                degraded_reason=failed.error or f"{' '.join(failed.command)} exited non-zero",
            )
        version = version_probe.stdout.strip().splitlines()
        help_text = help_probe.text
        return ProviderCapabilities(
            available=True,
            version=version[0] if version else "",
            print_mode=has_flag(help_text, "-p") or has_flag(help_text, "--print"),
            streaming=has_flag(help_text, "--output-format") and "stream-json" in help_text,
            resume=has_flag(help_text, "--resume"),
            structured_result=has_flag(help_text, "--json-schema"),
            verbose=has_flag(help_text, "--verbose"),
            evidence=evidence,
        )

    def build_invocation(self, request: InvocationRequest) -> InvocationSpec:
        caps = self.probe()
        require_proven(
            caps,
            request,
            missing="claude",
            inspect="claude --help",
            next_command="Install Claude Code or bind the actor to scripted.",
        )
        if not caps.verbose:
            raise Refusal(
                "claude cannot prove --verbose for stream-json.",
                "Claude stream-json requires the exact installed CLI flags to be proven.",
                "claude --help",
                "Upgrade Claude Code or bind the actor to scripted.",
            )
        argv = [self.executable, "-p", "--output-format", "stream-json", "--verbose"]
        if request.provider_session_id and caps.resume:
            argv.extend(["--resume", request.provider_session_id])
        argv.append(request.prompt)
        return InvocationSpec(argv=argv, cwd=request.workspace)

    def parse_event(self, line: str) -> ProviderEvent | None:
        event = parse_json_line(line)
        if event is None or event.malformed:
            return event
        payload = event.payload
        kind = str(payload.get("type") or "raw")
        session_id = payload.get("session_id")
        usage = payload.get("usage")
        normalized_usage = (
            {str(key): value for key, value in usage.items() if isinstance(value, int)}
            if isinstance(usage, dict)
            else {}
        )
        terminal = kind == "result"
        succeeded = None
        if terminal:
            succeeded = payload.get("subtype") == "success" and not bool(payload.get("is_error"))
            if not succeeded:
                kind = "error"
        return ProviderEvent(
            kind=kind,
            payload=payload,
            raw=event.raw,
            terminal=terminal,
            succeeded=succeeded,
            session_id=session_id if isinstance(session_id, str) else None,
            usage=normalized_usage,
        )
