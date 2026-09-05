"""Adversarial proofs for the six advanced teaching mechanisms."""

from __future__ import annotations

import sqlite3
from collections.abc import Iterator
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime, timedelta
from pathlib import Path
from threading import Barrier, Lock

import pytest

from reference_organizations.store.advanced_demo import run_advanced
from sovereign_agent.automation import WatchDecision, create_automation, run_due
from sovereign_agent.context import ContextItem, append_message, compact_one, render_context
from sovereign_agent.coordination import (
    claim_session,
    finish_session,
    record_delivery_failure,
    register_host,
)
from sovereign_agent.database import Database
from sovereign_agent.errors import Refusal
from sovereign_agent.isolation import IsolationPolicy
from sovereign_agent.memory import recall, remember
from sovereign_agent.organization import Organization
from sovereign_agent.tools import Tool, ToolCatalog

NOW = datetime(2026, 9, 5, tzinfo=UTC)


@pytest.fixture
def org(tmp_path: Path) -> Iterator[Organization]:
    organization = Organization(tmp_path)
    try:
        yield organization
    finally:
        organization.db.connection.close()


def test_isolation_planes_are_independent_and_deny_wins(tmp_path: Path) -> None:
    root = tmp_path / "workspace"
    root.mkdir()
    policy = IsolationPolicy(
        filesystem_roots=(root,),
        network_hosts=frozenset({"api.example.test"}),
        credential_names=frozenset({"MODEL_TOKEN"}),
        allowed_tools=frozenset({"read", "shell"}),
        denied_tools=frozenset({"shell"}),
    )
    assert policy.authorize_path(root / "answer.txt") == root / "answer.txt"
    assert policy.authorize_network("API.EXAMPLE.TEST.") == "api.example.test"
    assert policy.authorize_credential("MODEL_TOKEN") == "MODEL_TOKEN"
    with pytest.raises(Refusal, match="filesystem access"):
        policy.authorize_path(tmp_path / "outside.txt")
    with pytest.raises(Refusal, match="tool access"):
        policy.authorize_tool("shell")
    statuses = {status.plane: status for status in policy.explain()}
    assert statuses["process"].verdict == "UNAVAILABLE"
    assert "not an OS egress firewall" in statuses["network"].detail


def test_isolation_resolves_symlinks_before_authorizing(tmp_path: Path) -> None:
    root, outside = tmp_path / "workspace", tmp_path / "outside"
    root.mkdir()
    outside.mkdir()
    (root / "escape").symlink_to(outside, target_is_directory=True)
    with pytest.raises(Refusal):
        IsolationPolicy(filesystem_roots=(root,)).authorize_path(root / "escape" / "file")


def test_discovery_does_not_authorize_a_matching_tool() -> None:
    catalog = ToolCatalog(
        [
            Tool("read_inventory", "read stock levels", ("stock",)),
            Tool("delete_inventory", "delete stock rows", ("stock",)),
            Tool("send_email", "notify a supplier"),
        ]
    )
    result = catalog.discover("stock", limit=1)
    assert result.total_matches == 2 and result.truncated
    denied = next(
        tool for tool in catalog.discover("delete stock").tools if tool.name == "delete_inventory"
    )
    with pytest.raises(Refusal):
        catalog.authorize(
            denied,
            IsolationPolicy(
                allowed_tools=frozenset({"read_inventory", "delete_inventory"}),
                denied_tools=frozenset({"delete_inventory"}),
            ),
        )


def test_nonfiring_watcher_persists_state_without_inventing_a_run(org: Organization) -> None:
    create_automation(
        org.db, "low-stock", interval_seconds=60, payload="check stock", first_run_at=NOW
    )
    result = run_due(
        org.db,
        "low-stock",
        lambda state: WatchDecision(False, "still healthy", {"checks": state.get("checks", 0) + 1}),
        lambda _run_id, _message: pytest.fail("payload must not run"),
        now=NOW,
    )
    assert result.status == "NO_FIRE"
    row = org.db.connection.execute(
        "SELECT condition_state FROM automations WHERE id = 'low-stock'"
    ).fetchone()
    assert row["condition_state"] == '{"checks":1}'
    assert org.db.connection.execute("SELECT COUNT(*) FROM automation_runs").fetchone()[0] == 0


