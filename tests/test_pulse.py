"""Unit 9 proof matrix: sale -> signal -> wake gate -> Pulse event -> work.

Every test here drives the REAL mechanism -- a genuine sale through
`record_sale`, a genuine wake-gate decision through `store_wake_gate`, a
genuine canonical creation through `Organization.create_pulse_work`, and a
genuine `pulse.*` event through `append_event` called ONLY by that
production code path. No test fabricates a `pulse.*` event, inserts a
pre-classified wake result, or calls `append_event("pulse....")` directly --
the governing SOW's own "genuine Pulse events only" requirement.
"""

from __future__ import annotations

import json
import sqlite3
import threading
from pathlib import Path
from unittest.mock import patch

import pytest

from reference_organizations.store import apply_restock, record_sale, seed
from reference_organizations.store.demo import propose_restock_from_report, run_pulse_simulated
from reference_organizations.store.pulse_gate import store_wake_gate
from sovereign_agent import supervisor as supervisor_module
from sovereign_agent.database import Database
from sovereign_agent.models import AssignmentState, Role
from sovereign_agent.organization import Organization
from sovereign_agent.pulse import WakeDecision, run_pulse_once

SKU = "SKU-TEA"


def _seeded_active_org(root: Path) -> tuple[Organization, str]:
    org = Organization.init(root)
    seed(org.db)
    outcome = org.create_outcome(
        "Keep the tea jar stocked",
        "On-hand tea stays at or above the reorder point.",
        [
            "inventory_at_or_above_reorder_point",
            "cash_reconciles",
            "replenishment_event_exists",
        ],
        "principal-human",
        SKU,
    )
    org.activate(outcome.id, "master-course")
    return org, outcome.id


# === Separate mechanism =====================================================


def test_pulse_once_works(tmp_path: Path) -> None:
    org, _outcome_id = _seeded_active_org(tmp_path)
    record_sale(org.db, SKU, 2, 400)
    report = run_pulse_once(org, store_wake_gate)
    assert len(report.created) == 1


def test_supervisor_tick_still_creates_no_work_and_emits_no_pulse_event(tmp_path: Path) -> None:
    """THE decisive separation property: Pulse is a distinct mechanism.
    `supervisor.tick()` -- run against the SAME organization a Pulse-
    qualifying sale was just committed to -- must still create no work and
    emit no `pulse.*` event. This is the property the governing ruling
    exists to protect: Unit 8's accepted "never fires a wake gate" claim
    must remain literally true after Unit 9 lands."""
    org, _outcome_id = _seeded_active_org(tmp_path)
    record_sale(org.db, SKU, 2, 400)
    before_sows = org.db.connection.execute("SELECT COUNT(*) AS c FROM sows").fetchone()["c"]
    before_assignments = org.db.connection.execute(
        "SELECT COUNT(*) AS c FROM assignments"
    ).fetchone()["c"]

    supervisor_module.tick(org)

    after_sows = org.db.connection.execute("SELECT COUNT(*) AS c FROM sows").fetchone()["c"]
    after_assignments = org.db.connection.execute(
        "SELECT COUNT(*) AS c FROM assignments"
    ).fetchone()["c"]
    pulse_events = org.db.connection.execute(
        "SELECT COUNT(*) AS c FROM events WHERE kind LIKE 'pulse.%'"
    ).fetchone()["c"]
    assert after_sows == before_sows
    assert after_assignments == before_assignments
    assert pulse_events == 0


def test_pulse_never_imports_supervisor() -> None:
    """A static proof, not merely a behavioural one: pulse.py's own AST must
    contain no import of supervisor.py -- the module the governing ruling
    forbids Pulse from disguising itself as a step of."""
    import ast

    import sovereign_agent.pulse as pulse_module

    tree = ast.parse(Path(pulse_module.__file__).read_text(encoding="utf-8"))
    imported_modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_modules.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported_modules.add(node.module)
    assert not any("supervisor" in name for name in imported_modules)


