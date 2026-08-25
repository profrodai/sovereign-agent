#!/usr/bin/env python3
"""Detect drift between the SQLite ledger and the generated governance files.

Markdown and JSON under `governance/` are projections. They are never read back,
which means nothing else will ever notice if they go stale or are hand-edited.
This script notices.

Drift is always resolved TOWARD the database: the ledger is the authority and
the projection is regenerated. See docs/persistence-boundary.md.

    python scripts/verify_projections.py <organization-root>

Exits 0 when every projection matches the ledger, 1 otherwise.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "src"))

from sovereign_agent.governance import project_outcome  # noqa: E402
from sovereign_agent.organization import Organization  # noqa: E402


def check(root: Path) -> list[str]:
    problems: list[str] = []
    org = Organization(root)
    rows = org.db.connection.execute("SELECT id FROM outcomes").fetchall()
    if not rows:
        return ["no outcomes in the ledger: nothing to project"]

    for row in rows:
        outcome_id = str(row["id"])
        outcome = org._outcome(outcome_id)  # noqa: SLF001
        sows = org.sows_for(outcome_id)
        directory = root / "governance" / "outcomes" / outcome_id

        json_path = directory / "outcome.json"
        if not json_path.is_file():
            problems.append(f"{outcome_id}: outcome.json is missing")
        else:
            on_disk = json.loads(json_path.read_text(encoding="utf-8"))
            expected = json.loads(json.dumps(outcome.model_dump(mode="json"), default=str))
            if on_disk != expected:
                differing = sorted(
                    key
                    for key in set(on_disk) | set(expected)
                    if on_disk.get(key) != expected.get(key)
                )
                problems.append(
                    f"{outcome_id}: outcome.json differs from the ledger "
                    f"(fields: {', '.join(differing) or 'unknown'})"
                )

        readme = directory / "README.md"
        if not readme.is_file():
            problems.append(f"{outcome_id}: README.md is missing")
        else:
            before = readme.read_text(encoding="utf-8")
            project_outcome(root, outcome, sows)
            after = readme.read_text(encoding="utf-8")
            if before != after:
                problems.append(
                    f"{outcome_id}: README.md was stale or hand-edited "
                    "(regenerated from the ledger)"
                )
    return problems


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print(__doc__)
        return 2
    root = Path(argv[1]).resolve()
    if not (root / ".sovereign" / "organization.db").is_file():
        print(f"no organization at {root}")
        return 2
    problems = check(root)
    for problem in problems:
        print(f"DRIFT: {problem}")
    if problems:
        print(f"\n{len(problems)} projection problem(s). The ledger is the authority.")
        return 1
    print("projections match the ledger")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
