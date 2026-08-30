"""Unit 11 proof matrix: the pilot-start mechanism (governing ruling Holding 1).

Every test drives the real `start_pilot` mechanism against a real SQLite
database. Concurrency proofs use genuinely separate `Database` connections
opened against the same file -- never mocks standing in for the SQLite
boundary, matching this project's own standing discipline
(`tests/test_pulse.py`'s `test_two_real_processes_evaluating_the_same_
signal_create_one_canonical_sow` is the precedent extended here).

Nothing here invokes `start_pilot` against a real named pilot organization --
every pilot_id in this file is a disposable test fixture value, matching the
governing SOW's own scope boundary.
"""

from __future__ import annotations

import threading
from pathlib import Path

import pytest

from reference_organizations.store.pilot import active_pilot_id, start_pilot
from sovereign_agent.database import Database
from sovereign_agent.errors import Refusal
from sovereign_agent.events import append_event

PILOT_A = "pilot-disposable-a"
PILOT_B = "pilot-disposable-b"


def _start_a(db: Database) -> None:
    start_pilot(
        db,
        pilot_id=PILOT_A,
        store_org_id="store-test-org",
        pilot_profile_id="profile-test",
        evidence_namespace="ns-test-a",
    )


# === Idempotency ===============================================================


def test_fresh_start_creates_exactly_one_pilot_and_one_event(tmp_path: Path) -> None:
    db = Database(tmp_path / "org.db")
    record = start_pilot(
        db,
        pilot_id=PILOT_A,
        store_org_id="store-test-org",
        pilot_profile_id="profile-test",
        evidence_namespace="ns-test-a",
    )
    assert record.idempotent_replay is False
    assert record.pilot_id == PILOT_A

    pilots = db.connection.execute("SELECT COUNT(*) AS c FROM pilots").fetchone()["c"]
    events = db.connection.execute(
        "SELECT COUNT(*) AS c FROM events WHERE kind = 'pilot.started'"
    ).fetchone()["c"]
    assert pilots == 1
    assert events == 1
    assert active_pilot_id(db) == PILOT_A


def test_replaying_the_same_start_request_does_not_create_a_second_pilot(
    tmp_path: Path,
) -> None:
    db = Database(tmp_path / "org.db")
    first = start_pilot(
        db,
        pilot_id=PILOT_A,
        store_org_id="store-test-org",
        pilot_profile_id="profile-test",
        evidence_namespace="ns-test-a",
    )
    second = start_pilot(
        db,
        pilot_id=PILOT_A,
        store_org_id="store-test-org",
        pilot_profile_id="profile-test",
        evidence_namespace="ns-test-a",
    )
    assert first.idempotent_replay is False
    assert second.idempotent_replay is True
    assert second.started_at == first.started_at

    pilots = db.connection.execute("SELECT COUNT(*) AS c FROM pilots").fetchone()["c"]
    events = db.connection.execute(
        "SELECT COUNT(*) AS c FROM events WHERE kind = 'pilot.started'"
    ).fetchone()["c"]
    assert pilots == 1, "a replay must never create a second durable row"
    assert events == 1, "a replay must never append a second event"


def test_a_colliding_pilot_id_with_different_identity_is_refused_not_replayed(
    tmp_path: Path,
) -> None:
    """A `pilots.pilot_id` collision is only a safe replay when the incoming
    request's store_org_id/pilot_profile_id/evidence_namespace all match the
    durable row exactly. A DIFFERENT request reusing the same pilot_id must
    fail closed, never silently return the first caller's own data."""
    db = Database(tmp_path / "org.db")
    first = start_pilot(
        db,
        pilot_id=PILOT_A,
        store_org_id="store-test-org",
        pilot_profile_id="profile-test",
        evidence_namespace="ns-test-a",
    )
    assert first.idempotent_replay is False

    with pytest.raises(Refusal) as excinfo:
        start_pilot(
            db,
            pilot_id=PILOT_A,
            store_org_id="store-other-org",
            pilot_profile_id="profile-other",
            evidence_namespace="ns-test-b",
        )
    assert excinfo.value.category == "pilot_identity_conflict"

    pilots = db.connection.execute(
        "SELECT pilot_id, store_org_id, pilot_profile_id, evidence_namespace FROM pilots"
    ).fetchall()
    assert len(pilots) == 1
    assert pilots[0]["pilot_id"] == PILOT_A
    assert pilots[0]["store_org_id"] == "store-test-org"
    assert pilots[0]["pilot_profile_id"] == "profile-test"
    assert pilots[0]["evidence_namespace"] == "ns-test-a"
    events = db.connection.execute(
        "SELECT COUNT(*) AS c FROM events WHERE kind = 'pilot.started'"
    ).fetchone()["c"]
    assert events == 1, "the refusal must not append a second pilot.started event"
    assert active_pilot_id(db) == PILOT_A


