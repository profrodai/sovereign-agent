"""Deterministic fixture runner. No network."""

from __future__ import annotations

import json
from pathlib import Path

from sovereign_agent.models import ActorReport
from sovereign_agent.providers.base import (
    InvocationRequest,
    InvocationSpec,
    ProviderCapabilities,
    ProviderEvent,
    parse_json_line,
)


class ScriptedProvider:
    name = "scripted"
    executable = "python"
    requires_terminal_event = False

    def probe(self) -> ProviderCapabilities:
        return ProviderCapabilities(
            available=True,
            print_mode=True,
            streaming=True,
            structured_result=True,
        )

    def build_invocation(self, request: InvocationRequest) -> InvocationSpec:
        return InvocationSpec(
            argv=[
                "python",
                "-m",
                "sovereign_agent.providers.scripted",
                str(request.output),
                request.prompt,
            ],
            cwd=request.workspace,
        )

    def parse_event(self, line: str) -> ProviderEvent | None:
        return parse_json_line(line)


def write_scripted_report(output: Path, prompt: str) -> ActorReport:
    output.mkdir(parents=True, exist_ok=True)
    (output / "messages").mkdir(exist_ok=True)
    try:
        envelope = json.loads(prompt)
        scope = str(envelope["statement_of_work"]["scope"])
    except (json.JSONDecodeError, KeyError, TypeError):
        scope = prompt
    report = ActorReport(
        status="completed" if "fail" not in scope.lower() else "failed",
        changed_artifacts=["inventory.md"],
        proposed_checks=["inventory_non_negative", "cash_reconciles"],
        questions=[],
        notes="scripted fixture",
    )
    (output / "report.json").write_text(report.model_dump_json(indent=2), encoding="utf-8")
    (output / "artifacts.json").write_text(
        '{"inventory.md": "replenishment proposed"}', encoding="utf-8"
    )
    return report


def main(argv: list[str] | None = None) -> int:
    import sys

    args = list(sys.argv[1:] if argv is None else argv)
    write_scripted_report(Path(args[0]), args[1] if len(args) > 1 else "")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
