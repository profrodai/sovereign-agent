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

import hashlib  # noqa: E402

from sovereign_agent.checks import run_check  # noqa: E402
from sovereign_agent.governance import render_outcome  # noqa: E402
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
    subject = outcome.subject
    if not subject:
        # `outcome.subject or SKU` silently re-pointed a subjectless outcome at
        # tea and reported "ACCEPTED and true". Reported on PR #24.
        return [f"outcome {outcome_id} declares no subject: nothing to check it against"]

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

    # 7. EVERY SOW's proof chain, validated separately. The core permits
    #    per-SOW executions, so an oracle that assumes one latest execution owns
    #    all evidence will call a legitimate multi-SOW organization false. Both
    #    must agree, or the control plane can mint a state its own gate rejects.
    sows = org.sows_for(outcome_id)
    if not sows:
        fail("no SOW for this outcome")
    for sow in sows:
        if sow.state.value != "ACCEPTED":
            fail(f"SOW {sow.id} is {sow.state.value}, not ACCEPTED")
            continue
        execution = org.completed_assignment_for_sow(sow.id)
        if not execution:
            fail(f"SOW {sow.id} has no completed execution")
            continue

        verification = org.verification_for_sow(sow.id)
        if verification is None:
            fail(f"SOW {sow.id} has no verification")
            continue
        if verification.assignment_id != execution or verification.sow_id != sow.id:
            fail(f"verification {verification.id} is not bound to SOW {sow.id}'s execution")

        rows = db.connection.execute(
            "SELECT check_id, success, assignment_id FROM evidence WHERE verification_id = ?",
            (verification.id,),
        ).fetchall()
        passing = {str(row["check_id"]) for row in rows if int(row["success"]) == 1}
        missing = set(outcome.acceptance_checks) - passing
        if missing:
            fail(f"SOW {sow.id}: checks without successful evidence: {sorted(missing)}")
        for row in rows:
            if str(row["assignment_id"]) != execution:
                fail(f"SOW {sow.id}: evidence for '{row['check_id']}' is bound elsewhere")

        review_rows = db.connection.execute(
            "SELECT reviewer_actor_id, decision FROM reviews "
            "WHERE sow_id = ? AND verification_id = ?",
            (sow.id, verification.id),
        ).fetchall()
        if not review_rows:
            fail(f"SOW {sow.id} has no review of its current verification")
        for row in review_rows:
            if str(row["decision"]) != "accepted":
                fail(f"SOW {sow.id}: review decision is {row['decision']}")
            reviewer = str(row["reviewer_actor_id"])
            if reviewer == json.loads(
                db.connection.execute(
                    "SELECT record FROM assignments WHERE id = ?", (execution,)
                ).fetchone()["record"]
            ).get("actor_id"):
                fail(f"SOW {sow.id}: reviewer {reviewer} also performed the work")

        receipt_rows = db.connection.execute(
            "SELECT record, status FROM receipts WHERE assignment_id = ?", (execution,)
        ).fetchall()
        if not receipt_rows:
            fail(f"SOW {sow.id}: no receipt bound to execution {execution}")
        for row in receipt_rows:
            receipt = json.loads(row["record"])
            if str(row["status"]) != str(receipt.get("status")):
                fail(f"SOW {sow.id}: receipt column and record disagree")
            elif receipt.get("status") != "completed":
                fail(f"SOW {sow.id}: receipt status is {receipt.get('status')}")

        # Only SOWs that DECLARE a required effect must have changed the world.
        if sow.required_effect_kind is not None:
            kinds = org.effect_kinds_for_execution(execution)
            if sow.required_effect_kind not in kinds:
                fail(
                    f"SOW {sow.id} declares {sow.required_effect_kind} but its "
                    f"execution produced none"
                )

    # 8. Freshness is checked once, against the OUTCOME-LEVEL observation --
    #    selected explicitly, exactly as `Organization.accept()` selects it.
    #    This used to keep whichever SOW was iterated last, so review order
    #    changed which batch the oracle called final and the release gate
    #    rejected organizations the core had legitimately accepted.
    outcome_observation = org.outcome_verification(outcome_id)
    if outcome_observation is None:
        fail("the outcome condition has not been verified")
    else:
        for check_id in outcome.acceptance_checks:
            current = run_check(db, check_id, subject)
            digests = {
                str(row["state_digest"])
                for row in db.connection.execute(
                    "SELECT state_digest FROM evidence WHERE verification_id = ? AND check_id = ?",
                    (outcome_observation.id, check_id),
                ).fetchall()
            }
            if digests and current.state_digest not in digests:
                fail(f"evidence for '{check_id}' is stale relative to current state")

    # 9. The receipt sidecars on disk must exist and match.
    workspaces = list((root / ".sovereign" / "runs").glob("*"))
    if not workspaces:
        fail("no run workspace on disk")
    for workspace in workspaces:
        receipt_path = workspace / "receipt.json"
        digest_path = workspace / "receipt.json.sha256"
        if not receipt_path.is_file():
            fail(f"{workspace.name}: receipt.json is missing")
            continue
        if not digest_path.is_file():
            fail(f"{workspace.name}: receipt.json.sha256 is missing")
            continue
        expected = hashlib.sha256(receipt_path.read_text(encoding="utf-8").encode()).hexdigest()
        if digest_path.read_text(encoding="utf-8").strip() != expected:
            fail(f"{workspace.name}: receipt digest does not match receipt.json")

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
        for row in review_rows:
            if str(row["reviewer_actor_id"]) == accepted_by:
                fail(f"{accepted_by} both reviewed and accepted")
        for performer in performers:
            if org.actor(performer).role.value != "operator":
                fail(f"performer {performer} is not an operator")

    # 11. EVERY projected file matches the ledger byte for byte, not just `state`.
    directory = root / "governance" / "outcomes" / outcome_id
    for name, data in render_outcome(outcome, org.sows_for(outcome_id)).items():
        path = directory / name
        if not path.is_file():
            fail(f"projection {name} is missing")
        elif path.read_bytes() != data:
            fail(f"projection {name} does not match the ledger")

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