def test_replay_survives_reopening_the_database(tmp_path: Path) -> None:
    """Restart proof: idempotency is durable, not merely in-process."""
    root = tmp_path / "org.db"
    first_db = Database(root)
    first = start_pilot(
        first_db,
        pilot_id=PILOT_A,
        store_org_id="store-test-org",
        pilot_profile_id="profile-test",
        evidence_namespace="ns-test-a",
    )
    first_db.close()

    reopened = Database(root)
    second = start_pilot(
        reopened,
        pilot_id=PILOT_A,
        store_org_id="store-test-org",
        pilot_profile_id="profile-test",
        evidence_namespace="ns-test-a",
    )
    assert second.idempotent_replay is True
    assert second.started_at == first.started_at
    pilots = reopened.connection.execute("SELECT COUNT(*) AS c FROM pilots").fetchone()["c"]
    assert pilots == 1


# === Fail-closed refusal ========================================================


def test_a_second_different_pilot_is_refused_while_one_is_active(tmp_path: Path) -> None:
    db = Database(tmp_path / "org.db")
    _start_a(db)

    with pytest.raises(Refusal) as excinfo:
        start_pilot(
            db,
            pilot_id=PILOT_B,
            store_org_id="store-other-org",
            pilot_profile_id="profile-other",
            evidence_namespace="ns-test-b",
        )
    assert excinfo.value.category == "pilot_already_active"


def test_a_refused_start_leaves_no_orphaned_pilot_row(tmp_path: Path) -> None:
    """Terminal atomicity: the refused pilots INSERT must roll back with
    the whole transaction, never leaving a pilot row with no active slot."""
    db = Database(tmp_path / "org.db")
    _start_a(db)

    with pytest.raises(Refusal):
        start_pilot(
            db,
            pilot_id=PILOT_B,
            store_org_id="store-other-org",
            pilot_profile_id="profile-other",
            evidence_namespace="ns-test-b",
        )

    pilots = db.connection.execute("SELECT pilot_id FROM pilots").fetchall()
    assert [row["pilot_id"] for row in pilots] == [PILOT_A]
    events = db.connection.execute(
        "SELECT COUNT(*) AS c FROM events WHERE kind = 'pilot.started'"
    ).fetchone()["c"]
    assert events == 1, "a refused start must never append its own pilot.started event"
    assert active_pilot_id(db) == PILOT_A


# === Fabrication leaves no traceable chain ======================================


def test_a_fabricated_pilot_started_event_creates_no_real_pilots_row(tmp_path: Path) -> None:
    """A `pilot.started` event inserted directly, bypassing `start_pilot`
    entirely, is the exact shape a curriculum or ledger check must be able
    to distinguish from the genuine mechanism -- matching Unit 10's own
    Pulse-guard discipline for fabricated `pulse.*` events. The event exists
    in the append-only log (append_event has no way to refuse an honest
    caller); the durable `pilots` row -- the thing any consumer must
    actually trust -- does not."""
    db = Database(tmp_path / "org.db")
    with db.transaction():
        append_event(db, "pilot.started", {"pilot_id": "fabricated-pilot"})

    events = db.connection.execute(
        "SELECT COUNT(*) AS c FROM events WHERE kind = 'pilot.started'"
    ).fetchone()["c"]
    pilots = db.connection.execute("SELECT COUNT(*) AS c FROM pilots").fetchone()["c"]
    assert events == 1, "the fabricated event is real -- append_event cannot refuse it"
    assert pilots == 0, "but no genuine pilots row backs it -- the fabrication is detectable"
    assert active_pilot_id(db) is None


# === Terminal persistence is atomic ============================================


def test_pilot_row_and_event_commit_together(tmp_path: Path) -> None:
    """No half-written state is ever observable: the pilots row and the
    pilot.started event either both exist or neither does."""
    db = Database(tmp_path / "org.db")
    start_pilot(
        db,
        pilot_id=PILOT_A,
        store_org_id="store-test-org",
        pilot_profile_id="profile-test",
        evidence_namespace="ns-test-a",
    )
    pilots = db.connection.execute("SELECT COUNT(*) AS c FROM pilots").fetchone()["c"]
    events = db.connection.execute(
        "SELECT COUNT(*) AS c FROM events WHERE kind = 'pilot.started'"
    ).fetchone()["c"]
    active = db.connection.execute("SELECT COUNT(*) AS c FROM active_pilot").fetchone()["c"]
    assert pilots == 1
    assert events == 1
    assert active == 1


# === Concurrency: real, separate connections ===================================


