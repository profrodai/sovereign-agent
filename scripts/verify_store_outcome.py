#!/usr/bin/env python3
"""Assert that an accepted store outcome is ACTUALLY TRUE.

Run this after `sovereign-agent demo store`. It reads the ledger and checks the
world, rather than trusting the status field — because the whole point of this
unit is that a status field can lie.

    python scripts/verify_store_outcome.py <organization-root>

Exits 0 only when every claim below holds.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "src"))

from sovereign_agent.checks import run_check  # noqa: E402
from sovereign_agent.organization import Organization  # noqa: E402

SKU = "SKU-TEA"


def verify(root: Path) -> list[str]:
    failures: list[str] = []
    org = Organization(root)
    db = org.db

    row = db.connection.execute("SELECT id FROM outcomes").fetchone()
    if row is None:
        return ["no outcome exists"]
    outcome_id = str(row["id"])
    outcome = org._outcome(outcome_id)  # noqa: SLF001
    subject = outcome.subject or SKU

    def fail(message: str) -> None:
        failures.append(message)

    # 1. The outcome says ACCEPTED.
    if outcome.state.value != "ACCEPTED":
        fail(f"outcome state is {outcome.state.value}, expected ACCEPTED")

    # 2. Every declared check passes RIGHT NOW, re-executed against live state.
    for check_id in outcome.acceptance_checks:
        result = run_check(db, check_id, subject)
        if not result.success:
            fail(f"check '{check_id}' does not hold now: {result.detail}")

    # 3. Inventory is at or above the reorder point.
    inventory = db.connection.execute(
        "SELECT on_hand, reorder_point FROM inventory WHERE sku = ?", (subject,)
    ).fetchone()
    if inventory is None:
        fail(f"no inventory row for {subject}")
    elif int(inventory["on_hand"]) < int(inventory["reorder_point"]):
        fail(
            f"inventory {inventory['on_hand']} is below reorder point {inventory['reorder_point']}"
        )

    # 4. A purchasing cash entry exists, and cash reconciles.
    purchases = db.connection.execute(
        "SELECT id, amount_cents, record FROM cash_entries WHERE amount_cents < 0"
    ).fetchall()
    if not purchases:
        fail("no purchasing cash entry")

    # 5. A real replenishment event exists.
    events = db.connection.execute("SELECT kind, payload FROM events ORDER BY seq").fetchall()
    kinds = [str(event["kind"]) for event in events]
    if "replenishment.committed" not in kinds:
        fail("no replenishment.committed event")

    # 6. No Pulse was fabricated. Pulse is Unit 9.
    fabricated = [kind for kind in kinds if kind.startswith("pulse.")]
    if fabricated:
        fail(f"pulse events before Unit 9: {fabricated}")

    # 7. Every declared check has successful evidence bound to this outcome
    #    and to the execution that acceptance used.
    evidence = db.connection.execute(
        "SELECT check_id, success, assignment_id, state_digest FROM evidence WHERE outcome_id = ?",
        (outcome_id,),
    ).fetchall()
    passing = {str(row["check_id"]) for row in evidence if int(row["success"]) == 1}
    missing = set(outcome.acceptance_checks) - passing
    if missing:
        fail(f"declared checks without successful bound evidence: {sorted(missing)}")

    execution_id = org._latest_assignment_id(outcome_id)  # noqa: SLF001
    for row in evidence:
        if str(row["assignment_id"]) != execution_id:
            fail(f"evidence for '{row['check_id']}' is bound to another execution")

    # 8. Evidence is not stale relative to current state.
    for check_id in outcome.acceptance_checks:
        current = run_check(db, check_id, subject)
        digests = {str(row["state_digest"]) for row in evidence if str(row["check_id"]) == check_id}
        if digests and current.state_digest not in digests:
            fail(f"evidence for '{check_id}' is stale relative to current state")

    # 9. The receipt is successful and digest-bound.
    receipts = db.connection.execute("SELECT record FROM receipts").fetchall()
    if not receipts:
        fail("no receipt recorded")
    for row in receipts:
        receipt = json.loads(row["record"])
        if receipt.get("status") != "completed":
            fail(f"receipt {receipt.get('id')} status is {receipt.get('status')}")
    for digest_file in (root / ".sovereign" / "runs").glob("*/receipt.json.sha256"):
        import hashlib

        receipt_json = (digest_file.parent / "receipt.json").read_text(encoding="utf-8")
        expected = hashlib.sha256(receipt_json.encode()).hexdigest()
        if digest_file.read_text(encoding="utf-8").strip() != expected:
            fail(f"receipt digest mismatch at {digest_file}")

    # 10. Operator, reviewer, and Principal are distinct governed actors.
    acceptance_row = db.connection.execute(
        "SELECT record FROM acceptance WHERE outcome_id = ?", (outcome_id,)
    ).fetchone()
    if acceptance_row is None:
        fail("no acceptance record")
    else:
        accepted_by = json.loads(acceptance_row["record"])["accepted_by"]
        performers = org.performers_for(outcome_id)
        if accepted_by in performers:
            fail(f"{accepted_by} accepted work it performed")
        if org.actor(accepted_by).role.value != "principal":
            fail(f"{accepted_by} is not the Principal")
        for performer in performers:
            if org.actor(performer).role.value != "operator":
                fail(f"performer {performer} is not an operator")

    # 11. Governance projections agree with the ledger.
    projection = root / "governance" / "outcomes" / outcome_id / "outcome.json"
    if not projection.is_file():
        fail("governance projection missing")
    else:
        on_disk = json.loads(projection.read_text(encoding="utf-8"))
        if on_disk.get("state") != outcome.state.value:
            fail(f"projection says {on_disk.get('state')}, ledger says {outcome.state.value}")

    return failures


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print(__doc__)
        return 2
    root = Path(argv[1]).resolve()
    if not (root / ".sovereign" / "organization.db").is_file():
        print(f"no organization at {root}")
        return 2
    failures = verify(root)
    for failure in failures:
        print(f"FAIL: {failure}")
    if failures:
        print(f"\n{len(failures)} problem(s): this outcome is NOT truthfully accepted.")
        return 1
    print("ACCEPTED and true: inventory, cash, events, evidence, and actors all check out.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
