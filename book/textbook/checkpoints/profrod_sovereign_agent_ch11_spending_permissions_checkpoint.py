# Prof Rod | Build Your Always-On AI Agent From Scratch
# Full book and learning materials: https://profrod.ai/book
# Join the Prof Rod learner community: https://profrod.ai/community
# Original source and updates: https://github.com/profrodai/sovereign-agent

"""Chapter 11: exact approval survives restart, while obsolete authority cannot send."""

import json
import runpy
import sqlite3
import subprocess
import sys
import tempfile
import time
from contextlib import contextmanager
from pathlib import Path

from reference_organizations.store.agent import seed_lucy
from reference_organizations.store.supplier import SupplierClient
from sovereign_agent.assistant_orders import SpendingPolicy, approve, execute, propose, revoke
from sovereign_agent.assistant_work import claim, enqueue, finish
from sovereign_agent.database import Database


@contextmanager
def supplier_process(root):
    ready, path = root / "ready", root / "supplier.sqlite"
    process = subprocess.Popen(
        [
            sys.executable,
            "-m",
            "reference_organizations.store.supplier",
            "--database",
            str(path),
            "--port",
            "0",
            "--ready",
            str(ready),
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    try:
        deadline = time.monotonic() + 10
        while not ready.exists() and time.monotonic() < deadline and process.poll() is None:
            time.sleep(0.02)
        if not ready.exists():
            raise RuntimeError("chapter supplier failed to start")
        yield SupplierClient("http://127.0.0.1:" + ready.read_text()), path
    finally:
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=5)


def refused(action):
    try:
        action()
    except PermissionError:
        return True
    raise AssertionError("action unexpectedly retained authority")


def experiment(root):
    with supplier_process(root) as (supplier, supplier_path):
        db = Database(root / "agent.sqlite")
        try:
            seed_lucy(db)
            enqueue(db, "chapter8:morning", "lucy", "Prepare replenishment orders")
            work = claim(db, "chapter8-builder")
            original = propose(db, work, "SKU-VANILLA", 6, target=supplier.identity)

            def digest(operation):
                return db.connection.execute(
                    "SELECT digest FROM assistant_orders WHERE id=?", (operation,)
                ).fetchone()[0]

            automatic = SpendingPolicy(
                frozenset({"lucy"}), total_cents=2500, automatic_order_cents=2000
            )
            policy = SpendingPolicy(frozenset({"lucy"}), total_cents=2500)
            print(
                "Changed digest refused:",
                refused(
                    lambda: approve(
                        db, original, "wrong", actor="lucy", policy=policy, expires=time.time() + 60
                    )
                ),
            )
            print(
                "Model cannot approve:",
                refused(
                    lambda: approve(
                        db,
                        original,
                        digest(original),
                        actor="model",
                        policy=policy,
                        expires=time.time() + 60,
                    )
                ),
            )
            approve(
                db,
                original,
                digest(original),
                actor="lucy",
                policy=automatic,
                automatic=True,
                expires=time.time() + 60,
            )
            db.close()
            db = Database(root / "agent.sqlite")
            print(
                "Reduced automatic allowance refused:",
                refused(lambda: execute(db, work, original, supplier, policy=policy)),
            )
            # Controlled fault injection: the exact grant expired while work waited.
            with db.immediate() as connection:
                connection.execute(
                    "UPDATE assistant_orders SET approved_until=0 WHERE id=?", (original,)
                )
            print(
                "Expired grant refused:",
                refused(lambda: execute(db, work, original, supplier, policy=automatic)),
            )
            approve(
                db,
                original,
                digest(original),
                actor="lucy",
                policy=policy,
                expires=time.time() + 60,
            )
            # A changed physical fixture creates a revised need in the same assignment.
            with db.immediate() as connection:
                connection.execute("UPDATE inventory SET on_hand=1 WHERE sku='SKU-VANILLA'")
            revised = propose(db, work, "SKU-VANILLA", 7, target=supplier.identity)
            old = db.connection.execute(
                "SELECT status,revoked FROM assistant_orders WHERE id=?", (original,)
            ).fetchone()
            assert tuple(old) == ("REVOKED", 1)
            assert (
                db.connection.execute("SELECT reserved_cents FROM assistant_spending").fetchone()[0]
                == 0
            )
            print("Revision released obsolete reservation:", True)
            assert refused(lambda: execute(db, work, original, supplier, policy=policy))
            assert refused(
                lambda: approve(
                    db,
                    revised,
                    digest(original),
                    actor="lucy",
                    policy=policy,
                    expires=time.time() + 60,
                )
            )
            approve(
                db, revised, digest(revised), actor="lucy", policy=policy, expires=time.time() + 60
            )
            approve(
                db, revised, digest(revised), actor="lucy", policy=policy, expires=time.time() + 60
            )
            assert (
                db.connection.execute("SELECT reserved_cents FROM assistant_spending").fetchone()[0]
                == 1750
            )
            other = propose(db, work, "SKU-STRAWBERRY", 4, target=supplier.identity)
            print(
                "Cumulative overspend refused:",
                refused(
                    lambda: approve(
                        db,
                        other,
                        digest(other),
                        actor="lucy",
                        policy=policy,
                        expires=time.time() + 60,
                    )
                ),
            )
            with sqlite3.connect(supplier_path) as remote:
                assert remote.execute("SELECT count(*) FROM orders").fetchone()[0] == 0
            print("Supplier orders before authorized send:", 0)
            receipt = execute(db, work, revised, supplier, policy=policy)
            assert receipt["status"] == "ACCEPTED"
            assert execute(db, work, revised, supplier, policy=policy) == receipt
            revoke(db, other, actor="lucy", policy=policy)
            with sqlite3.connect(supplier_path) as remote:
                rows = remote.execute("SELECT operation,proposal FROM orders").fetchall()
            assert len(rows) == 1 and rows[0][0] == revised
            assert json.loads(rows[0][1])["quantity"] == 7
            balance = tuple(
                db.connection.execute(
                    "SELECT reserved_cents,spent_cents FROM assistant_spending"
                ).fetchone()
            )
            assert balance == (0, 1750)
            finish(db, work, "DONE", "Confirmed seven vanilla tubs for $17.50; no other purchase.")
            print("Supplier orders after authorized send:", len(rows))
            print("Reserved and spent cents:", *balance)
        finally:
            db.close()


BOOK = Path(__file__).resolve().parents[1]
CAL = runpy.run_path(str(BOOK / "learner/profrod_sovereign_agent_ch11_calibration_learner.py"))


def calibration_arithmetic():
    """Part A's formulas by independent checks, and the receipt recomputed from its runs."""
    assert CAL["reorder_quantity"](7, 5, 2) == 3 and CAL["reorder_quantity"](9, 1, 5) == 0
    assert CAL["calibration_error"]([1.0, 1.0], [True, False]) == 0.5
    assert CAL["calibration_error"]([0.5, 0.5], [True, False]) == 0.0
    assert CAL["auto_approval"]([0.95, 0.5], [False, True], 0.9) == (0.5, 1.0)
    assert CAL["agreement"]([3, 3, 7, 1, 3]) == (3, 0.6)
    assert round(CAL["approval_threshold"](1500, 50), 3) == 0.967
    print("ok   calibration error, agreement and the approval threshold")
    receipt = json.loads(
        (BOOK.parents[1] / "docs/evidence/book-ch11/ch11-calibration-receipt-v1.json").read_text()
    )
    for s in receipt["situations"]:
        assert s["answer"] == CAL["reorder_quantity"](s["on_hand"], s["daily"], s["days"])
    for row in receipt["rows"]:
        runs = [r for r in receipt["runs"] if r["model"] == row["model"] and "sample" in r]
        for run in runs:
            assert run["correct"] == (
                run["quantity"] == receipt["situations"][run["situation"]]["answer"]
            )
        confidences = [r["confidence"] for r in runs]
        correct = [r["correct"] for r in runs]
        assert round(sum(correct) / len(correct), 3) == row["accuracy"]
        error = CAL["calibration_error"](confidences, correct)
        assert round(error, 3) == row["stated_calibration_error"]
    print("ok   answers regraded, accuracy and calibration error recompute from the receipt")


def main():
    calibration_arithmetic()
    with tempfile.TemporaryDirectory(prefix="lucy-approval-") as directory:
        experiment(Path(directory))


if __name__ == "__main__":
    main()
