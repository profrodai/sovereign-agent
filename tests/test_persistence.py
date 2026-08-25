"""Transactions, migrations, and append-only enforcement.

These prove properties of the DATABASE, not of Python politeness. A rule that
lives only in a convention is a rule that a tired contributor removes.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path
from unittest.mock import patch

import pytest

import reference_organizations.store as store
from reference_organizations.store import RestockProposal, apply_restock, record_sale, seed
from sovereign_agent.database import MIGRATION_1, MIGRATIONS, Database
from sovereign_agent.organization import Organization


def store_state(org: Organization) -> tuple[int, int, int]:
    on_hand = int(
        org.db.connection.execute("SELECT on_hand FROM inventory WHERE sku = 'SKU-TEA'").fetchone()[
            "on_hand"
        ]
    )
    events = int(
        org.db.connection.execute(
            "SELECT COUNT(*) AS c FROM events WHERE kind = 'replenishment.committed'"
        ).fetchone()["c"]
    )
    purchases = int(
        org.db.connection.execute(
            "SELECT COUNT(*) AS c FROM cash_entries WHERE amount_cents < 0"
        ).fetchone()["c"]
    )
    return on_hand, events, purchases


def test_rollback_after_inventory_write_leaves_nothing_behind(tmp_path: Path) -> None:
    """Fail AFTER the inventory UPDATE but before the event commits."""
    org = Organization.init(tmp_path)
    seed(org.db)
    signal = record_sale(org.db, "SKU-TEA", 2, 400)
    before = store_state(org)
    with patch.object(store, "append_event", side_effect=RuntimeError("injected failure")):
        with pytest.raises(RuntimeError, match="injected failure"):
            apply_restock(org.db, RestockProposal("SKU-TEA", 6), "asg_fault", signal.id)
    assert store_state(org) == before, "partial business mutation survived a rollback"


def test_rollback_leaves_no_orphan_cash_entry(tmp_path: Path) -> None:
    org = Organization.init(tmp_path)
    seed(org.db)
    signal = record_sale(org.db, "SKU-TEA", 2, 400)
    with patch.object(store, "append_event", side_effect=RuntimeError("boom")):
        with pytest.raises(RuntimeError):
            apply_restock(org.db, RestockProposal("SKU-TEA", 6), "asg_fault", signal.id)
    row = org.db.connection.execute(
        "SELECT COUNT(*) AS c FROM cash_entries WHERE amount_cents < 0"
    ).fetchone()
    assert row["c"] == 0


def test_successful_sale_and_replenishment_keep_cash_reconciled(tmp_path: Path) -> None:
    org = Organization.init(tmp_path)
    seed(org.db)
    signal = record_sale(org.db, "SKU-TEA", 2, 400)
    assert store.cash_balance_cents(org.db) == 10_800
    apply_restock(org.db, RestockProposal("SKU-TEA", 6), "asg_ok", signal.id)
    # 10000 opening + 800 sale - (6 * 120) purchase
    assert store.cash_balance_cents(org.db) == 10_080


def test_inventory_never_goes_negative(tmp_path: Path) -> None:
    from sovereign_agent.errors import Refusal

    org = Organization.init(tmp_path)
    seed(org.db)
    with pytest.raises(Refusal, match="negative"):
        record_sale(org.db, "SKU-TEA", 99, 400)


def test_events_reject_update_and_delete(tmp_path: Path) -> None:
    org = Organization.init(tmp_path)
    seed(org.db)
    for statement in (
        "UPDATE events SET kind = 'TAMPERED'",
        "DELETE FROM events",
    ):
        with pytest.raises(sqlite3.IntegrityError, match="append-only"):
            org.db.connection.execute(statement)
        org.db.connection.rollback()


def test_insert_or_replace_cannot_bypass_the_append_only_guard(tmp_path: Path) -> None:
    """Without PRAGMA recursive_triggers, REPLACE deletes a row silently.

    SQLite does not fire BEFORE DELETE triggers for the implicit delete inside
    INSERT OR REPLACE unless recursive triggers are on. A guard that misses this
    is decorative.
    """
    org = Organization.init(tmp_path)
    row = org.db.connection.execute("SELECT id, kind FROM events LIMIT 1").fetchone()
    with pytest.raises(sqlite3.IntegrityError, match="append-only"):
        org.db.connection.execute(
            "INSERT OR REPLACE INTO events(id, kind, payload, created_at) "
            "VALUES (?, 'SNEAKY', '{}', 't')",
            (row["id"],),
        )
    org.db.connection.rollback()
    after = org.db.connection.execute(
        "SELECT kind FROM events WHERE id = ?", (row["id"],)
    ).fetchone()
    assert after["kind"] == row["kind"]


def test_fresh_database_applies_every_migration(tmp_path: Path) -> None:
    db = Database(tmp_path / "fresh.db")
    assert db.applied_versions() == {version for version, _ in MIGRATIONS}
    triggers = {
        row["name"]
        for row in db.connection.execute("SELECT name FROM sqlite_master WHERE type = 'trigger'")
    }
    assert {"events_no_update", "events_no_delete"} <= triggers


def test_upgrade_from_prior_schema_preserves_data(tmp_path: Path) -> None:
    """A database released at version 1 upgrades forward without losing rows."""
    path = tmp_path / "legacy.db"
    legacy = sqlite3.connect(path)
    legacy.executescript(MIGRATION_1)
    legacy.execute("INSERT INTO schema_migrations(version, applied_at) VALUES (1, datetime('now'))")
    legacy.execute(
        "INSERT INTO events(id, kind, payload, created_at) "
        "VALUES ('evt_legacy', 'legacy.kind', '{}', '2026-01-01T00:00:00Z')"
    )
    legacy.commit()
    legacy.close()

    db = Database(path)
    assert db.applied_versions() == {version for version, _ in MIGRATIONS}
    row = db.connection.execute(
        "SELECT COUNT(*) AS c FROM events WHERE id = 'evt_legacy'"
    ).fetchone()
    assert row["c"] == 1, "the upgrade destroyed pre-existing history"
    columns = {row[1] for row in db.connection.execute("PRAGMA table_info(evidence)")}
    assert {"outcome_id", "check_id", "success", "state_digest"} <= columns


def test_reopening_does_not_reapply_migrations(tmp_path: Path) -> None:
    """migrate() runs on every open, so it must be a no-op once applied."""
    path = tmp_path / "twice.db"
    first = Database(path)
    stamps = first.connection.execute(
        "SELECT version, applied_at FROM schema_migrations ORDER BY version"
    ).fetchall()
    second = Database(path)
    again = second.connection.execute(
        "SELECT version, applied_at FROM schema_migrations ORDER BY version"
    ).fetchall()
    assert [tuple(row) for row in stamps] == [tuple(row) for row in again]
    triggers = {
        row["name"]
        for row in second.connection.execute(
            "SELECT name FROM sqlite_master WHERE type = 'trigger'"
        )
    }
    assert {"events_no_update", "events_no_delete"} <= triggers


def test_migrations_are_forward_only_and_ordered() -> None:
    versions = [version for version, _ in MIGRATIONS]
    assert versions == sorted(versions), "migrations must apply in ascending order"
    assert len(set(versions)) == len(versions), "duplicate migration version"


def test_signal_is_recorded_with_the_sale(tmp_path: Path) -> None:
    org = Organization.init(tmp_path)
    seed(org.db)
    signal = record_sale(org.db, "SKU-TEA", 2, 400)
    row = org.db.connection.execute(
        "SELECT COUNT(*) AS c FROM signals WHERE id = ?", (signal.id,)
    ).fetchone()
    assert row["c"] == 1


def test_idempotency_is_scoped_to_assignment_and_sku(tmp_path: Path) -> None:
    """Replay protection must not silently swallow a different product's restock.

    Keyed on the assignment alone, a replenishment of SKU-B would make a later
    restock of SKU-TEA under the same assignment return "already done" while the
    tea shelf stayed empty.
    """
    import json

    org = Organization.init(tmp_path)
    seed(org.db)
    signal = record_sale(org.db, "SKU-TEA", 2, 400)
    org.db.connection.execute(
        "INSERT OR REPLACE INTO products(sku, record) VALUES ('SKU-B', ?)",
        (json.dumps({"sku": "SKU-B", "name": "b", "unit_cost_cents": 10, "price_cents": 20}),),
    )
    org.db.connection.execute(
        "INSERT OR REPLACE INTO inventory(sku, on_hand, reserved, reorder_point, record) "
        "VALUES ('SKU-B', 0, 0, 1, '{}')"
    )
    org.db.connection.commit()

    apply_restock(org.db, RestockProposal("SKU-B", 3), "asg_shared")
    result = apply_restock(org.db, RestockProposal("SKU-TEA", 6), "asg_shared", signal.id)
    assert result.get("idempotent_replay") is None, "a different SKU was treated as a replay"
    row = org.db.connection.execute(
        "SELECT on_hand FROM inventory WHERE sku = 'SKU-TEA'"
    ).fetchone()
    assert int(row["on_hand"]) == 8

    replay = apply_restock(org.db, RestockProposal("SKU-TEA", 6), "asg_shared", signal.id)
    assert replay.get("idempotent_replay") is True, "same assignment and SKU must still be a no-op"


def test_append_only_holds_from_a_connection_without_the_pragma(tmp_path: Path) -> None:
    """The guarantee must not depend on application code setting a PRAGMA.

    `recursive_triggers` is per-connection. With only the BEFORE DELETE guard,
    `INSERT OR REPLACE` from a plain sqlite3 connection — the exact tool
    Chapter 1 teaches — silently overwrote an event and left the row count
    unchanged, while verify_store_outcome still reported "ACCEPTED and true".

    This test opens its OWN connection and deliberately does not set the pragma,
    so it fails if enforcement ever moves back into application code.
    """
    org = Organization.init(tmp_path)
    seed(org.db)
    row = org.db.connection.execute("SELECT id, kind FROM events LIMIT 1").fetchone()
    event_id, original_kind = str(row["id"]), str(row["kind"])
    org.db.close()

    outsider = sqlite3.connect(tmp_path / ".sovereign" / "organization.db")
    outsider.row_factory = sqlite3.Row
    try:
        for statement, parameters in (
            (
                "INSERT OR REPLACE INTO events(id, kind, payload, created_at) "
                "VALUES (?, 'TAMPERED', '{}', 'now')",
                (event_id,),
            ),
            ("UPDATE events SET kind = 'TAMPERED' WHERE id = ?", (event_id,)),
            ("DELETE FROM events WHERE id = ?", (event_id,)),
        ):
            with pytest.raises(sqlite3.IntegrityError, match="append-only"):
                outsider.execute(statement, parameters)
                outsider.commit()
            outsider.rollback()

        surviving = outsider.execute("SELECT kind FROM events WHERE id = ?", (event_id,)).fetchone()
        assert surviving["kind"] == original_kind
    finally:
        outsider.close()
