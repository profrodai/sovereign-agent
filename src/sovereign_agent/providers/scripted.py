"""Provider protocol and scripted adapter for offline lessons."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Protocol

from sovereign_agent.models import ActorReport


@dataclass(frozen=True)
class ProviderCapabilities:
    available: bool
    streaming: bool = False
    resume: bool = False


@dataclass(frozen=True)
class InvocationSpec:
    argv: list[str]
    cwd: Path
    env: dict[str, str] = field(default_factory=dict)


class IntelligenceProvider(Protocol):
    name: str

    def probe(self) -> ProviderCapabilities: ...

    def build_invocation(self, workspace: Path, output: Path, prompt: str) -> InvocationSpec: ...


class ScriptedProvider:
    """Deterministic fixture runner. No network. Invoked through subprocess argv."""

    name = "scripted"

    def probe(self) -> ProviderCapabilities:
        return ProviderCapabilities(available=True)

    def build_invocation(self, workspace: Path, output: Path, prompt: str) -> InvocationSpec:
        return InvocationSpec(
            argv=[
                "python",
                "-m",
                "sovereign_agent.providers.scripted",
                str(output),
                prompt,
            ],
            cwd=workspace,
        )


def write_scripted_report(output: Path, prompt: str) -> ActorReport:
    output.mkdir(parents=True, exist_ok=True)
    (output / "messages").mkdir(exist_ok=True)
    report = ActorReport(
        status="completed" if "fail" not in prompt.lower() else "failed",
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
