"""Reference solution for Chapter 6: recovery records uncertainty honestly."""

from __future__ import annotations

import shutil
import sqlite3
from pathlib import Path

STUDENT_TODO = False


def _fresh(path: Path) -> None:
    if path.exists():
        shutil.rmtree(path)
    path.mkdir(parents=True)


def _recover(connection: sqlite3.Connection, attempt: str, *, inject_fault: bool = False) -> bool:
    try:
        connection.execute("BEGIN IMMEDIATE")
        cursor = connection.execute(
            "UPDATE assignments SET state='FAILED', current_attempt=NULL "
            "WHERE id='asg-1' AND state='RUNNING' AND current_attempt=?",
            (attempt,),
        )
        if cursor.rowcount != 1:
            connection.rollback()
            return False
        if inject_fault:
            raise RuntimeError("simulated crash before receipt")
        connection.execute(
            "INSERT INTO receipts(assignment_id, status, failure_category) "
            "VALUES('asg-1', 'failed', 'worker_lost')"
        )
        connection.commit()
        return True
    except RuntimeError:
        connection.rollback()
        return False


def exercise(root: Path) -> dict[str, object]:
    lab = root / "ch06"
    _fresh(lab)
    (lab / "partial-output.txt").write_text("work may have started", encoding="utf-8")
    connection = sqlite3.connect(lab / "recovery.db", isolation_level=None)
    connection.executescript(
        "CREATE TABLE assignments(id TEXT PRIMARY KEY, state TEXT NOT NULL, current_attempt TEXT);"
        "CREATE TABLE receipts(assignment_id TEXT UNIQUE, status TEXT, failure_category TEXT);"
        "INSERT INTO assignments VALUES('asg-1', 'RUNNING', 'attempt-7');"
    )

    naive_guess = "COMPLETED" if (lab / "partial-output.txt").exists() else "FAILED"
    injected_won = _recover(connection, "attempt-7", inject_fault=True)
    after_fault = connection.execute(
        "SELECT state, current_attempt FROM assignments WHERE id='asg-1'"
    ).fetchone()
    receipts_after_fault = connection.execute("SELECT COUNT(*) FROM receipts").fetchone()[0]
    connection.close()

    supervisor_a = sqlite3.connect(lab / "recovery.db", isolation_level=None)
    supervisor_b = sqlite3.connect(lab / "recovery.db", isolation_level=None)
    first_won = _recover(supervisor_a, "attempt-7")
    second_won = _recover(supervisor_b, "attempt-7")
    final_state, final_attempt = supervisor_a.execute(
        "SELECT state, current_attempt FROM assignments WHERE id='asg-1'"
    ).fetchone()
    receipt = supervisor_a.execute(
        "SELECT status, failure_category FROM receipts WHERE assignment_id='asg-1'"
    ).fetchone()
    receipt_count = supervisor_a.execute("SELECT COUNT(*) FROM receipts").fetchone()[0]
    supervisor_a.close()
    supervisor_b.close()

    return {
        "naive_output_guess": naive_guess,
        "injected_recovery_won": injected_won,
        "rollback_state": after_fault[0],
        "rollback_fence": after_fault[1],
        "rollback_receipts": receipts_after_fault,
        "supervisor_winners": int(first_won) + int(second_won),
        "terminal_state": final_state,
        "fence_released": final_attempt is None,
        "receipt_status": receipt[0],
        "failure_category": receipt[1],
        "receipt_count": receipt_count,
    }