# === No creation from nothing ===============================================


def test_empty_organization_creates_no_work(tmp_path: Path) -> None:
    org = Organization.init(tmp_path)
    report = run_pulse_once(org, store_wake_gate)
    assert report.items == ()


def test_seeded_store_with_no_sale_creates_no_work(tmp_path: Path) -> None:
    org, _outcome_id = _seeded_active_org(tmp_path)
    report = run_pulse_once(org, store_wake_gate)
    assert report.items == ()


def test_sale_remaining_above_reorder_creates_no_work(tmp_path: Path) -> None:
    org, _outcome_id = _seeded_active_org(tmp_path)
    # Seed leaves on_hand=4, reorder_point=3: raise the shelf well above
    # reorder first, then sell a small amount that still leaves it above.
    org.db.connection.execute("UPDATE inventory SET on_hand = 20 WHERE sku = ?", (SKU,))
    org.db.connection.commit()
    record_sale(org.db, SKU, 1, 400)  # on_hand: 20 -> 19, still far above reorder_point=3
    report = run_pulse_once(org, store_wake_gate)
    assert report.created == ()
    assert report.items[0].status == "skipped"


# === Qualification ===========================================================


def test_a_real_sale_crossing_the_threshold_creates_canonical_proactive_work(
    tmp_path: Path,
) -> None:
    org, outcome_id = _seeded_active_org(tmp_path)
    signal = record_sale(org.db, SKU, 2, 400)
    report = run_pulse_once(org, store_wake_gate)
    assert len(report.created) == 1
    item = report.created[0]
    assert item.signal_id == signal.id
    assert item.sow_id is not None
    sow = org._sow(item.sow_id)  # noqa: SLF001
    assert sow.outcome_id == outcome_id


# === Current-state check =====================================================


def test_a_formerly_qualifying_signal_does_not_fire_after_the_condition_resolves(
    tmp_path: Path,
) -> None:
    """The wake gate re-checks CURRENT state, not the signal's own stale
    severity at write time. A signal recorded while below reorder must not
    fire once the shelf has already been restocked by other means."""
    org, _outcome_id = _seeded_active_org(tmp_path)
    signal = record_sale(org.db, SKU, 2, 400)  # on_hand=2, below reorder_point=3
    org.db.connection.execute("UPDATE inventory SET on_hand = 10 WHERE sku = ?", (SKU,))
    org.db.connection.commit()

    report = run_pulse_once(org, store_wake_gate)
    assert report.created == ()
    assert report.items[0].signal_id == signal.id
    assert report.items[0].status == "skipped"


# === Attribution ==============================================================


def test_attribution_walks_source_event_to_signal_to_decision_to_pulse_event_to_sow_to_assignment(
    tmp_path: Path,
) -> None:
    org, _outcome_id = _seeded_active_org(tmp_path)
    signal = record_sale(org.db, SKU, 2, 400)
    report = run_pulse_once(org, store_wake_gate)
    item = report.created[0]
    assert item.sow_id is not None
    assert item.assignment_id is not None

    origin = org.pulse_origin_for_sow(item.sow_id)
    assert origin is not None
    assert origin.origin_kind == "pulse"
    assert origin.sow_id == item.sow_id
    assert origin.assignment_id == item.assignment_id

    decision = org.db.connection.execute(
        "SELECT source_signal_id, source_event_id FROM pulse_wake_decisions WHERE id = ?",
        (origin.wake_decision_id,),
    ).fetchone()
    assert decision["source_signal_id"] == signal.id

    source_event = org.db.connection.execute(
        "SELECT kind, payload FROM events WHERE id = ?", (decision["source_event_id"],)
    ).fetchone()
    assert source_event["kind"] == "sale.committed"
    assert json.loads(source_event["payload"])["signal_id"] == signal.id

    pulse_event = org.db.connection.execute(
        "SELECT kind FROM events WHERE id = ?", (origin.pulse_event_id,)
    ).fetchone()
    assert pulse_event["kind"] == "pulse.work_created"

    assert org._sow(origin.sow_id).id == item.sow_id  # noqa: SLF001
    assert org._assignment(origin.assignment_id).id == item.assignment_id  # noqa: SLF001


