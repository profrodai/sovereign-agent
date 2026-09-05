"""Durable unattended work, separate from heartbeat and signal-driven Pulse."""

from __future__ import annotations

import json
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any

from sovereign_agent.database import Database
from sovereign_agent.ids import new_id, utc_now

MAX_STATE_BYTES = 16_384
Condition = Callable[[dict[str, Any]], "WatchDecision"]
Payload = Callable[[str, str], None]


@dataclass(frozen=True)
class WatchDecision:
    fire: bool
    message: str
    state: dict[str, Any]


@dataclass(frozen=True)
class AutomationResult:
    status: str
    run_id: str | None = None
    detail: str = ""


def create_automation(
    db: Database,
    automation_id: str,
    *,
    interval_seconds: int,
    payload: str,
    first_run_at: datetime | None = None,
    max_failures: int = 3,
) -> None:
    if interval_seconds < 1 or max_failures < 1:
        raise ValueError("interval and max_failures must be positive")
    with db.transaction():
        db.connection.execute(
            "INSERT INTO automations"
            "(id, interval_seconds, next_run_at, payload, max_failures) "
            "VALUES (?, ?, ?, ?, ?)",
            (
                automation_id,
                interval_seconds,
                (first_run_at or utc_now()).isoformat(),
                payload,
                max_failures,
            ),
        )


def run_due(
    db: Database,
    automation_id: str,
    condition: Condition,
    payload: Payload,
    *,
    now: datetime | None = None,
) -> AutomationResult:
    observed_at = now or utc_now()
    row = db.connection.execute(
        "SELECT * FROM automations WHERE id = ?", (automation_id,)
    ).fetchone()
    if row is None:
        raise KeyError(automation_id)
    if not row["enabled"]:
        return AutomationResult("DISABLED")
    due_at = datetime.fromisoformat(row["next_run_at"])
    if observed_at < due_at:
        return AutomationResult("NOT_DUE")
    previous = json.loads(row["condition_state"])
    decision = condition(previous)
    encoded = json.dumps(decision.state, sort_keys=True, separators=(",", ":"))
    if len(encoded.encode()) > MAX_STATE_BYTES:
        raise ValueError("condition state exceeds 16384 bytes")
    next_at = due_at + timedelta(seconds=int(row["interval_seconds"]))
    if not decision.fire:
        with db.immediate() as connection:
            changed = connection.execute(
                "UPDATE automations SET condition_state = ?, next_run_at = ? "
                "WHERE id = ? AND next_run_at = ?",
                (encoded, next_at.isoformat(), automation_id, row["next_run_at"]),
            ).rowcount
        return AutomationResult("NO_FIRE" if changed else "RACED")
    run_id = new_id("run")
    try:
        with db.immediate() as connection:
            connection.execute(
                "INSERT INTO automation_runs"
                "(id, automation_id, due_at, message, status, created_at) "
                "VALUES (?, ?, ?, ?, 'RUNNING', ?)",
                (
                    run_id,
                    automation_id,
                    row["next_run_at"],
                    decision.message,
                    observed_at.isoformat(),
                ),
            )
            connection.execute(
                "UPDATE automations SET next_run_at = ? WHERE id = ? AND next_run_at = ?",
                (next_at.isoformat(), automation_id, row["next_run_at"]),
            )
    except Exception as error:
        if "UNIQUE constraint failed" in str(error):
            return AutomationResult("REPLAYED", detail="due slot already claimed")
        raise
    try:
        payload(run_id, decision.message)
    except Exception as error:
        with db.transaction():
            db.connection.execute(
                "UPDATE automation_runs SET status = 'FAILED', error = ? WHERE id = ?",
                (str(error), run_id),
            )
            db.connection.execute(
                "UPDATE automations SET failure_count = failure_count + 1, "
                "enabled = CASE WHEN failure_count + 1 >= max_failures "
                "THEN 0 ELSE enabled END WHERE id = ?",
                (automation_id,),
            )
        return AutomationResult("FAILED", run_id, str(error))
    with db.transaction():
        db.connection.execute(
            "UPDATE automation_runs SET status = 'SUCCEEDED' WHERE id = ?", (run_id,)
        )
        db.connection.execute(
            "UPDATE automations SET condition_state = ?, failure_count = 0 WHERE id = ?",
            (encoded, automation_id),
        )
    return AutomationResult("SUCCEEDED", run_id)
