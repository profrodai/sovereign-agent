# Prof Rod | Build Your Always-On AI Agent From Scratch
# Full book and learning materials: https://profrod.ai/book
# Join the Prof Rod learner community: https://profrod.ai/community
# Original source and updates: https://github.com/profrodai/sovereign-agent

"""Chapter 7 learner file: durable work in, durable reports out.

The completed comparison copy of what the chapter builds, on top of the Chapter 4 StateStore. The
queue owns its own line of schema versions ("work"). Its invariants: every finished work item has
a report; every report belongs to finished work; a report's body never changes; and a send whose
reply was lost is recorded as unknown, never silently resent.
"""

from __future__ import annotations

import runpy
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

STORE = runpy.run_path(
    str(Path(__file__).resolve().parent / "profrod_sovereign_agent_ch04_state_store_learner.py")
)
StateStore, StoreError = STORE["StateStore"], STORE["StoreError"]


class TransitionError(StoreError):
    """A work item asked to move between states the state machine does not allow."""


# The work state machine: the only transitions a work item may make.
TRANSITIONS = {("pending", "running"), ("running", "finished")}

WORK_MIGRATIONS: dict[int, tuple[str, ...]] = {
    1: (
        "CREATE TABLE work ("
        " work_id INTEGER PRIMARY KEY,"
        " source_id TEXT NOT NULL UNIQUE,"
        " session_id TEXT NOT NULL,"
        " text TEXT NOT NULL,"
        " state TEXT NOT NULL CHECK (state IN ('pending', 'running', 'finished')),"
        " worker_id TEXT)",
        "CREATE TABLE reports ("
        " report_id TEXT PRIMARY KEY,"
        " work_id INTEGER NOT NULL REFERENCES work (work_id),"
        " generation INTEGER NOT NULL,"
        " body TEXT NOT NULL,"
        " delivery TEXT NOT NULL"
        " CHECK (delivery IN ('pending', 'sending', 'confirmed', 'unknown')),"
        " receipt TEXT,"
        " UNIQUE (work_id, generation))",
        # The database refuses a transition the state machine does not name, whoever asks.
        "CREATE TRIGGER work_transitions BEFORE UPDATE OF state ON work"
        " WHEN NOT ((OLD.state = 'pending' AND NEW.state = 'running')"
        " OR (OLD.state = 'running' AND NEW.state = 'finished'))"
        " BEGIN SELECT RAISE(ABORT, 'transition not allowed'); END",
        "CREATE TRIGGER report_body_fixed BEFORE UPDATE OF body, work_id, generation ON reports"
        " BEGIN SELECT RAISE(ABORT, 'a report never changes what it says'); END",
    ),
}


@dataclass(frozen=True)
class Assignment:
    work_id: int
    session_id: str
    text: str
    worker_id: str


class TransportUncertainError(Exception):
    """The send may have been accepted: the reply was lost."""


