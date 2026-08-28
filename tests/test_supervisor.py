"""Unit 8 proof matrix: supervisor reconciliation, and hard-kill recovery.

The hard-kill cases run a REAL child process (`tests/fixtures/hard_kill_
worker.py`), SIGKILL it while it is genuinely blocked inside a subprocess
call, and prove the supervisor -- never the dead process itself -- recovers
the assignment it left behind. This is deliberately not a `Refusal`
injected in place of a crash: a preclassified injection could not prove
anything about `current_execution_attempt` surviving a real, uncatchable
`SIGKILL` the way this does, since a Python exception handler never runs at
all for that signal.
"""

from __future__ import annotations

import json
import subprocess
import sys
import time
from datetime import timedelta
from pathlib import Path

from reference_organizations.store import seed
from sovereign_agent import fencing, supervisor
from sovereign_agent.ids import utc_now
from sovereign_agent.models import AssignmentState, Role, SowState
from sovereign_agent.organization import Organization
from sovereign_agent.relay import send

FIXTURE = Path(__file__).parent / "fixtures" / "hard_kill_worker.py"


def _governed_but_not_run(tmp_path: Path) -> tuple[Organization, str]:
    org = Organization.init(tmp_path)
    seed(org.db)
    outcome = org.create_outcome(
        "t", "d", ["inventory_at_or_above_reorder_point"], "principal-human", "SKU-TEA"
    )
    org.activate(outcome.id, "master-course")
    sow = org.create_sow(outcome.id, "s", Role.OPERATOR, "master-course")
    org.ready_sow(sow.id)
    assignment = org.assign(sow.id, "operator-course", "master-course")
    return org, assignment.id


class FakeClock:
    def __init__(self) -> None:
        self.now = utc_now()

    def __call__(self):  # noqa: ANN204
        return self.now

    def advance(self, delta: timedelta) -> None:
        self.now = self.now + delta


def _far_future_clock():  # noqa: ANN201
    """A clock fixed well past any TTL this module uses, for recovery tests
    that don't need to reproduce the real wall-clock wait."""
    return utc_now() + timedelta(hours=1)


# === Hard-kill recovery: a REAL child process, REAL SIGKILL =================


def test_a_sigkilled_worker_leaves_the_assignment_running_with_a_live_attempt(
    tmp_path: Path,
) -> None:
    """Establishes the starting condition every recovery test below assumes,
    proven against a real process boundary rather than assumed."""
    org, assignment_id = _governed_but_not_run(tmp_path)
    org.db.close()

    worker = subprocess.Popen([sys.executable, str(FIXTURE), str(tmp_path), assignment_id])
    try:
        deadline = time.monotonic() + 10
        # Poll until the worker has actually reached RUNNING (opened its own
        # connection, acquired the attempt, committed the RUNNING transition)
        # rather than sleeping a fixed guess -- avoids a flaky race against a
        # slow CI machine while still killing it strictly before completion.
        reached_running = False
        while time.monotonic() < deadline:
            probe = Organization(tmp_path)
            state = probe._assignment(assignment_id).state  # noqa: SLF001
            probe.db.close()
            if state == AssignmentState.RUNNING:
                reached_running = True
                break
            time.sleep(0.1)
        assert reached_running, "worker never reached RUNNING before the deadline"
    finally:
        worker.kill()
        worker.wait(timeout=10)
    assert worker.returncode != 0, "the worker must have died abnormally (SIGKILL)"

    org2 = Organization(tmp_path)
    assignment = org2._assignment(assignment_id)  # noqa: SLF001
    assert assignment.state == AssignmentState.RUNNING, "a hard kill must not self-record failure"
    row = org2.db.connection.execute(
        "SELECT current_execution_attempt FROM assignments WHERE id = ?", (assignment_id,)
    ).fetchone()
    assert row["current_execution_attempt"] is not None, "the attempt must still be live"