def test_failed_payload_keeps_condition_state_retryable_and_auto_disables(
    org: Organization,
) -> None:
    create_automation(
        org.db,
        "supplier",
        interval_seconds=60,
        payload="contact supplier",
        first_run_at=NOW,
        max_failures=2,
    )

    def fail(_run_id: str, _message: str) -> None:
        raise RuntimeError("supplier unavailable")

    def condition(_state: dict[str, object]) -> WatchDecision:
        return WatchDecision(True, "order", {"notified": True})

    first = run_due(org.db, "supplier", condition, fail, now=NOW)
    second = run_due(org.db, "supplier", condition, fail, now=NOW + timedelta(seconds=60))
    row = org.db.connection.execute("SELECT * FROM automations WHERE id = 'supplier'").fetchone()
    assert (first.status, second.status) == ("FAILED", "FAILED")
    assert row["condition_state"] == "{}"
    assert row["enabled"] == 0 and row["failure_count"] == 2


def test_payload_receives_durable_run_id_as_its_idempotency_key(org: Organization) -> None:
    create_automation(org.db, "daily", interval_seconds=60, payload="report", first_run_at=NOW)
    calls: list[tuple[str, str]] = []
    result = run_due(
        org.db,
        "daily",
        lambda _state: WatchDecision(True, "report now", {"sent": True}),
        lambda run_id, message: calls.append((run_id, message)),
        now=NOW,
    )
    assert result.status == "SUCCEEDED"
    assert calls == [(result.run_id, "report now")]


def test_two_scheduler_processes_claim_one_due_slot(tmp_path: Path) -> None:
    org = Organization(tmp_path)
    create_automation(org.db, "daily", interval_seconds=60, payload="report", first_run_at=NOW)
    org.db.close()
    barrier, lock, calls = Barrier(2), Lock(), []

    def contender() -> str:
        db = Database(tmp_path / ".sovereign" / "organization.db")

        def condition(_state: dict[str, object]) -> WatchDecision:
            barrier.wait()
            return WatchDecision(True, "report", {"sent": True})

        def payload(_run_id: str, _message: str) -> None:
            with lock:
                calls.append("sent")

        try:
            return run_due(db, "daily", condition, payload, now=NOW).status
        finally:
            db.close()

    with ThreadPoolExecutor(max_workers=2) as pool:
        futures = [pool.submit(contender) for _ in range(2)]
        statuses = sorted(future.result() for future in futures)
    assert statuses == ["REPLAYED", "SUCCEEDED"]
    assert calls == ["sent"]


def _seed_transcript(org: Organization) -> None:
    for role, content in (
        ("system", "Founding instruction"),
        ("user", "Keep Lucy's request verbatim"),
        ("assistant", "A long derived explanation"),
        ("tool", "A large derived tool result"),
        ("user", "Do not paraphrase this correction"),
        ("assistant", "Recent answer"),
        ("tool", "Recent tool output"),
    ):
        append_message(org.db, "session-1", role, content)


def test_compaction_appends_a_view_and_preserves_every_source_byte(org: Organization) -> None:
    _seed_transcript(org)
    before = [tuple(row) for row in org.db.connection.execute("SELECT * FROM transcript_messages")]
    assert compact_one(
        org.db,
        "session-1",
        lambda prior, exchange: prior + "summary:" + ",".join(item.role for item in exchange),
    )
    after = [tuple(row) for row in org.db.connection.execute("SELECT * FROM transcript_messages")]
    rendered = render_context(org.db, "session-1")
    assert after == before
    assert any(item.derived and item.content == "summary:assistant,tool" for item in rendered)
    assert {item.content for item in rendered if item.role == "user"} == {
        "Keep Lucy's request verbatim",
        "Do not paraphrase this correction",
    }


def test_failed_or_empty_compaction_leaves_no_marker(org: Organization) -> None:
    _seed_transcript(org)
    assert not compact_one(org.db, "session-1", lambda _prior, _exchange: "")
    assert org.db.connection.execute("SELECT COUNT(*) FROM context_compactions").fetchone()[0] == 0


def test_compactor_exception_leaves_source_and_cursor_untouched(org: Organization) -> None:
    _seed_transcript(org)

    def fail(_prior: str, _exchange: tuple[ContextItem, ...]) -> str:
        raise RuntimeError("summarizer unavailable")

    with pytest.raises(RuntimeError, match="summarizer unavailable"):
        compact_one(org.db, "session-1", fail)
    assert org.db.connection.execute("SELECT COUNT(*) FROM context_compactions").fetchone()[0] == 0


def test_transcript_source_is_append_only(org: Organization) -> None:
    append_message(org.db, "session-1", "user", "source")
    with pytest.raises(sqlite3.IntegrityError, match="update refused"):
        org.db.connection.execute("UPDATE transcript_messages SET content = 'rewrite'")


