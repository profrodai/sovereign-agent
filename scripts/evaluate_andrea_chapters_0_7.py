#!/usr/bin/env python3
"""Run the machine-checkable half of the Andrea Chapters 0-7 evaluation.

Stdlib only (plus the production package, matching evaluate_andrea_alpha.py).
Executes the cold-start learner path through Chapter 7 exactly as
docs/andrea-chapters-0-7-evaluation.md writes it, and reports what a fresh
Andrea-profile session would actually see.

It scores REACHABILITY and DURABLE EVIDENCE, not understanding. Task 4 (from
the historical docs/andrea-alpha-evaluation.md) and Tasks 7b/7c/7d of the new
document require a human reading Andrea's answers; this script says so rather
than inventing a score for them.

Exits 0 when every machine-checkable task passes.
"""

from __future__ import annotations

import sqlite3
import subprocess
import sys
import tempfile
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "src"))


def run(argv: list[str]) -> tuple[int, str]:
    result = subprocess.run(  # noqa: S603 - fixed argv, no shell
        argv, capture_output=True, text=True, cwd=REPO_ROOT
    )
    return result.returncode, (result.stdout + result.stderr)


def main() -> int:
    python = sys.executable
    results: list[tuple[str, bool, str]] = []
    started = time.monotonic()

    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp) / "andrea-shift"

        # Tasks 1-6: the historical cold-start path, unchanged in substance
        # from evaluate_andrea_alpha.py -- reproduced here rather than
        # imported, since this script is meant to stand alone the same way
        # docs/andrea-chapters-0-7-evaluation.md itself does.
        code, output = run([python, "-m", "sovereign_agent", "doctor"])
        ok = code == 0 and "Python:" in output
        results.append(
            (
                "1. doctor runs on a cold start",
                ok,
                output.strip().splitlines()[0] if output.strip() else "",
            )
        )

        code, output = run(
            [
                python,
                "-m",
                "sovereign_agent",
                "demo",
                "store",
                "--mode",
                "simulated",
                "--root",
                str(root),
            ]
        )
        accepted = code == 0 and "ACCEPTED" in output
        results.append(
            (
                "2a. demo reaches ACCEPTED",
                accepted,
                output.strip().splitlines()[-1] if output.strip() else "",
            )
        )

        code, output = run(
            [python, str(REPO_ROOT / "scripts" / "verify_store_outcome.py"), str(root)]
        )
        results.append(
            (
                "2b. the accepted outcome is TRUE",
                code == 0,
                output.strip().splitlines()[-1] if output.strip() else "",
            )
        )

        from sovereign_agent.organization import Organization

        org = Organization(root)
        tables = {
            "outcome": "SELECT COUNT(*) c FROM outcomes",
            "SOW": "SELECT COUNT(*) c FROM sows",
            "assignment": "SELECT COUNT(*) c FROM assignments",
            "evidence": "SELECT COUNT(*) c FROM evidence",
            "inventory": "SELECT COUNT(*) c FROM inventory",
            "cash entry": "SELECT COUNT(*) c FROM cash_entries",
            "event history": "SELECT COUNT(*) c FROM events",
            "receipt": "SELECT COUNT(*) c FROM receipts",
        }
        missing = [
            name
            for name, query in tables.items()
            if int(org.db.connection.execute(query).fetchone()["c"]) == 0
        ]
        found_files = list((root / ".sovereign" / "runs").glob("*/receipt.json"))
        ok = not missing and bool(found_files)
        results.append(
            (
                "3. all eight artifacts exist and are locatable",
                ok,
                "all present" if ok else f"missing: {missing}",
            )
        )

        org.db.connection.execute("UPDATE inventory SET reorder_point = 99 WHERE sku = 'SKU-TEA'")
        org.db.connection.commit()
        org.db.close()
        code, output = run(
            [python, str(REPO_ROOT / "scripts" / "verify_store_outcome.py"), str(root)]
        )
        ok = code == 1
        results.append(
            (
                "5. raising the reorder point makes the claim fail",
                ok,
                "verifier correctly refuses" if ok else "verifier still passed",
            )
        )

        bad = Path(tmp) / "report.json"
        bad.write_text("{not json", encoding="utf-8")
        from reference_organizations.store.demo import propose_restock_from_report
        from sovereign_agent.errors import Refusal

        try:
            propose_restock_from_report(bad, "SKU-TEA")
            ok, detail = False, "malformed report was accepted"
        except Refusal as refusal:
            ok, detail = True, str(refusal).splitlines()[0]
        results.append(("6. malformed provider report is refused", ok, detail))

        # Task 3.5: Chapters 4-6 reachability -- each exercise runs cleanly
        # against a fresh root, exits without raising.
        for chapter, _entry in (
            ("ch04_work_stays_inside_its_boundary", "explore_workspace_lifecycle"),
            ("ch05_authority_needs_a_fence", "explore_fencing"),
            ("ch06_the_organization_recovers", "recover_from_a_real_hard_kill"),
        ):
            script = REPO_ROOT / "book" / chapter / "solution.py"
            chapter_root = Path(tmp) / chapter
            code, output = run([python, str(script), "--root", str(chapter_root)])
            ok = code == 0
            results.append(
                (
                    f"3.5. {chapter} exercise runs cleanly",
                    ok,
                    "exit 0" if ok else output.strip().splitlines()[-1] if output.strip() else "",
                )
            )

        # Task 7: the decisive addition this document makes. Run Chapter 7's
        # own exercise, then verify -- independently, via a fresh sqlite3
        # connection, NOT by trusting the exercise script's own printed
        # summary -- that a genuine, traceable Pulse chain landed.
        ch07_root = Path(tmp) / "ch07"
        ch07_script = REPO_ROOT / "book" / "ch07_the_organization_wakes_itself" / "solution.py"
        code, output = run([python, str(ch07_script), "--root", str(ch07_root)])
        ok = code == 0 and '"pulse_work_created_present": true' in output
        results.append(
            (
                "7a. Chapter 7 exercise reaches genuine Pulse-created work",
                ok,
                "reached" if ok else output.strip().splitlines()[-1] if output.strip() else "",
            )
        )

        db_path = ch07_root / ".sovereign" / "organization.db"
        if db_path.is_file():
            connection = sqlite3.connect(str(db_path))
            connection.row_factory = sqlite3.Row
            try:
                pulse_events = connection.execute(
                    "SELECT COUNT(*) AS c FROM events WHERE kind LIKE 'pulse.%'"
                ).fetchone()["c"]
                traceable = connection.execute(
                    "SELECT COUNT(*) AS c FROM pulse_origins po "
                    "JOIN pulse_wake_decisions wd ON wd.id = po.wake_decision_id "
                    "WHERE po.origin_kind = 'pulse' AND wd.source_signal_id IS NOT NULL"
                ).fetchone()["c"]
                ok = pulse_events > 0 and traceable > 0
                results.append(
                    (
                        "7c. independently-queried pulse_origins chain is traceable",
                        ok,
                        f"pulse.* events={pulse_events} traceable_origins={traceable}",
                    )
                )
            finally:
                connection.close()
        else:
            results.append(
                (
                    "7c. independently-queried pulse_origins chain is traceable",
                    False,
                    "no database found",
                )
            )

        # Not machine-checkable: the historical Task 4, and this document's
        # own 7b (prediction) and 7d (boundary explanation) all require a
        # human reading Andrea's own words.

    elapsed = time.monotonic() - started

    print("Andrea Chapters 0-7 -- machine-checkable tasks\n")
    failures = 0
    for label, ok, detail in results:
        mark = "PASS" if ok else "FAIL"
        if not ok:
            failures += 1
        print(f"  [{mark}] {label}")
        if detail:
            print(f"         {detail}")

    print(f"\nmachine execution time: {elapsed:.1f}s")
    print("\nNOT machine-checkable -- a human must read Andrea's answers:")
    print("  4. (historical) why an actor is not a provider; why the operator cannot")
    print("     self-approve; why evidence is more than an ID; governance vs. operational data")
    print("  7b. Andrea's prediction of what replaced manual dispatch, before reading the code")
    print("  7d. Andrea's explanation of what Pulse still does NOT do (no scheduling, no cron)")

    if failures:
        print(f"\n{failures} machine-checkable task(s) failed.")
        return 1
    print("\nAll machine-checkable tasks pass. Schedule the human session.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
