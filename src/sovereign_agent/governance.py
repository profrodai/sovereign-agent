"""Outcomes, SOWs, rulings, and Markdown projections."""

from __future__ import annotations

from pathlib import Path

from sovereign_agent.files import write_json, write_text
from sovereign_agent.models import Outcome, Ruling, StatementOfWork


def project_outcome(root: Path, outcome: Outcome, sows: list[StatementOfWork]) -> None:
    directory = root / "governance" / "outcomes" / outcome.id
    write_json(directory / "outcome.json", outcome.model_dump(mode="json"))
    lines = [
        f"# {outcome.title}",
        "",
        f"- id: `{outcome.id}`",
        f"- state: `{outcome.state}`",
        f"- owner: `{outcome.owner_actor_id}`",
        "",
        "## Desired state",
        "",
        outcome.desired_state,
        "",
        "## Acceptance checks",
        "",
        *[f"- {check}" for check in outcome.acceptance_checks],
        "",
        "## SOWs",
        "",
    ]
    sow_lines = [f"- `{sow.id}` ({sow.state}): {sow.scope}" for sow in sows] or ["- none"]
    lines.extend(sow_lines)
    lines.append("")
    write_text(directory / "README.md", "\n".join(lines))
    for sow in sows:
        write_json(directory / "sows" / f"{sow.id}.json", sow.model_dump(mode="json"))


def project_ruling(root: Path, ruling: Ruling) -> None:
    write_json(
        root / "governance" / "rulings" / f"{ruling.id}.json", ruling.model_dump(mode="json")
    )
    write_text(
        root / "governance" / "rulings" / f"{ruling.id}.md",
        "\n".join(
            [
                f"# Ruling {ruling.id}",
                "",
                f"**Question:** {ruling.question}",
                "",
                f"**Decision:** {ruling.decision}",
                "",
                f"**Authority:** `{ruling.authority_actor_id}`",
                "",
                f"**Applies to:** `{ruling.applies_to}`",
                "",
            ]
        ),
    )
