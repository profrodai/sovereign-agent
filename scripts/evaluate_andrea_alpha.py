#!/usr/bin/env python3
"""Run the machine-checkable half of the Andrea Alpha evaluation.

Stdlib only. Executes the cold-start learner path exactly as the guide writes
it, and reports what a fresh Andrea-profile session would actually see.

It scores REACHABILITY, not understanding. Tasks 4 and 7 of
docs/andrea-alpha-evaluation.md require a human reading Andrea's answers; this
script says so rather than inventing a score for them.

Exits 0 when every machine-checkable task passes.
"""

from __future__ import annotations

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

        # Task 1: enter the environment.
        code, output = run([python, "-m", "sovereign_agent", "doctor"])
        ok = code == 0 and "Python:" in output
        results.append(
            (
                "1. doctor runs on a cold start",
                ok,
                output.strip().splitlines()[0] if output.strip() else "",
            )
        )

        # Task 2: reach a truthful accepted outcome.
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
        truthful = code == 0
        results.append(
            (
                "2b. the accepted outcome is TRUE",
                truthful,
                output.strip().splitlines()[-1] if output.strip() else "",
            )
        )

        # Task 3: the eight artifacts are locatable.
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

        # Task 5: changing the reorder point changes the verdict.
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

        # Task 6: a malformed provider report is refused.
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

        # Task 7 (partial): no Pulse event was fabricated.
        org = Organization(root)
        kinds = [
            str(row["kind"])
            for row in org.db.connection.execute("SELECT kind FROM events").fetchall()
        ]
        ok = not any(kind.startswith("pulse.") for kind in kinds)
        results.append(
            (
                "7. no Pulse event fabricated before Unit 9",
                ok,
                "no pulse events" if ok else "PULSE EVENT FOUND",
            )
        )

    elapsed = time.monotonic() - started

    print("Andrea Alpha — machine-checkable tasks\n")
    failures = 0
    for label, ok, detail in results:
        mark = "PASS" if ok else "FAIL"
        if not ok:
            failures += 1
        print(f"  [{mark}] {label}")
        if detail:
            print(f"         {detail}")

    print(f"\nmachine execution time: {elapsed:.1f}s")
    print("(The ten-minute budget is learner reading time, not machine time.)")
    print("\nNOT machine-checkable — a human must read Andrea's answers:")
    print("  4. why an actor is not a provider; why the operator cannot self-approve;")
    print("     why evidence is more than an ID; governance versus operational data")
    print("  7. why the organization is still passive before Pulse (Unit 9)")

    if failures:
        print(f"\n{failures} machine-checkable task(s) failed.")
        return 1
    print("\nAll machine-checkable tasks pass. Schedule the human session.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