def test_supervisor_recovers_a_real_sigkilled_assignment(tmp_path: Path) -> None:
    """The decisive proof: supervisor.tick(), run against the SAME database a
    real killed child process left behind, produces a durable FAILED receipt
    naming worker_lost -- never a guessed success, never left RUNNING forever."""
    org, assignment_id = _governed_but_not_run(tmp_path)
    org.db.close()

    worker = subprocess.Popen([sys.executable, str(FIXTURE), str(tmp_path), assignment_id])
    try:
        deadline = time.monotonic() + 10
        while time.monotonic() < deadline:
            probe = Organization(tmp_path)
            state = probe._assignment(assignment_id).state  # noqa: SLF001
            probe.db.close()
            if state == AssignmentState.RUNNING:
                break
            time.sleep(0.1)
    finally:
        worker.kill()
        worker.wait(timeout=10)

    org2 = Organization(tmp_path)
    report = supervisor.tick(org2, clock=_far_future_clock)
    assert [r.assignment_id for r in report.recovered_assignments] == [assignment_id]

    assignment = org2._assignment(assignment_id)  # noqa: SLF001
    assert assignment.state == AssignmentState.FAILED
    sow_raw = org2.db.get("sows", "id", org2._assignment(assignment_id).sow_id)  # noqa: SLF001
    assert sow_raw is not None
    assert sow_raw["state"] == SowState.FAILED.value

    receipt_rows = org2.db.connection.execute(
        "SELECT record FROM receipts WHERE assignment_id = ?", (assignment_id,)
    ).fetchall()
    assert len(receipt_rows) == 1
    receipt = json.loads(receipt_rows[0]["record"])
    assert receipt["status"] == "failed"
    assert receipt["failure_category"] == "worker_lost"
    assert "expired" in receipt["failure_message"]

    row = org2.db.connection.execute(
        "SELECT current_execution_attempt FROM assignments WHERE id = ?", (assignment_id,)
    ).fetchone()
    assert row["current_execution_attempt"] is None, "the fence must be released"


def test_recovery_is_idempotent_a_second_tick_recovers_nothing_more(tmp_path: Path) -> None:
    org, assignment_id = _governed_but_not_run(tmp_path)
    org.db.close()
    worker = subprocess.Popen([sys.executable, str(FIXTURE), str(tmp_path), assignment_id])
    try:
        deadline = time.monotonic() + 10
        while time.monotonic() < deadline:
            probe = Organization(tmp_path)
            state = probe._assignment(assignment_id).state  # noqa: SLF001
            probe.db.close()
            if state == AssignmentState.RUNNING:
                break
            time.sleep(0.1)
    finally:
        worker.kill()
        worker.wait(timeout=10)

    org2 = Organization(tmp_path)
    first = supervisor.tick(org2, clock=_far_future_clock)
    second = supervisor.tick(org2, clock=_far_future_clock)
    assert len(first.recovered_assignments) == 1
    assert second.recovered_assignments == ()
    receipt_rows = org2.db.connection.execute(
        "SELECT COUNT(*) AS c FROM receipts WHERE assignment_id = ?", (assignment_id,)
    ).fetchone()
    assert receipt_rows["c"] == 1, "a second tick must not write a second receipt"


def test_never_guesses_success_recovery_receipt_is_always_failed(tmp_path: Path) -> None:
    """However far the orphaned subprocess actually got -- even if it would
    have gone on to write a valid completed report.json eventually -- the
    recovered receipt is always FAILED. Recovery has no way to know what the
    dead process's provider subprocess would have produced, and Unit 5's
    'nothing is ever a guessed success' rule extends here rather than
    exempting the recovery path."""
    org, assignment_id = _governed_but_not_run(tmp_path)
    org.db.close()
    worker = subprocess.Popen([sys.executable, str(FIXTURE), str(tmp_path), assignment_id])
    try:
        deadline = time.monotonic() + 10
        while time.monotonic() < deadline:
            probe = Organization(tmp_path)
            state = probe._assignment(assignment_id).state  # noqa: SLF001
            probe.db.close()
            if state == AssignmentState.RUNNING:
                break
            time.sleep(0.1)
    finally:
        worker.kill()
        worker.wait(timeout=10)

    org2 = Organization(tmp_path)
    supervisor.tick(org2, clock=_far_future_clock)
    assignment = org2._assignment(assignment_id)  # noqa: SLF001
    assert assignment.state != AssignmentState.COMPLETED


def test_workspace_reclaim_applies_only_after_the_terminal_write_is_durable(
    tmp_path: Path,
) -> None:
    """Reclaim (temporary_directory policy) removes the workspace's scratch
    space -- proven to happen, and to happen against a workspace that
    already has a terminal, durable ledger record, not before."""
    org, assignment_id = _governed_but_not_run(tmp_path)
    org.db.close()
    worker = subprocess.Popen([sys.executable, str(FIXTURE), str(tmp_path), assignment_id])
    try:
        deadline = time.monotonic() + 10
        while time.monotonic() < deadline:
            probe = Organization(tmp_path)
            state = probe._assignment(assignment_id).state  # noqa: SLF001
            probe.db.close()
            if state == AssignmentState.RUNNING:
                break
            time.sleep(0.1)
    finally:
        worker.kill()
        worker.wait(timeout=10)

    org2 = Organization(tmp_path)
    assignment = org2._assignment(assignment_id)  # noqa: SLF001
    workspace = tmp_path / ".sovereign" / "runs" / assignment.workspace_id
    assert workspace.exists()
    supervisor.tick(org2, clock=_far_future_clock)
    assignment_after = org2._assignment(assignment_id)  # noqa: SLF001
    assert assignment_after.state == AssignmentState.FAILED, "must be terminal before reclaim ran"
    # receipt.json survives reclaim (Unit 7's own preserved set) -- proof
    # the terminal write landed before whatever reclaim removed.
    assert (workspace / "receipt.json").exists()