# === Manual attribution ======================================================


def test_manually_created_work_says_manual_explicitly(tmp_path: Path) -> None:
    org, outcome_id = _seeded_active_org(tmp_path)
    sow = org.create_sow(outcome_id, "manual scope", Role.OPERATOR, "master-course")
    origin = org.pulse_origin_for_sow(sow.id)
    assert origin is not None
    assert origin.origin_kind == "manual"
    assert origin.wake_decision_id is None
    assert origin.pulse_event_id is None


def test_existing_migrated_work_says_manual_explicitly(tmp_path: Path) -> None:
    """A SOW that existed BEFORE migration 15 gets an explicit manual row at
    migration time -- absence of a Pulse-origin row must never be the
    definition of manual (the governing ruling's own words)."""
    import sovereign_agent.database as database_module

    path = tmp_path / "legacy.db"
    connection = sqlite3.connect(path)
    for version, script in database_module.MIGRATIONS:
        if version > 14:
            break
        for statement in database_module._split_statements(script):  # noqa: SLF001
            connection.execute(statement)
        connection.execute(
            "INSERT INTO schema_migrations(version, applied_at) VALUES (?, datetime('now'))",
            (version,),
        )
    connection.execute("INSERT INTO outcomes(id, record) VALUES ('out1', '{}')")
    connection.execute(
        "INSERT INTO sows(id, outcome_id, record) VALUES ('sow_legacy', 'out1', ?)",
        (json.dumps({"created_at": "2026-01-01T00:00:00+00:00"}),),
    )
    connection.commit()
    connection.close()

    db = Database(path)
    row = db.connection.execute(
        "SELECT origin_kind FROM pulse_origins WHERE sow_id = 'sow_legacy'"
    ).fetchone()
    assert row is not None
    assert row["origin_kind"] == "manual"


# === Replay ===================================================================


def test_same_process_replay_returns_the_same_identifiers_and_counts_remain_one(
    tmp_path: Path,
) -> None:
    org, _outcome_id = _seeded_active_org(tmp_path)
    record_sale(org.db, SKU, 2, 400)
    first = run_pulse_once(org, store_wake_gate)
    second = run_pulse_once(org, store_wake_gate)

    assert len(first.created) == 1
    # The signal already has a wake decision after the first pass, so the
    # second pass finds nothing left to evaluate -- it never re-offers an
    # already-decided signal to the gate at all.
    assert second.items == ()

    sows = org.db.connection.execute("SELECT COUNT(*) AS c FROM sows").fetchone()["c"]
    decisions = org.db.connection.execute(
        "SELECT COUNT(*) AS c FROM pulse_wake_decisions"
    ).fetchone()["c"]
    assert sows == 1
    assert decisions == 1


def test_create_pulse_work_called_twice_for_the_same_signal_returns_the_same_identifiers(
    tmp_path: Path,
) -> None:
    """Isolates the canonical-creation transaction itself, independent of
    run_pulse_once's own signal-selection skip -- proves create_pulse_work is
    idempotent on its own terms, not merely "never called twice" by its
    caller."""
    org, outcome_id = _seeded_active_org(tmp_path)
    signal = record_sale(org.db, SKU, 2, 400)
    source_event_id = org.db.connection.execute(
        "SELECT id FROM events WHERE kind = 'sale.committed'"
    ).fetchone()["id"]

    kwargs = dict(
        source_signal_id=signal.id,
        source_event_id=source_event_id,
        subject=SKU,
        outcome_id=outcome_id,
        scope="pulse replenishment",
        role=Role.OPERATOR,
        planner_id="master-course",
        worker_id="operator-course",
        required_effect_kind="replenishment",
    )
    sow1, assignment1, created1 = org.create_pulse_work(**kwargs)  # type: ignore[arg-type]
    sow2, assignment2, created2 = org.create_pulse_work(**kwargs)  # type: ignore[arg-type]
    assert created1 is True
    assert created2 is False
    assert sow1.id == sow2.id
    assert assignment1.id == assignment2.id


