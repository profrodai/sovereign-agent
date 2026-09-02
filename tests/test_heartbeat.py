"""Heartbeat: durable liveness records, honestly separate from work.

Each test is a claim the mechanism makes; together they pin the design:
beats are appended and never rewritten, verdicts are earned against real
timestamps, and — the load-bearing one — recording a beat writes NOTHING
into the events ledger, so liveness can never masquerade as work.
"""

from __future__ import annotations

import sqlite3
from datetime import timedelta
from pathlib import Path

import pytest

from sovereign_agent.heartbeat import heartbeat_status, record_heartbeat
from sovereign_agent.ids import utc_now
from sovereign_agent.organization import Organization


@pytest.fixture
def org(tmp_path: Path) -> Organization:
    return Organization(tmp_path)


def test_no_beats_is_its_own_verdict_not_stale(org: Organization) -> None:
    status = heartbeat_status(org)
    assert status.verdict == "NO_BEATS"
    assert status.last_beat_at is None
    assert "no heartbeat has ever been recorded" in status.line()


def test_a_fresh_beat_reads_alive(org: Organization) -> None:
    beat_id = record_heartbeat(org, source="test")
    status = heartbeat_status(org, stale_after_seconds=900)
    assert status.verdict == "ALIVE"
    assert status.last_beat_id == beat_id
    assert status.source == "test"
    assert status.age_seconds is not None and status.age_seconds < 60


def test_an_old_beat_reads_stale_and_says_what_that_proves(org: Organization) -> None:
    old = (utc_now() - timedelta(seconds=3600)).isoformat()
    org.db.connection.execute(
        "INSERT INTO heartbeats (beat_id, source, created_at) VALUES (?, ?, ?)",
        ("beat_old", "test", old),
    )
    org.db.connection.commit()
    status = heartbeat_status(org, stale_after_seconds=900)
    assert status.verdict == "STALE"
    assert "proves silence, not death" in status.line()


def test_the_newest_beat_wins(org: Organization) -> None:
    old = (utc_now() - timedelta(seconds=3600)).isoformat()
    org.db.connection.execute(
        "INSERT INTO heartbeats (beat_id, source, created_at) VALUES (?, ?, ?)",
        ("beat_old", "test", old),
    )
    org.db.connection.commit()
    fresh = record_heartbeat(org, source="fresher")
    status = heartbeat_status(org, stale_after_seconds=900)
    assert status.verdict == "ALIVE"
    assert status.last_beat_id == fresh


def test_beats_are_append_only(org: Organization) -> None:
    record_heartbeat(org)
    with pytest.raises(sqlite3.IntegrityError, match="update refused"):
        org.db.connection.execute("UPDATE heartbeats SET source = 'forged'")
    with pytest.raises(sqlite3.IntegrityError, match="delete refused"):
        org.db.connection.execute("DELETE FROM heartbeats")


def test_a_beat_writes_nothing_into_the_events_ledger(org: Organization) -> None:
    """The separation that keeps the claim honest: liveness is not work."""
    before = org.db.connection.execute("SELECT COUNT(*) FROM events").fetchone()[0]
    record_heartbeat(org)
    record_heartbeat(org)
    after = org.db.connection.execute("SELECT COUNT(*) FROM events").fetchone()[0]
    assert after == before


def test_cli_status_exit_codes_are_watchdog_usable(org: Organization, capsys) -> None:
    import argparse

    from sovereign_agent.cli import _heartbeat

    def ns(**kw) -> argparse.Namespace:
        return argparse.Namespace(root=str(org.root), **kw)

    assert _heartbeat(ns(status=True, stale_after=900, source="cli")) == 1  # NO_BEATS
    assert _heartbeat(ns(status=False, stale_after=900, source="watchdog")) == 0
    assert _heartbeat(ns(status=True, stale_after=900, source="cli")) == 0  # ALIVE
    out = capsys.readouterr().out
    assert "NO_BEATS" in out and "beat recorded:" in out and "ALIVE" in out


def test_migration_17_applies_to_an_existing_database(tmp_path: Path) -> None:
    """Reopening an org created before this feature gains the table cleanly."""
    org = Organization(tmp_path)
    assert 17 in org.db.applied_versions()
    reopened = Organization(tmp_path)
    assert 17 in reopened.db.applied_versions()
    record_heartbeat(reopened)
    assert heartbeat_status(reopened).verdict == "ALIVE"
