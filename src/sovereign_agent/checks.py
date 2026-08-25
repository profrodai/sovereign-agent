"""The check registry: deterministic questions with checkable answers.

A check is a small Python function that reads authoritative state and answers
one question about the world. Checks are looked up by a stable identifier, so an
outcome declares *which* questions must be answered, and nothing else gets to
decide that later.

Two rules make this teachable rather than magical:

1. A check is named for the fact it measures. `inventory_at_or_above_reorder_point`
   reads inventory. If it read cash, the name would be a lie — and that lie is the
   exact defect this module was written to remove.
2. A check returns the facts it observed *and* a digest of the state it read. The
   digest lets acceptance notice that the world moved after the check ran.

There is deliberately no rule engine here. A registry of named functions is
something a learner can read end to end in a minute.
"""

from __future__ import annotations

import json
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

from sovereign_agent.database import Database
from sovereign_agent.evidence import digest_payload


@dataclass(frozen=True)
class CheckResult:
    """The answer to one deterministic question, with its supporting facts."""

    check_id: str
    success: bool
    observed: dict[str, Any] = field(default_factory=dict)
    state_digest: str = ""
    detail: str = ""


CheckFn = Callable[[Database, str], CheckResult]


def _inventory_row(db: Database, sku: str) -> dict[str, int] | None:
    row = db.connection.execute(
        "SELECT on_hand, reserved, reorder_point FROM inventory WHERE sku = ?", (sku,)
    ).fetchone()
    if row is None:
        return None
    return {
        "on_hand": int(row["on_hand"]),
        "reserved": int(row["reserved"]),
        "reorder_point": int(row["reorder_point"]),
    }


def _cash_cents(db: Database) -> int:
    row = db.connection.execute(
        "SELECT COALESCE(SUM(amount_cents), 0) AS total FROM cash_entries"
    ).fetchone()
    return int(row["total"])


def _digest_for(db: Database, sku: str) -> str:
    """Digest the facts every store check depends on.

    Deliberately NOT an event counter: a plain `UPDATE inventory` changes the
    world without appending an event, so a counter would report 'fresh' while
    the claim had already become false.
    """
    return digest_payload(
        {"sku": sku, "inventory": _inventory_row(db, sku), "cash": _cash_cents(db)}
    )


def inventory_at_or_above_reorder_point(db: Database, sku: str) -> CheckResult:
    """WORLD FACT: is there actually enough stock on the shelf right now?"""
    row = _inventory_row(db, sku)
    digest = _digest_for(db, sku)
    if row is None:
        return CheckResult(
            "inventory_at_or_above_reorder_point",
            False,
            {"sku": sku},
            digest,
            f"No inventory row for {sku}.",
        )
    ok = row["on_hand"] >= row["reorder_point"]
    return CheckResult(
        "inventory_at_or_above_reorder_point",
        ok,
        {"sku": sku, **row},
        digest,
        f"on_hand={row['on_hand']} vs reorder_point={row['reorder_point']}",
    )


def cash_reconciles(db: Database, sku: str) -> CheckResult:
    """WORLD FACT: does the purchase cash entry match the replenishment event?

    This is a reconciliation, not a solvency test. `SUM(...) >= 0` would happily
    pass a purchase that recorded -9999 for six units of tea. Here the recorded
    cash movement must equal exactly -(qty * unit_cost) for the committed
    replenishment, and the entry must be tied to that same assignment.
    """
    digest = _digest_for(db, sku)
    events = [
        json.loads(row["payload"])
        for row in db.connection.execute(
            "SELECT payload FROM events WHERE kind = 'replenishment.committed' ORDER BY seq"
        ).fetchall()
    ]
    events = [event for event in events if event.get("sku") == sku]
    if not events:
        return CheckResult(
            "cash_reconciles", False, {"sku": sku}, digest, "No replenishment to reconcile against."
        )
    problems: list[str] = []
    observed: list[dict[str, Any]] = []
    for event in events:
        row = db.connection.execute(
            "SELECT amount_cents, record FROM cash_entries WHERE id = ?", (event["cash_id"],)
        ).fetchone()
        if row is None:
            problems.append(f"cash entry {event['cash_id']} is missing")
            continue
        expected = -(int(event["qty"]) * int(event["unit_cost_cents"]))
        actual = int(row["amount_cents"])
        record = json.loads(row["record"])
        observed.append({"cash_id": event["cash_id"], "expected": expected, "actual": actual})
        if actual != expected:
            problems.append(f"cash entry {event['cash_id']} is {actual}, expected {expected}")
        if record.get("assignment_id") != event.get("assignment_id"):
            problems.append(f"cash entry {event['cash_id']} is not tied to the replenishment")
    return CheckResult(
        "cash_reconciles",
        not problems,
        {"sku": sku, "entries": observed, "cash_cents": _cash_cents(db)},
        digest,
        "; ".join(problems) if problems else f"{len(observed)} purchase entr(y/ies) reconcile",
    )


def replenishment_event_exists(db: Database, sku: str) -> CheckResult:
    """WORLD FACT: did a replenishment actually get committed to the ledger?"""
    digest = _digest_for(db, sku)
    rows = [
        json.loads(row["payload"])
        for row in db.connection.execute(
            "SELECT payload FROM events WHERE kind = 'replenishment.committed'"
        ).fetchall()
    ]
    matching = [row for row in rows if row.get("sku") == sku]
    return CheckResult(
        "replenishment_event_exists",
        bool(matching),
        {"sku": sku, "count": len(matching)},
        digest,
        f"{len(matching)} replenishment event(s) for {sku}",
    )


REGISTRY: dict[str, CheckFn] = {
    "inventory_at_or_above_reorder_point": inventory_at_or_above_reorder_point,
    "cash_reconciles": cash_reconciles,
    "replenishment_event_exists": replenishment_event_exists,
}

# Checks about the world vs checks about the process. Both matter, but only the
# first kind can tell you the business outcome is true.
WORLD_FACT_CHECKS = frozenset(REGISTRY)


def run_check(db: Database, check_id: str, subject: str) -> CheckResult:
    """Execute one declared check. Unknown or erroring checks FAIL CLOSED.

    An unknown check is not a pass and not a skip: an outcome that declares a
    question nobody can answer has not been proved.
    """
    fn = REGISTRY.get(check_id)
    if fn is None:
        return CheckResult(
            check_id,
            False,
            {"subject": subject},
            "",
            f"Unknown check '{check_id}'. Unknown checks fail closed.",
        )
    try:
        return fn(db, subject)
    except Exception as error:  # noqa: BLE001 - an erroring check must never pass
        return CheckResult(
            check_id,
            False,
            {"subject": subject},
            "",
            f"Check raised {type(error).__name__}: {error}",
        )
