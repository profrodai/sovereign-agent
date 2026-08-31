#!/usr/bin/env python3
"""Run the machine-checkable half of the new Chapters 0-12 Andrea tasks.

Stdlib only (plus the production package), following
`scripts/evaluate_andrea_chapters_0_7.py`'s own established shape. Covers
ONLY Task 8 (multi-SKU isolation) and Task 9 (pilot-start structured
evidence, replay, and refusal)'s own machine-checkable reachability/evidence
portions -- Tasks 1-7 are already covered by
`evaluate_andrea_chapters_0_7.py` and are not reproduced here, and Task 10
(distinguishing the local mechanism from a real deployment; identifying ZEO
Go as the production path) is a comprehension question only a human reader
can score, so this script explicitly declines to score it rather than
inventing a result.

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
        # -------------------------------------------------------------
        # Task 8: multi-SKU isolation. Reachability -- Chapter 8's own
        # exercise seeds a real multi-SKU catalog (at least two
        # independently-tracked SKUs) and the isolation properties
        # tests/test_store_multi_sku.py proves are the ones this task
        # asks Andrea to observe, not re-derive. This script confirms the
        # cold-start exercise reaches a catalog with at least two SKUs and
        # genuinely independent reorder points and inventory rows -- the
        # observable evidence Andrea is asked to point at.
        # -------------------------------------------------------------
        ch08_root = Path(tmp) / "ch08"
        ch08_script = REPO_ROOT / "book" / "ch08_the_store_becomes_a_catalog" / "solution.py"
        code, output = run([python, str(ch08_script), "--root", str(ch08_root)])
        ok = code == 0 and '"at_least_two": true' in output and '"not_all_the_same": true' in output
        results.append(
            (
                "8a. Chapter 8 exercise seeds an isolated multi-SKU catalog",
                ok,
                "reached" if ok else output.strip().splitlines()[-1] if output.strip() else "",
            )
        )

        db_path = ch08_root / ".sovereign" / "organization.db"
        if db_path.is_file():
            connection = sqlite3.connect(str(db_path))
            connection.row_factory = sqlite3.Row
            try:
                sku_rows = connection.execute(
                    "SELECT sku, on_hand, reorder_point FROM inventory ORDER BY sku"
                ).fetchall()
                skus = [str(row["sku"]) for row in sku_rows]
                distinct_reorder_points = {int(row["reorder_point"]) for row in sku_rows}
                ok = len(skus) >= 2 and len(distinct_reorder_points) > 1
                results.append(
                    (
                        "8b. independently-queried inventory rows are per-SKU, not shared",
                        ok,
                        f"skus={skus} reorder_points={sorted(distinct_reorder_points)}",
                    )
                )
            finally:
                connection.close()
        else:
            results.append(
                (
                    "8b. independently-queried inventory rows are per-SKU, not shared",
                    False,
                    "no database found",
                )
            )

        # -------------------------------------------------------------
        # Task 9: pilot-start structured evidence, replay, and refusal.
        # Chapter 12's own exercise already proves: a durable `pilots` row,
        # an idempotent replay of the SAME disposable identity, and exactly
        # one `pilot.started` event despite the replay. This script runs
        # that exercise, then independently drives one further refusal case
        # (a DIFFERENT pilot_id while the exercise's own pilot is active)
        # against the SAME database, verifying `start_pilot`'s fail-closed
        # refusal directly rather than trusting the exercise's own summary.
        # -------------------------------------------------------------
        ch12_root = Path(tmp) / "ch12"
        ch12_script = REPO_ROOT / "book" / "ch12_the_pilot_begins_with_a_receipt" / "solution.py"
        code, output = run([python, str(ch12_script), "--root", str(ch12_root)])
        ok = (
            code == 0
            and '"idempotent_replay": true' in output
            and '"exactly_one_despite_the_replay_above": true' in output
        )
        results.append(
            (
                "9a. Chapter 12 exercise reaches structured pilot-start evidence and replay",
                ok,
                "reached" if ok else output.strip().splitlines()[-1] if output.strip() else "",
            )
        )

        db_path = ch12_root / ".sovereign" / "organization.db"
        if db_path.is_file():
            from reference_organizations.store.pilot import start_pilot
            from sovereign_agent.database import Database
            from sovereign_agent.errors import Refusal

            db = Database(db_path)
            try:
                start_pilot(
                    db,
                    pilot_id="book-ch12-exercise-pretender",
                    store_org_id="book-ch12-exercise-store-org-different",
                    pilot_profile_id="book-ch12-exercise-profile",
                    evidence_namespace="book-ch12-exercise-evidence-ns",
                )
                ok, detail = False, "a different pilot_id was NOT refused while one is active"
            except Refusal as refusal:
                ok = refusal.category == "pilot_already_active"
                detail = f"refused: category={refusal.category!r}"
            finally:
                db.close()
            results.append(("9b. a different pilot_id is refused while one is active", ok, detail))

            connection = sqlite3.connect(str(db_path))
            connection.row_factory = sqlite3.Row
            try:
                pilots_row_count = connection.execute(
                    "SELECT COUNT(*) AS c FROM pilots"
                ).fetchone()["c"]
                # The refused attempt above rolled back its WHOLE transaction --
                # no orphaned `pilots` row from the refused, different pilot_id.
                ok = pilots_row_count == 1
                results.append(
                    (
                        "9c. the refused attempt left no orphaned pilots row",
                        ok,
                        f"pilots_row_count={pilots_row_count} (expected 1, the exercise's own)",
                    )
                )
            finally:
                connection.close()
        else:
            results.append(
                (
                    "9b. a different pilot_id is refused while one is active",
                    False,
                    "no database found",
                )
            )
            results.append(
                ("9c. the refused attempt left no orphaned pilots row", False, "no database found")
            )

        # Not machine-checkable: Task 8's own "explain why" comprehension
        # portion, and Task 10 entirely -- distinguishing the local
        # mechanism from a real 30-day deployment and identifying ZEO Go as
        # the production graduation path requires a human reader.

    elapsed = time.monotonic() - started

    print("Andrea Chapters 8-9 -- machine-checkable portions only\n")
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
    print("  8. Andrea's explanation of why the two SKUs' state never leaks into each other")
    print("  9d. Andrea's explanation of what proves the replay is safe, not merely repeated")
    print("  10. Andrea distinguishing the local mechanism from a real 30-day deployment,")
    print("      and identifying ZEO Go as the production graduation path")

    if failures:
        print(f"\n{failures} machine-checkable task(s) failed.")
        return 1
    print("\nAll machine-checkable tasks pass. Schedule the human session.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