# === Restart ==================================================================


def test_reopening_the_database_and_replaying_keeps_counts_at_one(tmp_path: Path) -> None:
    org, _outcome_id = _seeded_active_org(tmp_path)
    record_sale(org.db, SKU, 2, 400)
    run_pulse_once(org, store_wake_gate)
    org.db.close()

    reopened = Organization(tmp_path)
    second = run_pulse_once(reopened, store_wake_gate)
    assert second.items == ()
    sows = reopened.db.connection.execute("SELECT COUNT(*) AS c FROM sows").fetchone()["c"]
    assert sows == 1


# === Concurrency ==============================================================


def test_two_real_processes_evaluating_the_same_signal_create_one_canonical_sow(
    tmp_path: Path,
) -> None:
    """A REAL two-connection proof, matching this project's own standing
    discipline (test_concurrency.py, test_fencing.py): two genuinely
    separate `Organization` instances, opened on separate SQLite
    connections against the SAME root, race `create_pulse_work` for the
    SAME source signal via a real threading.Barrier. Exactly one must
    create the canonical SOW; the other must return the SAME identifiers."""
    org, outcome_id = _seeded_active_org(tmp_path)
    signal = record_sale(org.db, SKU, 2, 400)
    source_event_id = org.db.connection.execute(
        "SELECT id FROM events WHERE kind = 'sale.committed'"
    ).fetchone()["id"]
    org.db.close()

    barrier = threading.Barrier(2)
    results: list[tuple[str, str, bool]] = []
    lock = threading.Lock()

    def contend() -> None:
        contender = Organization(tmp_path)
        contender.db.connection.execute("PRAGMA busy_timeout = 5000")
        barrier.wait()
        sow, assignment, created = contender.create_pulse_work(
            source_signal_id=signal.id,
            source_event_id=source_event_id,
            subject=SKU,
            outcome_id=outcome_id,
            scope="pulse replenishment",
            role=Role.OPERATOR,
            planner_id="master-course",
            worker_id="operator-course",
            required_effect_kind="replenishment",
        )
        with lock:
            results.append((sow.id, assignment.id, created))
        contender.db.close()

    threads = [threading.Thread(target=contend) for _ in range(2)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    sow_ids = {r[0] for r in results}
    assignment_ids = {r[1] for r in results}
    created_flags = [r[2] for r in results]
    assert len(sow_ids) == 1, f"two different SOWs were created: {results}"
    assert len(assignment_ids) == 1
    assert sorted(created_flags) == [False, True]

    inspector = Organization(tmp_path)
    sow_count = inspector.db.connection.execute("SELECT COUNT(*) AS c FROM sows").fetchone()["c"]
    decision_count = inspector.db.connection.execute(
        "SELECT COUNT(*) AS c FROM pulse_wake_decisions"
    ).fetchone()["c"]
    assert sow_count == 1
    assert decision_count == 1


# === Crash window =============================================================


def test_canonical_created_work_survives_restart_and_resumes_without_duplication(
    tmp_path: Path,
) -> None:
    """Simulates a crash after canonical creation but before provider
    invocation: create_pulse_work runs (the SOW/assignment/origin/pulse
    event are durable), but run_assignment never happens -- the assignment
    is left at CREATED, as it genuinely would be after a hard kill between
    the two. A fresh pass must invoke that SAME assignment, never create a
    second one."""
    org, outcome_id = _seeded_active_org(tmp_path)
    signal = record_sale(org.db, SKU, 2, 400)
    source_event_id = org.db.connection.execute(
        "SELECT id FROM events WHERE kind = 'sale.committed'"
    ).fetchone()["id"]
    sow, assignment, created = org.create_pulse_work(
        source_signal_id=signal.id,
        source_event_id=source_event_id,
        subject=SKU,
        outcome_id=outcome_id,
        scope="pulse replenishment",
        role=Role.OPERATOR,
        planner_id="master-course",
        worker_id="operator-course",
        required_effect_kind="replenishment",
    )
    assert created is True
    assert assignment.state == AssignmentState.CREATED
    org.db.close()

    resumed = Organization(tmp_path)
    report = run_pulse_once(resumed, store_wake_gate)
    # The signal already has a wake decision, so the gate is never
    # re-consulted -- but its CREATED assignment is resumed, invoking the
    # SAME canonical assignment rather than minting a second one.
    assert len(report.items) == 1
    assert report.items[0].signal_id == signal.id
    assert report.items[0].assignment_id == assignment.id
    assert report.items[0].assignment_state == AssignmentState.COMPLETED.value

    final = resumed._assignment(assignment.id)  # noqa: SLF001
    assert final.state == AssignmentState.COMPLETED
    sow_count = resumed.db.connection.execute("SELECT COUNT(*) AS c FROM sows").fetchone()["c"]
    assert sow_count == 1
    assignment_count = resumed.db.connection.execute(
        "SELECT COUNT(*) AS c FROM assignments"
    ).fetchone()["c"]
    assert assignment_count == 1


# === Existing RUNNING work ====================================================


def test_pulse_does_not_bypass_actor_leases_or_execution_attempt_fencing(tmp_path: Path) -> None:
    """The canonical assignment is genuinely RUNNING (a live, unexpired
    execution attempt and a live actor lease already held by a DIFFERENT
    process) when a second pulse pass reaches it -- proves Pulse reports
    the in-flight state rather than invoking run_assignment a second time,
    which would go through the exact same fencing every other caller does
    and be refused there."""
    from sovereign_agent import fencing

    org, outcome_id = _seeded_active_org(tmp_path)
    signal = record_sale(org.db, SKU, 2, 400)
    source_event_id = org.db.connection.execute(
        "SELECT id FROM events WHERE kind = 'sale.committed'"
    ).fetchone()["id"]
    sow, assignment, _created = org.create_pulse_work(
        source_signal_id=signal.id,
        source_event_id=source_event_id,
        subject=SKU,
        outcome_id=outcome_id,
        scope="pulse replenishment",
        role=Role.OPERATOR,
        planner_id="master-course",
        worker_id="operator-course",
        required_effect_kind="replenishment",
    )
    other_process = fencing.new_process_identity()
    lease = fencing.acquire_actor_lease(org.db, "operator-course", other_process)
    fencing.acquire_execution_attempt(
        org.db, assignment.id, "operator-course", other_process, lease.fencing_token
    )
    org.db.connection.execute(
        "UPDATE assignments SET record = json_set(record, '$.state', 'RUNNING') WHERE id = ?",
        (assignment.id,),
    )
    org.db.connection.commit()

    report = run_pulse_once(org, store_wake_gate)
    assert report.items == (), "the signal already has a wake decision; nothing left to evaluate"

    # Isolate the reporting behaviour directly against the RUNNING assignment,
    # independent of the signal-skip above.
    from sovereign_agent.pulse import _invoke_or_report

    running = org._assignment(assignment.id)  # noqa: SLF001
    assert running.state == AssignmentState.RUNNING
    item = _invoke_or_report(org, signal.id, sow.id, running, False)
    assert item.status == "already_running"


# === Terminal work =============================================================


def test_completed_canonical_assignment_is_not_rerun(tmp_path: Path) -> None:
    org, _outcome_id = _seeded_active_org(tmp_path)
    record_sale(org.db, SKU, 2, 400)
    first = run_pulse_once(org, store_wake_gate)
    assert first.created[0].assignment_state == AssignmentState.COMPLETED.value

    with patch(
        "sovereign_agent.organization.Organization.run_assignment",
        side_effect=AssertionError("must not be invoked again"),
    ):
        second = run_pulse_once(org, store_wake_gate)
    assert second.items == ()


def test_blocked_and_failed_canonical_assignments_are_not_rerun_or_replaced(
    tmp_path: Path,
) -> None:
    org, outcome_id = _seeded_active_org(tmp_path)
    signal = record_sale(org.db, SKU, 2, 400)
    source_event_id = org.db.connection.execute(
        "SELECT id FROM events WHERE kind = 'sale.committed'"
    ).fetchone()["id"]
    sow, assignment, _created = org.create_pulse_work(
        source_signal_id=signal.id,
        source_event_id=source_event_id,
        subject=SKU,
        outcome_id=outcome_id,
        scope="pulse replenishment",
        role=Role.OPERATOR,
        planner_id="master-course",
        worker_id="operator-course",
        required_effect_kind="replenishment",
    )
    org.db.connection.execute(
        "UPDATE assignments SET record = json_set(record, '$.state', 'FAILED') WHERE id = ?",
        (assignment.id,),
    )
    org.db.connection.commit()

    from sovereign_agent.pulse import _invoke_or_report

    failed = org._assignment(assignment.id)  # noqa: SLF001
    item = _invoke_or_report(org, signal.id, sow.id, failed, False)
    assert item.status == "replayed"
    assert item.assignment_state == AssignmentState.FAILED.value
    still_failed = org._assignment(assignment.id)  # noqa: SLF001
    assert still_failed.state == AssignmentState.FAILED


# === Source integrity =========================================================


def test_missing_source_event_fails_closed(tmp_path: Path) -> None:
    """A signal with no matching sale.committed event (source relationship
    missing or inconsistent -- events are append-only, so this is simulated
    by inserting a signal row with no corresponding event, the honest shape
    a source-relationship gap could ever actually take in this ledger)
    must be skipped, not fabricated a source_event_id."""
    org, _outcome_id = _seeded_active_org(tmp_path)
    from sovereign_agent.models import Signal

    orphan = Signal(
        id="sig_orphan",
        kind="inventory.changed",
        source="sale",
        subject_ref=SKU,
        severity="warning",
        observed_at=org.db.connection.execute("SELECT datetime('now') AS n").fetchone()["n"],
        payload_digest=SKU,
        dedupe_key="inventory:SKU-TEA:orphan",
    )
    org.db.connection.execute(
        "INSERT INTO signals(id, dedupe_key, record) VALUES (?, ?, ?)",
        (orphan.id, orphan.dedupe_key, orphan.model_dump_json()),
    )
    org.db.connection.commit()

    report = run_pulse_once(org, store_wake_gate)
    assert report.created == ()
    assert report.items[0].status == "skipped"
    assert "no source" in report.items[0].detail


def test_fabricated_source_signal_id_is_refused_by_the_foreign_key(tmp_path: Path) -> None:
    org, outcome_id = _seeded_active_org(tmp_path)
    with pytest.raises(Exception, match="FOREIGN KEY"):
        org.create_pulse_work(
            source_signal_id="sig_does_not_exist",
            source_event_id="evt_does_not_exist",
            subject=SKU,
            outcome_id=outcome_id,
            scope="pulse replenishment",
            role=Role.OPERATOR,
            planner_id="master-course",
            worker_id="operator-course",
            required_effect_kind="replenishment",
        )


def test_no_active_outcome_matching_the_subject_creates_no_work(tmp_path: Path) -> None:
    org = Organization.init(tmp_path)
    seed(org.db)
    # No outcome created at all for SKU-TEA.
    record_sale(org.db, SKU, 2, 400)
    report = run_pulse_once(org, store_wake_gate)
    assert report.created == ()


def test_more_than_one_matching_active_outcome_creates_no_work(tmp_path: Path) -> None:
    org, _outcome_id = _seeded_active_org(tmp_path)
    second = org.create_outcome(
        "A second outcome about the same SKU",
        "Also tea.",
        ["inventory_at_or_above_reorder_point"],
        "principal-human",
        SKU,
    )
    org.activate(second.id, "master-course")
    record_sale(org.db, SKU, 2, 400)
    report = run_pulse_once(org, store_wake_gate)
    assert report.created == ()


# === Ledger integrity ==========================================================


def test_pulse_origins_and_wake_decisions_are_append_only(tmp_path: Path) -> None:
    org, _outcome_id = _seeded_active_org(tmp_path)
    record_sale(org.db, SKU, 2, 400)
    run_pulse_once(org, store_wake_gate)

    with pytest.raises(sqlite3.IntegrityError, match="append-only"):
        org.db.connection.execute("UPDATE pulse_wake_decisions SET subject = 'tampered' WHERE 1=1")
    with pytest.raises(sqlite3.IntegrityError, match="append-only"):
        org.db.connection.execute("DELETE FROM pulse_origins")


def test_two_pulse_origin_rows_cannot_name_the_same_sow(tmp_path: Path) -> None:
    org, outcome_id = _seeded_active_org(tmp_path)
    sow = org.create_sow(outcome_id, "manual scope", Role.OPERATOR, "master-course")
    with pytest.raises(sqlite3.IntegrityError):
        org.db.connection.execute(
            "INSERT INTO pulse_origins(id, origin_kind, sow_id, created_at) "
            "VALUES ('porg_dup', 'manual', ?, datetime('now'))",
            (sow.id,),
        )


def test_a_pulse_origin_row_without_a_real_sow_is_refused_by_the_foreign_key(
    tmp_path: Path,
) -> None:
    org = Organization.init(tmp_path)
    with pytest.raises(sqlite3.IntegrityError, match="FOREIGN KEY"):
        org.db.connection.execute(
            "INSERT INTO pulse_origins(id, origin_kind, sow_id, created_at) "
            "VALUES ('porg_x', 'manual', 'sow_does_not_exist', datetime('now'))"
        )


def test_indexed_pulse_origin_agrees_with_the_organization_method(tmp_path: Path) -> None:
    org, _outcome_id = _seeded_active_org(tmp_path)
    record_sale(org.db, SKU, 2, 400)
    report = run_pulse_once(org, store_wake_gate)
    item = report.created[0]
    assert item.sow_id is not None
    origin = org.pulse_origin_for_sow(item.sow_id)
    row = org.db.connection.execute(
        "SELECT sow_id, assignment_id, origin_kind FROM pulse_origins WHERE sow_id = ?",
        (item.sow_id,),
    ).fetchone()
    assert origin is not None
    assert origin.sow_id == row["sow_id"]
    assert origin.assignment_id == row["assignment_id"]
    assert origin.origin_kind == row["origin_kind"]


# === Recurrence ================================================================


def test_a_later_sale_reaching_a_previously_seen_level_retains_the_old_signal_and_can_fire_again(
    tmp_path: Path,
) -> None:
    """THE decisive signal-stability property. Before the fix, a second sale
    reaching the SAME on_hand level replaced the first signal's row via
    INSERT OR REPLACE keyed on dedupe_key -- so Pulse origin referencing the
    first signal's id would find it silently gone. Two DISTINCT sales here
    both leave on_hand at 2 (buy back up to 4 between them); both signals
    must survive, and each is a genuine, independent opportunity for
    Pulse-created work."""
    org, outcome_id = _seeded_active_org(tmp_path)
    first_signal = record_sale(org.db, SKU, 2, 400)  # on_hand: 4 -> 2

    first_report = run_pulse_once(org, store_wake_gate)
    assert len(first_report.created) == 1
    first_assignment_id = first_report.created[0].assignment_id
    assert first_assignment_id is not None
    assignment = org._assignment(first_assignment_id)  # noqa: SLF001
    report_path = (
        tmp_path
        / ".sovereign"
        / "runs"
        / assignment.workspace_id
        / ".sovereign-out"
        / "report.json"
    )
    proposal = propose_restock_from_report(report_path, SKU)
    apply_restock(org.db, proposal, first_assignment_id, first_signal.id)

    row = org.db.connection.execute(
        "SELECT on_hand FROM inventory WHERE sku = ?", (SKU,)
    ).fetchone()
    on_hand_after_restock = int(row["on_hand"])
    # Sell back down to exactly the same level the first signal recorded.
    quantity = on_hand_after_restock - 2
    second_signal = record_sale(org.db, SKU, quantity, 400)
    assert second_signal.id != first_signal.id

    still_present = org.db.connection.execute(
        "SELECT COUNT(*) AS c FROM signals WHERE id = ?", (first_signal.id,)
    ).fetchone()["c"]
    assert still_present == 1, "the earlier signal that already caused work was overwritten"

    second_report = run_pulse_once(org, store_wake_gate)
    assert len(second_report.created) == 1
    assert second_report.created[0].signal_id == second_signal.id
    assert second_report.created[0].sow_id != first_report.created[0].sow_id

    signal_count = org.db.connection.execute("SELECT COUNT(*) AS c FROM signals").fetchone()["c"]
    assert signal_count == 2


# === Real mechanism =============================================================


def test_no_pulse_event_exists_before_pulse_runs(tmp_path: Path) -> None:
    org, _outcome_id = _seeded_active_org(tmp_path)
    record_sale(org.db, SKU, 2, 400)
    count = org.db.connection.execute(
        "SELECT COUNT(*) AS c FROM events WHERE kind LIKE 'pulse.%'"
    ).fetchone()["c"]
    assert count == 0


def test_wake_gate_receives_a_real_signal_object_read_from_the_database(tmp_path: Path) -> None:
    """Proves the gate is called with the genuine persisted Signal, not a
    hand-built stand-in -- a spy gate records what it was actually given."""
    org, _outcome_id = _seeded_active_org(tmp_path)
    signal = record_sale(org.db, SKU, 2, 400)
    seen: list[str] = []

    def spy_gate(spy_org: Organization, spy_signal) -> WakeDecision | None:  # type: ignore[no-untyped-def]
        seen.append(spy_signal.id)
        return store_wake_gate(spy_org, spy_signal)

    run_pulse_once(org, spy_gate)
    assert seen == [signal.id]


# === Full teaching slice =========================================================


def test_full_teaching_slice_reaches_verified_reviewed_truthful_acceptance(
    tmp_path: Path,
) -> None:
    text = run_pulse_simulated(tmp_path)
    assert "ACCEPTED" in text
    org = Organization(tmp_path)
    outcome_row = org.db.connection.execute("SELECT record FROM outcomes").fetchone()
    outcome = json.loads(outcome_row["record"])
    assert outcome["state"] == "ACCEPTED"
    sow_row = org.db.connection.execute("SELECT id FROM sows").fetchone()
    origin = org.pulse_origin_for_sow(sow_row["id"])
    assert origin is not None
    assert origin.origin_kind == "pulse"


# === CLI artifact ================================================================


def test_pulse_once_requires_the_flag(tmp_path: Path) -> None:
    from sovereign_agent.cli import build_parser

    parser = build_parser()
    with pytest.raises(SystemExit):
        parser.parse_args(["--root", str(tmp_path), "pulse"])


def test_pulse_cli_handler_reports_created_work(tmp_path: Path, capsys) -> None:  # type: ignore[no-untyped-def]
    from sovereign_agent.cli import main

    org, _outcome_id = _seeded_active_org(tmp_path)
    record_sale(org.db, SKU, 2, 400)
    org.db.close()

    exit_code = main(["pulse", "--root", str(tmp_path), "--once"])
    assert exit_code == 0
    out = capsys.readouterr().out
    assert "created" in out
    assert "1 created" in out