def test_session_takeover_increments_incarnation_and_fences_stale_finish(
    org: Organization,
) -> None:
    register_host(org.db, "host-a", now=NOW, ttl_seconds=10)
    register_host(org.db, "host-b", now=NOW + timedelta(seconds=20), ttl_seconds=60)
    first = claim_session(org.db, "session-1", "host-a", now=NOW, ttl_seconds=10)
    second = claim_session(
        org.db, "session-1", "host-b", now=NOW + timedelta(seconds=20), ttl_seconds=60
    )
    assert (first.incarnation, second.incarnation) == (1, 2)
    with pytest.raises(Refusal, match="Session claim refused"):
        finish_session(org.db, first, "stale result")
    finish_session(org.db, second, "current result", now=NOW + timedelta(seconds=20))
    row = org.db.connection.execute(
        "SELECT host_id, incarnation, result FROM session_completions"
    ).fetchone()
    assert tuple(row) == ("host-b", 2, "current result")


def test_live_session_claim_refuses_a_second_host(org: Organization) -> None:
    register_host(org.db, "host-a", now=NOW)
    register_host(org.db, "host-b", now=NOW)
    claim_session(org.db, "session-1", "host-a", now=NOW)
    with pytest.raises(Refusal, match="live claim belongs to host-a"):
        claim_session(org.db, "session-1", "host-b", now=NOW)


def test_expired_session_cannot_finish_without_a_takeover(org: Organization) -> None:
    register_host(org.db, "host-a", now=NOW, ttl_seconds=10)
    claim = claim_session(org.db, "session-1", "host-a", now=NOW, ttl_seconds=10)
    with pytest.raises(Refusal, match="stale or expired"):
        finish_session(org.db, claim, "late result", now=NOW + timedelta(seconds=11))


def test_delivery_attempt_count_survives_reopen(tmp_path: Path) -> None:
    org = Organization(tmp_path)
    assert record_delivery_failure(org.db, "delivery-1", "offline", NOW) == 1
    org.db.connection.close()
    reopened = Organization(tmp_path)
    assert record_delivery_failure(reopened.db, "delivery-1", "still offline", NOW) == 2
    reopened.db.connection.close()


def test_memory_filters_access_before_ranking_and_exposes_score_components(
    org: Organization,
) -> None:
    remember(org.db, "public", "Lucy orders vanilla stock", embedding=(1.0, 0.0))
    remember(
        org.db,
        "private-a",
        "Lucy's private vanilla supplier password",
        visibility="actor:alice",
        importance=1.0,
        embedding=(1.0, 0.0),
    )
    remember(
        org.db,
        "private-b",
        "Bob private vanilla plan",
        visibility="actor:bob",
        embedding=(1.0, 0.0),
    )
    hits = recall(org.db, "vanilla stock", actor_id="alice", query_embedding=(1.0, 0.0))
    assert {hit.id for hit in hits} == {"public", "private-a"}
    assert all(hit.semantic_status == "used" for hit in hits)
    assert all(0 <= hit.lexical <= 1 and 0 <= hit.recency <= 1 for hit in hits)


def test_memory_semantic_failure_is_visible_as_lexical_only(org: Organization) -> None:
    remember(org.db, "one", "vanilla inventory")
    hit = recall(org.db, "vanilla", actor_id="alice")[0]
    assert hit.semantic == 0 and hit.semantic_status == "unavailable"


def test_memory_does_not_return_an_unrelated_high_importance_row(org: Organization) -> None:
    remember(org.db, "unrelated", "chocolate supplier", importance=1.0)
    assert recall(org.db, "vanilla inventory", actor_id="alice") == ()


def test_migration_18_applies_to_existing_databases(tmp_path: Path) -> None:
    org = Organization(tmp_path)
    assert 18 in org.db.applied_versions()
    org.db.connection.close()
    reopened = Organization(tmp_path)
    assert 18 in reopened.db.applied_versions()
    reopened.db.connection.close()


def test_advanced_demo_exercises_all_six_mechanisms(tmp_path: Path) -> None:
    report = run_advanced(tmp_path)
    assert "process=UNAVAILABLE" in report
    assert "tools: discovered=read_inventory authorized=read_inventory truncated=True" in report
    assert "automation: NO_FIRE, runs=0, state persisted" in report
    assert "context: source=7 rendered=6 summaries=1" in report
    assert "coordination: incarnation 1->2" in report
    assert "memory: visible=1 semantic=used" in report