class WorkQueue:
    """Admit, claim and finish work; keep and send its reports. One worker at a time here."""

    def __init__(self, store: StateStore, *, capacity: int = 10) -> None:
        self.store, self.capacity = store, capacity
        store.migrate("work", WORK_MIGRATIONS)

    def admit(self, source_id: str, session_id: str, text: str) -> str:
        """ "accepted", "duplicate", "conflict" or "refused". Refused work is never stored."""
        with self.store.immediate() as db:
            row = db.execute(
                "SELECT session_id, text FROM work WHERE source_id = ?", (source_id,)
            ).fetchone()
            if row is not None:
                return "duplicate" if row == (session_id, text) else "conflict"
            (open_work,) = db.execute(
                "SELECT COUNT(*) FROM work WHERE state IN ('pending', 'running')"
            ).fetchone()
            if open_work >= self.capacity:
                return "refused"
            db.execute(
                "INSERT INTO work (source_id, session_id, text, state) VALUES (?, ?, ?, 'pending')",
                (source_id, session_id, text),
            )
        return "accepted"

    def claim(self, worker_id: str) -> Assignment | None:
        """Take the oldest pending item, or None. The claim commits before any work starts."""
        with self.store.immediate() as db:
            row = db.execute(
                "SELECT work_id, session_id, text FROM work WHERE state = 'pending'"
                " ORDER BY work_id LIMIT 1"
            ).fetchone()
            if row is None:
                return None
            db.execute(
                "UPDATE work SET state = 'running', worker_id = ? WHERE work_id = ?",
                (worker_id, row[0]),
            )
        return Assignment(row[0], row[1], row[2], worker_id)

    def finish(
        self,
        assignment: Assignment,
        body: str,
        *,
        between: Callable[[], None] | None = None,
    ) -> str:
        """Mark the work finished and create its report in one transaction; return the report id."""
        with self.store.immediate() as db:
            row = db.execute(
                "SELECT state, worker_id FROM work WHERE work_id = ?", (assignment.work_id,)
            ).fetchone()
            if row != ("running", assignment.worker_id):
                raise TransitionError(f"work {assignment.work_id} is not running for this worker")
            db.execute(
                "UPDATE work SET state = 'finished' WHERE work_id = ?", (assignment.work_id,)
            )
            if between is not None:
                between()
            (generation,) = db.execute(
                "SELECT COUNT(*) + 1 FROM reports WHERE work_id = ?", (assignment.work_id,)
            ).fetchone()
            report_id = f"r{assignment.work_id}.{generation}"
            db.execute(
                "INSERT INTO reports (report_id, work_id, generation, body, delivery)"
                " VALUES (?, ?, ?, ?, 'pending')",
                (report_id, assignment.work_id, generation, body),
            )
        return report_id

    def send_one(self, transport: Callable[[str, str], str]) -> tuple[str, str] | None:
        """Send the oldest pending report once. Returns (report_id, outcome), or None if none.

        The report is marked "sending" and committed before the network call, which never runs
        inside a transaction. A receipt confirms it; a lost reply makes it "unknown", and an
        unknown report is never picked up again by this method.
        """
        with self.store.immediate() as db:
            row = db.execute(
                "SELECT report_id, body FROM reports WHERE delivery = 'pending'"
                " ORDER BY work_id, generation LIMIT 1"
            ).fetchone()
            if row is None:
                return None
            db.execute("UPDATE reports SET delivery = 'sending' WHERE report_id = ?", (row[0],))
        try:
            receipt = transport(row[0], row[1])
        except TransportUncertainError:
            outcome, receipt = "unknown", None
        else:
            outcome = "confirmed"
        with self.store.immediate() as db:
            db.execute(
                "UPDATE reports SET delivery = ?, receipt = ? WHERE report_id = ?",
                (outcome, receipt, row[0]),
            )
        return row[0], outcome


def work_once(queue: WorkQueue, worker_id: str, run: Callable[[str], str]) -> str | None:
    """Claim one item, run it through ``run`` (the Chapter 3 loop), and finish it with a report."""
    assignment = queue.claim(worker_id)
    if assignment is None:
        return None
    return queue.finish(assignment, run(assignment.text))


class FakeService:
    """A controlled messaging service with its own record of accepted sends.

    ``lose_reply`` makes it accept a send and then drop the reply. ``idempotent`` makes it accept
    each report identity once, so a repeated send of the same report delivers nothing new.
    """

    def __init__(self, *, idempotent: bool = False) -> None:
        self.accepted: list[str] = []
        self.idempotent = idempotent
        self.lose_reply = False

    def __call__(self, report_id: str, body: str) -> str:
        if not (self.idempotent and report_id in self.accepted):
            self.accepted.append(report_id)
        if self.lose_reply:
            raise TransportUncertainError("accepted, but the reply was lost")
        return f"receipt-{len(self.accepted)}"