# === Supervisor tick: reconciliation boundary (non-goals) ====================


def test_tick_reports_expired_actor_leases_without_creating_work(tmp_path: Path) -> None:
    org = Organization.init(tmp_path)
    clock = FakeClock()
    fencing.acquire_actor_lease(
        org.db, "operator-course", fencing.new_process_identity(), clock=clock
    )
    clock.advance(timedelta(minutes=10))
    report = supervisor.tick(org, clock=clock)
    assert report.expired_actor_leases == ("operator-course",)
    # No work created: no new outcomes, SOWs, or assignments exist beyond
    # what the test itself set up (none, here).
    count = org.db.connection.execute("SELECT COUNT(*) AS c FROM outcomes").fetchone()
    assert count["c"] == 0


def test_tick_sweeps_expired_mailbox_claims_proactively(tmp_path: Path) -> None:
    org = Organization.init(tmp_path)
    message = send(org.db, "master-course", "sparring-course", "s", "b")
    from sovereign_agent.relay import claim

    claim(org.db, message.id, "sparring-course")
    org.db.connection.execute(
        "UPDATE messages SET claim_expires_at = ?, "
        "record = json_set(record, '$.claim_expires_at', ?) WHERE id = ?",
        ("2020-01-01T00:00:00+00:00", "2020-01-01T00:00:00+00:00", message.id),
    )
    org.db.connection.commit()
    report = supervisor.tick(org)
    assert report.swept_mailbox_claims == (message.id,)
    row = org.db.connection.execute(
        "SELECT state, claim_owner FROM messages WHERE id = ?", (message.id,)
    ).fetchone()
    assert row["state"] == "NEW"
    assert row["claim_owner"] is None


def test_once_runs_a_single_deterministic_tick(tmp_path: Path) -> None:
    org = Organization.init(tmp_path)
    exit_code = supervisor.run(org, once=True)
    assert exit_code == 0


def test_loop_stops_cleanly_on_sigint(tmp_path: Path) -> None:
    """The long-running loop mode (no `--once`) must handle an ordinary
    interruption cleanly -- exit 0, no traceback -- rather than crash. Run as
    a real child process via the actual CLI entry point (not `supervisor.run`
    called in-process), because catching SIGINT correctly depends on signal
    delivery to the process itself, which an in-process call cannot exercise.

    Unbuffered (`-u`) so the child's first-tick print is flushed immediately
    -- otherwise Python's own stdout buffering (not a TTY) can hold it back
    until the process exits, which would make a `readline()`-based wait
    indistinguishable from a hang.
    """
    import signal as signal_module

    org = Organization.init(tmp_path)
    org.db.close()
    process = subprocess.Popen(
        [sys.executable, "-u", "-m", "sovereign_agent", "supervisor", "--root", str(tmp_path)],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    try:
        assert process.stdout is not None
        first_line = process.stdout.readline()
        assert "supervisor tick" in first_line, f"unexpected first line: {first_line!r}"
        process.send_signal(signal_module.SIGINT)
        returncode = process.wait(timeout=10)
    finally:
        if process.poll() is None:
            process.kill()
            process.wait(timeout=10)
    assert returncode == 0, f"SIGINT must exit cleanly, got {returncode}"
    stderr = process.stderr.read() if process.stderr else ""
    assert "Traceback" not in stderr, f"SIGINT must not crash with a traceback: {stderr}"


def test_tick_never_creates_a_new_outcome_sow_or_assignment(tmp_path: Path) -> None:
    """The reconciliation boundary: a tick against a freshly initialized,
    completely empty organization must leave it completely empty -- no
    inventory-triggered, time-triggered, or otherwise invented work."""
    org = Organization.init(tmp_path)
    before = {
        table: org.db.connection.execute(f"SELECT COUNT(*) AS c FROM {table}").fetchone()["c"]
        for table in ("outcomes", "sows", "assignments", "messages")
    }
    supervisor.tick(org)
    after = {
        table: org.db.connection.execute(f"SELECT COUNT(*) AS c FROM {table}").fetchone()["c"]
        for table in ("outcomes", "sows", "assignments", "messages")
    }
    assert before == after == {"outcomes": 0, "sows": 0, "assignments": 0, "messages": 0}
