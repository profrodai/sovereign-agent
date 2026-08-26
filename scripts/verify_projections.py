#!/usr/bin/env python3
"""Detect drift between the SQLite ledger and the generated governance files.

Markdown and JSON under `governance/` are projections. They are never read back,
which means nothing else will ever notice if they go stale or are hand-edited.
This script notices — and does NOT fix.

Verification is PURE. An earlier version called the projection writer to learn
what the files should contain, which silently repaired hand-edited SOWs and then
reported "projections match the ledger". A verifier that edits reality until it
agrees with itself is worse than no verifier, because it reports success.

Repair lives behind an explicit flag:

    python scripts/verify_projections.py <organization-root>            # check only
    python scripts/verify_projections.py <organization-root> --reconcile  # rewrite

Drift is always resolved TOWARD the database. See docs/persistence-boundary.md.
Exits 0 when every projection matches the ledger, 1 otherwise.
"""

from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "src"))

from sovereign_agent.governance import project_outcome, render_outcome  # noqa: E402
from sovereign_agent.organization import Organization  # noqa: E402


def check(root: Path) -> list[str]:
    """Compare every projected file against expected bytes. Never writes."""
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
        expected = render_outcome(outcome, sows)

        for name, data in expected.items():
            path = directory / name
            if not path.is_file():
                problems.append(f"{outcome_id}: {name} is missing")
                continue
            if path.read_bytes() != data:
                problems.append(f"{outcome_id}: {name} does not match the ledger")

        # Extra SOW projections are drift too: a deleted SOW must not linger.
        sows_directory = directory / "sows"
        if sows_directory.is_dir():
            expected_sows = {name.split("/", 1)[1] for name in expected if name.startswith("sows/")}
            for path in sorted(sows_directory.glob("*.json")):
                if path.name not in expected_sows:
                    problems.append(f"{outcome_id}: sows/{path.name} is not in the ledger")
    return problems


def reconcile(root: Path) -> int:
    """Rewrite projections from the ledger. Explicit, never a side effect of checking."""
    org = Organization(root)
    count = 0
    for row in org.db.connection.execute("SELECT id FROM outcomes").fetchall():
        outcome_id = str(row["id"])
        project_outcome(root, org._outcome(outcome_id), org.sows_for(outcome_id))  # noqa: SLF001
        count += 1
    print(f"reconciled {count} outcome projection(s) from the ledger")
    return 0


def main(argv: list[str]) -> int:
    arguments = [item for item in argv[1:] if not item.startswith("--")]
    if len(arguments) != 1:
        print(__doc__)
        return 2
    root = Path(arguments[0]).resolve()
    if not (root / ".sovereign" / "organization.db").is_file():
        print(f"no organization at {root}")
        return 2
    if "--reconcile" in argv:
        return reconcile(root)

    problems = check(root)
    for problem in problems:
        print(f"DRIFT: {problem}")
    if problems:
        print(f"\n{len(problems)} projection problem(s). The ledger is the authority.")
        print("Rewrite them with: verify_projections.py <root> --reconcile")
        return 1
    print("projections match the ledger")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
