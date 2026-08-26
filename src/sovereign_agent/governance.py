"""Outcomes, SOWs, rulings, and Markdown projections."""

from __future__ import annotations

import json
from pathlib import Path

from sovereign_agent.files import atomic_write, write_json, write_text
from sovereign_agent.models import Outcome, Ruling, StatementOfWork


def render_outcome(outcome: Outcome, sows: list[StatementOfWork]) -> dict[str, bytes]:
    """Render the projection WITHOUT writing it.

    Verification needs the expected bytes in memory. When rendering and writing
    were one function, `verify_projections.py` had to call the writer to learn
    what the files should contain -- so it silently repaired the drift it was
    supposed to report. A verifier that edits reality until it agrees with
    itself is not a check.
    """
    files: dict[str, bytes] = {
        "outcome.json": json.dumps(
            outcome.model_dump(mode="json"), indent=2, sort_keys=True, default=str
        ).encode()
    }
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
    lines.extend([f"- `{sow.id}` ({sow.state}): {sow.scope}" for sow in sows] or ["- none"])
    lines.append("")
    files["README.md"] = "\n".join(lines).encode()
    for sow in sows:
        files[f"sows/{sow.id}.json"] = json.dumps(
            sow.model_dump(mode="json"), indent=2, sort_keys=True, default=str
        ).encode()
    return files


def project_outcome(root: Path, outcome: Outcome, sows: list[StatementOfWork]) -> None:
    """Write the rendered projection. Derived output; never authoritative."""
    directory = root / "governance" / "outcomes" / outcome.id
    for name, data in render_outcome(outcome, sows).items():
        atomic_write(directory / name, data)


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
