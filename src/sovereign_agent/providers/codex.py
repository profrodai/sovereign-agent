"""Codex CLI adapter. Capabilities come from live --help probes."""

from __future__ import annotations

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


class CodexProvider:
    name = "codex"
    executable = "codex"
    requires_terminal_event = True

    def probe(self) -> ProviderCapabilities:
        if look_up(self.executable) is None:
            return ProviderCapabilities(available=False)
        version_probe = capture(self.executable, "--version")
        exec_probe = capture(self.executable, "exec", "--help")
        resume_probe = capture(self.executable, "exec", "resume", "--help")
        evidence = (version_probe, exec_probe, resume_probe)
        failed = next((item for item in evidence[:2] if item.exit_code != 0), None)
        if failed is not None:
            return ProviderCapabilities(
                available=False,
                evidence=evidence,
                degraded_reason=failed.error or f"{' '.join(failed.command)} exited non-zero",
            )
        version = version_probe.stdout.strip().splitlines()
        exec_help = exec_probe.text
        resume_help = resume_probe.text
        return ProviderCapabilities(
            available=True,
            version=version[0] if version else "",
            print_mode=True,
            streaming=has_flag(exec_help, "--json"),
            resume=resume_probe.exit_code == 0 and "resume" in resume_help,
            sandbox=has_flag(exec_help, "--sandbox"),
            evidence=evidence,
            degraded_reason=(
                resume_probe.error or "codex exec resume --help exited non-zero"
                if resume_probe.exit_code != 0
                else None
            ),
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
        if request.provider_session_id:
            argv = [
                self.executable,
                "exec",
                "resume",
                "--json",
                request.provider_session_id,
            ]
        else:
            argv = [self.executable, "exec", "--json"]
        if request.require_sandbox:
            argv.extend(["--sandbox", "workspace-write"])
        argv.append(request.prompt)
        return InvocationSpec(argv=argv, cwd=request.workspace)

    def parse_event(self, line: str) -> ProviderEvent | None:
        event = parse_json_line(line)
        if event is None or event.malformed:
            return event
        payload = event.payload
        kind = str(payload.get("type") or "raw")
        thread_id = payload.get("thread_id")
        usage = payload.get("usage")
        normalized_usage = (
            {str(key): value for key, value in usage.items() if isinstance(value, int)}
            if isinstance(usage, dict)
            else {}
        )
        terminal = kind in {"turn.completed", "turn.failed"}
        succeeded = kind == "turn.completed" if terminal else None
        if kind in {"turn.failed", "error"}:
            kind = "error"
        return ProviderEvent(
            kind=kind,
            payload=payload,
            raw=event.raw,
            terminal=terminal,
            succeeded=succeeded,
            session_id=thread_id if isinstance(thread_id, str) else None,
            usage=normalized_usage,
        )
