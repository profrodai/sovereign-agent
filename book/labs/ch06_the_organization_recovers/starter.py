"""Starter for Chapter 6's supervisor-recovery lab."""

from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import NamedTuple

STUDENT_TODO = True
WORKER_LOST = "worker_lost"


class RecoveryState(NamedTuple):
    """The three durable facts one recovery transaction must reconcile."""

    assignment_state: str
    current_attempt: str | None
    receipt_count: int


def recover(connection: sqlite3.Connection, attempt_id: str, *, inject_fault: bool = False) -> bool:
    """Try to recover one still-current abandoned attempt."""
    # TODO(1): Begin an immediate transaction and CAS RUNNING/current_attempt.
    # TODO(2): Write a FAILED/worker_lost receipt and clear the fence in the
    # same transaction; injected failure must roll every fact back.
    # TODO(3): Treat a lost CAS as an idempotent false result, not an error or
    # second receipt.
    raise NotImplementedError


def read_state(connection: sqlite3.Connection) -> RecoveryState:
    """Read the assignment/fence/receipt facts used by the assertions."""
    raise NotImplementedError


def exercise(root: Path) -> dict[str, object]:
    """Recover an expired attempt atomically and reject duplicate recovery."""
    # TODO(4): Demonstrate the naive output-file guess, inject rollback, then
    # let two SQLite connections contend and return check.py's observations.
    raise NotImplementedError("Implement the Chapter 6 recovery experiment")