def test_two_real_processes_starting_the_same_pilot_produce_exactly_one_row(
    tmp_path: Path,
) -> None:
    """A REAL two-connection proof, matching `test_pulse.py`'s own
    precedent: two genuinely separate `Database` connections race
    `start_pilot` for the SAME pilot_id via a real `threading.Barrier`.
    Exactly one must create the canonical row; the other must observe the
    SAME identity as an idempotent replay."""
    root = tmp_path / "org.db"
    Database(root).close()  # create the file and apply migrations up front

    barrier = threading.Barrier(2)
    results: list[bool] = []
    lock = threading.Lock()

    def contend() -> None:
        db = Database(root)
        db.connection.execute("PRAGMA busy_timeout = 5000")
        barrier.wait()
        record = start_pilot(
            db,
            pilot_id=PILOT_A,
            store_org_id="store-test-org",
            pilot_profile_id="profile-test",
            evidence_namespace="ns-test-a",
        )
        with lock:
            results.append(record.idempotent_replay)
        db.close()

    threads = [threading.Thread(target=contend) for _ in range(2)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    assert sorted(results) == [False, True], f"expected one winner, one replay: {results}"

    inspector = Database(root)
    pilots = inspector.connection.execute("SELECT COUNT(*) AS c FROM pilots").fetchone()["c"]
    events = inspector.connection.execute(
        "SELECT COUNT(*) AS c FROM events WHERE kind = 'pilot.started'"
    ).fetchone()["c"]
    assert pilots == 1
    assert events == 1


def test_two_real_processes_starting_different_pilots_produce_exactly_one_winner(
    tmp_path: Path,
) -> None:
    """The distinct concurrency property the governing SOW names
    separately from replay: two DIFFERENT pilot identities racing to start
    at the same moment. One must win (create the canonical row); the other
    must be refused, never both creating their own row."""
    root = tmp_path / "org.db"
    Database(root).close()

    barrier = threading.Barrier(2)
    outcomes: list[str] = []
    lock = threading.Lock()

    def contend(pilot_id: str, org_id: str) -> None:
        db = Database(root)
        db.connection.execute("PRAGMA busy_timeout = 5000")
        barrier.wait()
        try:
            start_pilot(
                db,
                pilot_id=pilot_id,
                store_org_id=org_id,
                pilot_profile_id="profile-test",
                evidence_namespace=f"ns-{pilot_id}",
            )
            with lock:
                outcomes.append("won")
        except Refusal as error:
            assert error.category == "pilot_already_active"
            with lock:
                outcomes.append("refused")
        db.close()

    threads = [
        threading.Thread(target=contend, args=(PILOT_A, "store-a")),
        threading.Thread(target=contend, args=(PILOT_B, "store-b")),
    ]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    assert sorted(outcomes) == ["refused", "won"], f"expected one winner, one refusal: {outcomes}"

    inspector = Database(root)
    pilots = inspector.connection.execute("SELECT COUNT(*) AS c FROM pilots").fetchone()["c"]
    events = inspector.connection.execute(
        "SELECT COUNT(*) AS c FROM events WHERE kind = 'pilot.started'"
    ).fetchone()["c"]
    assert pilots == 1, "exactly one of the two competing pilots may become durable"
    assert events == 1


def test_two_real_processes_racing_the_same_pilot_id_with_conflicting_identity_produce_one_winner(
    tmp_path: Path,
) -> None:
    """The identity-conflict dual of the above: two REAL, separate
    connections race `start_pilot` for the SAME pilot_id but with
    conflicting store_org_id/pilot_profile_id/evidence_namespace. Exactly
    one may win (create the canonical row); the other must be refused with
    `pilot_identity_conflict`, never silently replay the winner's data."""
    root = tmp_path / "org.db"
    Database(root).close()

    barrier = threading.Barrier(2)
    outcomes: list[str] = []
    lock = threading.Lock()

    def contend(org_id: str) -> None:
        db = Database(root)
        db.connection.execute("PRAGMA busy_timeout = 5000")
        barrier.wait()
        try:
            start_pilot(
                db,
                pilot_id=PILOT_A,
                store_org_id=org_id,
                pilot_profile_id=f"profile-{org_id}",
                evidence_namespace=f"ns-{org_id}",
            )
            with lock:
                outcomes.append("won")
        except Refusal as error:
            assert error.category == "pilot_identity_conflict"
            with lock:
                outcomes.append("refused")
        db.close()

    threads = [
        threading.Thread(target=contend, args=("store-a",)),
        threading.Thread(target=contend, args=("store-b",)),
    ]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    assert sorted(outcomes) == ["refused", "won"], f"expected one winner, one refusal: {outcomes}"

    inspector = Database(root)
    pilots = inspector.connection.execute("SELECT COUNT(*) AS c FROM pilots").fetchone()["c"]
    events = inspector.connection.execute(
        "SELECT COUNT(*) AS c FROM events WHERE kind = 'pilot.started'"
    ).fetchone()["c"]
    assert pilots == 1, "exactly one canonical pilots row must exist afterward"
    assert events == 1, "exactly one pilot.started event must exist afterward"
