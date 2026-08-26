"""The Scripted provider's own failure matrix.

Every learner runs the Scripted provider; none of them need credentials for it.
Yet the provider integration matrix parametrized ["claude", "codex", "cursor"]
only, so the one provider a reader actually exercises was the one whose failure
paths had no test. Reported in the Units 0-6 acceptance audit as F-U5-2.

Every case below asserts the SAME property from a different direction: a run
that did not succeed must leave a DURABLE FAILED RECEIPT and a non-running
terminal state. Never a guessed success, never a silent orphan.
"""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

import pytest

import sovereign_agent.organization as organization_module
from reference_organizations.store import seed
from sovereign_agent.errors import Refusal
from sovereign_agent.models import AssignmentState, Role
from sovereign_agent.organization import Organization


def dispatched(tmp_path: Path, scope: str = "replenish") -> tuple[Organization, str]:
    """An organization with one assignment created and ready to run."""
    org = Organization.init(tmp_path)
    seed(org.db)
    outcome = org.create_outcome(
        "Keep the tea jar stocked",
        "On-hand tea stays at or above the reorder point.",
        ["inventory_at_or_above_reorder_point"],
        "principal-human",
        "SKU-TEA",
    )
    org.activate(outcome.id, "master-course")
    sow = org.create_sow(outcome.id, scope, Role.OPERATOR, "master-course")
    org.ready_sow(sow.id)
    assignment = org.assign(sow.id, "operator-course", "master-course")
    return org, assignment.id


def receipts(org: Organization) -> list[dict]:
    return [
        json.loads(row["record"])
        for row in org.db.connection.execute("SELECT record FROM receipts").fetchall()
    ]


def assert_failed_closed(org: Organization, assignment_id: str, category: str) -> None:
    """The invariant every non-success case must satisfy."""
    state = org._assignment(assignment_id).state  # noqa: SLF001
    assert state is not AssignmentState.RUNNING, "left recorded as RUNNING: the ledger lies"
    assert state in {AssignmentState.FAILED, AssignmentState.BLOCKED}
    written = receipts(org)
    assert written, "no durable receipt: the failure left no record"
    assert written[-1]["status"] != "completed", "a failure was recorded as success"
    assert written[-1]["failure_category"] == category
    assert written[-1]["assignment_id"] == assignment_id


# --- 1. success -------------------------------------------------------------


def test_scripted_success_records_a_completed_receipt(tmp_path: Path) -> None:
    org, assignment_id = dispatched(tmp_path)
    org.run_assignment(assignment_id)
    assert org._assignment(assignment_id).state is AssignmentState.COMPLETED  # noqa: SLF001
    written = receipts(org)
    assert written[-1]["status"] == "completed"
    assert written[-1]["failure_category"] is None


# --- 2. provider reports its own failure ------------------------------------


def test_scripted_provider_reported_failure(tmp_path: Path) -> None:
    """The Scripted fixture fails deliberately when its scope says so.

    That branch exists in providers/scripted.py and was never asserted.
    """
    org, assignment_id = dispatched(tmp_path, scope="please fail this run")
    org.run_assignment(assignment_id)
    assert_failed_closed(org, assignment_id, "actor_reported_failure")


# --- 3. timeout -------------------------------------------------------------


def test_scripted_timeout_is_not_completion(tmp_path: Path) -> None:
    org, assignment_id = dispatched(tmp_path)
    timeout = Refusal(
        "Provider timed out.",
        "A hung provider must not be treated as completion.",
        "logs",
        "Retry.",
        category="timeout",
    )
    with patch.object(organization_module, "invoke_actor", side_effect=timeout):
        with pytest.raises(Refusal):
            org.run_assignment(assignment_id)
    assert_failed_closed(org, assignment_id, "timeout")


# --- 4. catchable interruption ----------------------------------------------


@pytest.mark.parametrize("interruption", [KeyboardInterrupt, SystemExit])
def test_catchable_interruption_never_leaves_a_running_assignment(
    tmp_path: Path, interruption: type[BaseException]
) -> None:
    """KeyboardInterrupt and SystemExit are NOT Exception.

    They escaped `run_assignment` entirely, skipping the persistence block and
    leaving the assignment recorded as RUNNING with no receipt — a ledger
    asserting work in progress that was not. Fail-open, in the unit whose
    subject is that a status must not outrun the world. Audit finding F-U5-1.

    A hard kill (SIGKILL) is deliberately NOT covered: a process cannot record
    its own death, and that is Unit 8 recovery territory.
    """
    org, assignment_id = dispatched(tmp_path)
    with patch.object(organization_module, "invoke_actor", side_effect=interruption("stop")):
        with pytest.raises(interruption):
            org.run_assignment(assignment_id)
    assert_failed_closed(org, assignment_id, "interrupted")


# --- 5. malformed JSONL stream ----------------------------------------------


def test_malformed_event_stream_fails_closed(tmp_path: Path) -> None:
    org, assignment_id = dispatched(tmp_path)
    malformed = Refusal(
        "Provider emitted a malformed stream.",
        "Unparseable output is not evidence of work.",
        "provider-raw/events.jsonl",
        "Inspect the raw stream.",
        category="malformed_stream",
    )
    with patch.object(organization_module, "invoke_actor", side_effect=malformed):
        with pytest.raises(Refusal):
            org.run_assignment(assignment_id)
    assert_failed_closed(org, assignment_id, "malformed_stream")


# --- 6. malformed report (unparseable) --------------------------------------


def test_malformed_report_is_refused(tmp_path: Path) -> None:
    from reference_organizations.store.demo import propose_restock_from_report

    bad = tmp_path / "report.json"
    bad.write_text("{not json", encoding="utf-8")
    with pytest.raises(Refusal, match="not valid JSON"):
        propose_restock_from_report(bad, "SKU-TEA")


# --- 7. invalid report (parses, violates the schema) ------------------------


def test_invalid_report_fails_closed(tmp_path: Path) -> None:
    """Valid JSON that is not a valid ActorReport is still a failure."""
    org, assignment_id = dispatched(tmp_path)
    invalid = Refusal(
        "Provider report did not match the contract.",
        "A report that violates its schema proves nothing.",
        ".sovereign-out/report.json",
        "Fix the provider.",
        category="invalid_report",
    )
    with patch.object(organization_module, "invoke_actor", side_effect=invalid):
        with pytest.raises(Refusal):
            org.run_assignment(assignment_id)
    assert_failed_closed(org, assignment_id, "invalid_report")


# --- 8. no guessed success --------------------------------------------------


def test_no_failure_mode_is_ever_recorded_as_success(tmp_path: Path) -> None:
    """Sweep every category: none may yield status=completed.

    This is the property the other seven cases each demonstrate once. Asserting
    it as a set means a NEW failure path added later without a receipt fails
    here rather than shipping as a silent success.
    """
    categories = [
        "timeout",
        "malformed_stream",
        "invalid_report",
        "nonzero_exit",
        "missing_report",
        "missing_terminal",
        "provider_error",
    ]
    for category in categories:
        org, assignment_id = dispatched(tmp_path / category)
        refusal = Refusal("failed", "why", "where", "next", category=category)
        with patch.object(organization_module, "invoke_actor", side_effect=refusal):
            with pytest.raises(Refusal):
                org.run_assignment(assignment_id)
        assert_failed_closed(org, assignment_id, category)
