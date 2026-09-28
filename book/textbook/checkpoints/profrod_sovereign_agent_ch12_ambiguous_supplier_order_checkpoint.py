# Prof Rod | Build Your Always-On AI Agent From Scratch
# Full book and learning materials: https://profrod.ai/book
# Join the Prof Rod learner community: https://profrod.ai/community
# Original source and updates: https://github.com/profrodai/sovereign-agent

"""Chapter 12: an accepted order with a lost response and independent receipts."""

import json
import math
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
from sovereign_agent.assistant_orders import SpendingPolicy, approve, execute, propose
from sovereign_agent.assistant_work import claim, enqueue
from sovereign_agent.database import Database

BOOK = Path(__file__).resolve().parents[1]
RETRY = runpy.run_path(str(BOOK / "learner/profrod_sovereign_agent_ch12_retries_learner.py"))


def retry_arithmetic():
    """Part A's formulas by independent checks, and the receipt recomputed from its runs."""
    attempts, duplicates = RETRY["expected_attempts"], RETRY["expected_duplicates"]
    assert attempts(0, 0) == 1 and duplicates(0.3, 0) == 0
    a, b = 0.1, 0.2
    s = 1 - a - b
    series = sum(s * (1 - s) ** (k - 1) * (k - 1) * b / (a + b) for k in range(1, 400))
    assert math.isclose(series, duplicates(a, b)) and math.isclose(attempts(a, b), 1 / s)
    capped = RETRY["capped_attempts"]
    assert capped(0.5, 3) == 1.75 and capped(1, 3) == 3 and capped(0, 5) == 1
    key = RETRY["operation_key"]
    proposal = {"sku": "SKU-VANILLA", "quantity": 6}
    assert key("w", "t", proposal) == key("w", "t", dict(reversed(list(proposal.items()))))
    assert key("w", "t", proposal) != key("w", "other", proposal)
    print("ok   duplicates are b / (1 - a - b), and one key names one intended order")
    receipt = json.loads(
        (BOOK.parents[1] / "docs/evidence/book-ch12/ch12-retries-receipt-v1.json").read_text()
    )
    latencies = receipt["timeouts"]["pilot_latencies"]
    rules = {
        "pilot median": RETRY["percentile"](latencies, 50),
        "pilot 90th percentile": RETRY["percentile"](latencies, 90),
        "twice the pilot maximum": round(2 * max(latencies), 3),
    }
    for row in receipt["timeouts"]["rows"]:
        assert row["timeout_seconds"] == rules[row["rule"]]
        share = RETRY["timed_out_share"](latencies, row["timeout_seconds"])
        assert round(share, 3) == row["pilot_timed_out_share"]
        mine = [
            order
            for order in receipt["timeouts"]["orders"]
            if (order["rule"], order["operation_key"]) == (row["rule"], row["operation_key"])
        ]
        attempts = sum(len(order["attempts"]) for order in mine) / len(mine)
        placed = sum(order["supplier_orders"] for order in mine) / len(mine)
        assert round(attempts, 3) == row["mean_attempts"]
        assert round(placed, 3) == row["supplier_orders_per_intended"]
    for row in receipt["behavior"]["rows"]:
        runs = [
            [c["name"] for c in run["turns"][-1]["calls"]]
            for run in receipt["runs"]
            if (run["model"], run["error"]) == (row["model"], row["error_text"])
        ]
        assert row["resent"] == sum("place_order" in names for names in runs)
        assert row["looked_up"] == sum("lookup_order" in names for names in runs)
        resends = sum(names.count("place_order") for names in runs)
        assert row["supplier_orders_without_key"] == len(runs) + resends
        assert row["supplier_orders_with_key"] == len(runs)
    print("ok   timeouts, re-sends and supplier orders recompute from the retained runs")


@contextmanager
def independent_supplier(root):
    ready = root / "supplier-ready"
    supplier_path = root / "supplier.sqlite"
    process = subprocess.Popen(
        [
            sys.executable,
            "-m",
            "reference_organizations.store.supplier",
            "--database",
            str(supplier_path),
            "--port",
            "0",
            "--ready",
            str(ready),
            "--drop-first-response",
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    try:
        deadline = time.monotonic() + 10
        while not ready.exists() and time.monotonic() < deadline and process.poll() is None:
            time.sleep(0.02)
        if not ready.exists():
            raise RuntimeError("independent supplier did not become ready")
        yield SupplierClient("http://127.0.0.1:" + ready.read_text()), supplier_path
    finally:
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=5)


def spending(db):
    row = db.connection.execute(
        "SELECT reserved_cents,spent_cents FROM assistant_spending WHERE id=1"
    ).fetchone()
    return tuple(row)


def experiment(root):
    with independent_supplier(root) as (supplier, supplier_path):
        db = Database(root / "agent.sqlite")
        try:
            seed_lucy(db)
            enqueue(db, "chapter9:morning", "lucy", "Replenish vanilla")
            work = claim(db, "chapter9-worker")
            identifier = propose(db, work, "SKU-VANILLA", 6, target=supplier.identity)
            assert propose(db, work, "SKU-VANILLA", 6, target=supplier.identity) == identifier
            digest = db.connection.execute(
                "SELECT digest FROM assistant_orders WHERE id=?", (identifier,)
            ).fetchone()[0]
            policy = SpendingPolicy(frozenset({"lucy"}), total_cents=2000)
            approve(db, identifier, digest, actor="lucy", policy=policy, expires=time.time() + 60)
            initial = execute(db, work, identifier, supplier, policy=policy)
            assert initial["status"] == "UNKNOWN"
            print("initial", initial["status"])
            print("reserved and spent", *spending(db))
            with sqlite3.connect(supplier_path) as remote:
                assert remote.execute("SELECT count(*) FROM orders").fetchone()[0] == 1
            # Reopen the durable ledger while the same ownership claim remains valid.
            # Worker death and replacement are a separate Chapter 13 experiment.
            db.close()
            db = Database(root / "agent.sqlite")
            receipt = execute(db, work, identifier, supplier, policy=policy)
            assert receipt["status"] == "ACCEPTED"
            assert execute(db, work, identifier, supplier, policy=policy) == receipt
            status = db.connection.execute(
                "SELECT status FROM assistant_orders WHERE id=?", (identifier,)
            ).fetchone()[0]
            print("after reconciliation", receipt["status"], status)
            print("reserved and spent", *spending(db))
            with sqlite3.connect(supplier_path) as remote:
                count = remote.execute("SELECT count(*) FROM orders").fetchone()[0]
                assert count == 1
                print("supplier orders", count)
            assert spending(db) == (0, 1500)
        finally:
            db.close()


def main():
    retry_arithmetic()
    with tempfile.TemporaryDirectory(prefix="lucy-chapter9-") as directory:
        experiment(Path(directory))


if __name__ == "__main__":
    main()
