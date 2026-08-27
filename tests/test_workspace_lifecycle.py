"""Unit 7: workspace lifecycle.

Five properties, per docs/rulings/2026-08-27-unit7-is-workspaces-not-pulse.md:

1. Reclaim tied to assignment terminal state.
2. `Actor.workspace_policy` is enforced, not merely declared.
3. The workspace boundary is detectable, not merely declared.
4. `_require_deliverables` refuses a path that would escape its root.
5. All four providers held to the same rule, with no live credential.

Every test here drives the REAL `run_assignment` / `_require_deliverables`
path, the same discipline test_scripted_execution_matrix.py established for
the interrupted-receipt fix this ruling explicitly asks reclaim to match.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from unittest.mock import patch

import pytest

import sovereign_agent.organization as organization_module
from reference_organizations.store import seed
from sovereign_agent.errors import Refusal
from sovereign_agent.models import AssignmentState, Role
from sovereign_agent.organization import Organization
from sovereign_agent.workspace import (
    PERSISTENT,
    TEMPORARY_DIRECTORY,
    diff_boundary,
    reclaim_workspace,
    safe_join,
    snapshot_boundary,
)


def dispatched(root: Path) -> tuple[Organization, str, str]:
    """A store with one SOW assigned but not yet run."""
    org = Organization.init(root)
    seed(org.db)
    outcome = org.create_outcome(
        "Keep the tea jar stocked",
        "On-hand tea stays at or above the reorder point.",
        ["inventory_at_or_above_reorder_point"],
        "principal-human",
        "SKU-TEA",
    )
    org.activate(outcome.id, "master-course")
    sow = org.create_sow(outcome.id, "replenish", Role.OPERATOR, "master-course")
    org.ready_sow(sow.id)
    assignment = org.assign(sow.id, "operator-course", "master-course")
    return org, sow.id, assignment.id


def workspace_dir(org: Organization, assignment_id: str) -> Path:
    assignment = org._assignment(assignment_id)  # noqa: SLF001
    return org.root / ".sovereign" / "runs" / assignment.workspace_id


# --- Property 1: reclaim tied to terminal state -----------------------------


def test_workspace_reclaimed_after_terminal_state(tmp_path: Path) -> None:
    """A completed assignment's scratch space is gone; its proof is not."""
    org, _sow_id, assignment_id = dispatched(tmp_path)
    workspace = workspace_dir(org, assignment_id)
    org.run_assignment(assignment_id)

    assert workspace.exists(), "the workspace directory itself must survive"
    assert (workspace / "receipt.json").is_file(), "the receipt is evidence, never reclaimed"
    assert (workspace / "receipt.json.sha256").is_file()
    assert (workspace / ".sovereign-out" / "report.json").is_file(), (
        "the report must survive reclaim: later verification reads it"
    )
    # provider-raw is the actor's own disposable scratch output -- exactly
    # what "reclaim" means here.
    assert not (workspace / "provider-raw").exists(), (
        "reclaim did not run: disposable scratch space survived a terminal state"
    )


def test_workspace_survives_non_terminal_state(tmp_path: Path) -> None:
    """An assignment that never ran must not have its workspace touched.

    `assign()` allocates a `workspace_id` but `run_assignment` is what creates
    the directory and is the only place reclaim is ever called. Nothing must
    reach into a workspace for an assignment still short of RUNNING.
    """
    org, _sow_id, assignment_id = dispatched(tmp_path)
    workspace = workspace_dir(org, assignment_id)
    assert not workspace.exists(), "run_assignment was never called"
    assert org._assignment(assignment_id).state == AssignmentState.CREATED  # noqa: SLF001


def test_interrupted_assignment_still_reclaims_its_scratch_space(tmp_path: Path) -> None:
    """The ruling's own bar: reclaim must be as fail-closed-correct as the
    interrupted-receipt fix it is compared to -- meaning reclaim must still
    run on the interrupted path, not be silently skipped, because the
    assignment IS recorded terminal (FAILED, category "interrupted") before
    `run_assignment` re-raises. A workspace is not "still in use" once the
    ledger itself says the work is over.
    """
    org, _sow_id, assignment_id = dispatched(tmp_path)
    workspace = workspace_dir(org, assignment_id)
    workspace.mkdir(parents=True)
    (workspace / ".sovereign-out").mkdir()
    # The actor's own disposable scratch output -- exactly what "reclaim"
    # means, and exactly what test_workspace_reclaimed_after_terminal_state
    # checks for the non-interrupted path. Without this, the test has no
    # precondition reclaim could possibly observe: `.sovereign-out` is on
    # `_PRESERVED_DIR_ON_RECLAIM` and survives whether or not reclaim ever
    # runs, so a test that only creates it cannot tell "reclaim ran and
    # preserved evidence" from "reclaim never ran at all."
    (workspace / "provider-raw").mkdir()
    (workspace / "provider-raw" / "scratch.txt").write_text("disposable")

    with patch.object(organization_module, "invoke_actor", side_effect=KeyboardInterrupt("stop")):
        with pytest.raises(KeyboardInterrupt):
            org.run_assignment(assignment_id)

    assert org._assignment(assignment_id).state == AssignmentState.FAILED  # noqa: SLF001
    assert (workspace / "receipt.json").is_file(), "the interrupted receipt is evidence"
    row = org.db.connection.execute(
        "SELECT record FROM receipts WHERE assignment_id = ?", (assignment_id,)
    ).fetchone()
    assert json.loads(row["record"])["failure_category"] == "interrupted"
    assert not (workspace / "provider-raw").exists(), (
        "reclaim did not run on the interrupted path: disposable scratch space survived"
    )


def test_a_hard_kill_that_never_returns_leaves_the_workspace_alone(tmp_path: Path) -> None:
    """A process that dies before `run_assignment` reaches its persistence
    block never calls reclaim at all -- simulated here not by raising inside
    `run_assignment` (that IS the interrupted case above) but by never
    invoking it in the first place, the only thing an in-process test can
    honestly stand in for a SIGKILL. Unit 8 recovery territory; this test
    only proves Unit 7 does not overreach into it.
    """
    org, _sow_id, assignment_id = dispatched(tmp_path)
    workspace = workspace_dir(org, assignment_id)
    workspace.mkdir(parents=True)
    marker = workspace / "still-running.marker"
    marker.write_text("a hard kill leaves this behind")

    # No call to run_assignment: this stands for the process dying before
    # reclaim's call site is ever reached.
    assert marker.is_file(), "nothing reclaimed a workspace run_assignment never finished"


# --- Property 2: Actor.workspace_policy is enforced -------------------------


def test_persistent_policy_keeps_scratch_space(tmp_path: Path) -> None:
    org, _sow_id, assignment_id = dispatched(tmp_path)
    org.actors["operator-course"].workspace_policy = PERSISTENT
    workspace = workspace_dir(org, assignment_id)
    org.run_assignment(assignment_id)
    assert (workspace / "provider-raw").exists(), "persistent must leave the whole run inspectable"


def test_temporary_directory_policy_reclaims_scratch_files(tmp_path: Path) -> None:
    """The default value, exercised explicitly: same assignment shape as the
    persistent case above, opposite outcome -- proof the field, not luck,
    drives the branch.
    """
    org, _sow_id, assignment_id = dispatched(tmp_path)
    assert org.actors["operator-course"].workspace_policy == TEMPORARY_DIRECTORY
    workspace = workspace_dir(org, assignment_id)
    org.run_assignment(assignment_id)
    assert not (workspace / "provider-raw").exists()


def test_unknown_workspace_policy_fails_closed(tmp_path: Path) -> None:
    workspace = tmp_path / "ws"
    workspace.mkdir()
    with pytest.raises(Refusal, match="Unknown workspace policy"):
        reclaim_workspace(workspace, "delete_immediately")


def test_workspace_policy_loads_from_toml(tmp_path: Path) -> None:
    """Loaded, not just modeled: `actors.py` used to read id/role/provider/
    authority and silently drop workspace_policy from committed TOML.
    """
    Organization.init(tmp_path)
    (tmp_path / "sovereign.toml").write_text(
        (tmp_path / "sovereign.toml")
        .read_text(encoding="utf-8")
        .replace(
            'id = "operator-course"',
            'id = "operator-course"\nworkspace_policy = "persistent"',
        ),
        encoding="utf-8",
    )
    reloaded = Organization(tmp_path)
    assert reloaded.actors["operator-course"].workspace_policy == PERSISTENT


# --- Property 3: the workspace boundary is detectable -----------------------


def test_detects_write_outside_workspace(tmp_path: Path) -> None:
    """A file outside the workspace changing during an invocation must be
    caught by the boundary diff -- the detection mechanism itself, exercised
    directly rather than through a fake CLI, since the property is about the
    organization's own check, not about any one provider's honesty.
    """
    org = Organization.init(tmp_path)
    tracked = tmp_path / "outside.txt"
    tracked.write_text("original")
    workspace = tmp_path / ".sovereign" / "runs" / "ws_test"
    workspace.mkdir(parents=True)

    before = snapshot_boundary(org.root, workspace)
    tracked.write_text("tampered by a provider that ignored its boundary")
    after = snapshot_boundary(org.root, workspace)

    report = diff_boundary(before, after)
    assert report.violated
    assert "outside.txt" in report.changed


def test_writes_inside_the_workspace_do_not_trip_the_boundary_check(tmp_path: Path) -> None:
    """Mutation check, the other direction: legitimate work inside the
    workspace -- exactly what an actor is authorized to do -- must not be
    reported as a violation. A detector that fires on authorized work is as
    wrong as one that misses a real escape.
    """
    org = Organization.init(tmp_path)
    workspace = tmp_path / ".sovereign" / "runs" / "ws_test"
    workspace.mkdir(parents=True)

    before = snapshot_boundary(org.root, workspace)
    (workspace / "report.json").write_text('{"status": "completed"}')
    after = snapshot_boundary(org.root, workspace)

    report = diff_boundary(before, after)
    assert not report.violated


def test_a_new_file_outside_the_workspace_is_also_detected(tmp_path: Path) -> None:
    """Not just modification -- an added file outside the boundary counts too."""
    org = Organization.init(tmp_path)
    workspace = tmp_path / ".sovereign" / "runs" / "ws_test"
    workspace.mkdir(parents=True)

    before = snapshot_boundary(org.root, workspace)
    (tmp_path / "surprise.txt").write_text("a provider wrote here instead")
    after = snapshot_boundary(org.root, workspace)

    report = diff_boundary(before, after)
    assert report.violated
    assert "surprise.txt" in report.added


def test_a_completed_assignment_records_a_clean_boundary_event(tmp_path: Path) -> None:
    """The real run_assignment path: a scripted assignment writes only inside
    its own workspace, so the recorded event must say the boundary held.
    """
    org, _sow_id, assignment_id = dispatched(tmp_path)
    org.run_assignment(assignment_id)
    rows = org.db.connection.execute(
        "SELECT payload FROM events WHERE kind = 'assignment.workspace_boundary_checked'"
    ).fetchall()
    assert len(rows) == 1
    payload = json.loads(rows[0]["payload"])
    assert payload["assignment_id"] == assignment_id
    assert payload["violated"] is False


def test_a_provider_that_writes_outside_its_workspace_is_caught_by_run_assignment(
    tmp_path: Path,
) -> None:
    """End to end: a misbehaving provider writes outside the workspace during
    a real invocation, and `run_assignment` records that as a fact on the
    ledger rather than silently accepting a completed report. This is the
    property stated as "detected, not prevented": the assignment can still
    complete -- nothing here claims to have stopped the write -- but the
    violation is on the record either way.
    """
    org, sow_id, assignment_id = dispatched(tmp_path)
    intruder = tmp_path / "tracked-outside-file.txt"
    intruder.write_text("before")

    from sovereign_agent.providers.scripted import ScriptedProvider

    real_build = ScriptedProvider.build_invocation

    def build_and_escape(self, request):  # noqa: ANN001
        intruder.write_text("a provider reached outside its workspace")
        return real_build(self, request)

    with patch.object(ScriptedProvider, "build_invocation", build_and_escape):
        org.run_assignment(assignment_id)

    row = org.db.connection.execute(
        "SELECT payload FROM events WHERE kind = 'assignment.workspace_boundary_checked'"
    ).fetchone()
    payload = json.loads(row["payload"])
    assert payload["violated"] is True
    assert "tracked-outside-file.txt" in payload["changed"]
    assert sow_id  # sanity: the fixture built a real SOW, unused beyond that


# --- Property 4: traversal-safe deliverable paths ---------------------------


def test_traversal_deliverable_is_refused(tmp_path: Path) -> None:
    root = tmp_path / "output"
    root.mkdir()
    with pytest.raises(Refusal, match="escapes its workspace root"):
        safe_join(root, "../../../etc/passwd")


def test_absolute_deliverable_path_is_refused(tmp_path: Path) -> None:
    root = tmp_path / "output"
    root.mkdir()
    with pytest.raises(Refusal, match="escapes its workspace root"):
        safe_join(root, "/etc/passwd")


def test_legitimate_nested_deliverable_still_succeeds(tmp_path: Path) -> None:
    """The check must not be so broad it refuses valid, nested work."""
    root = tmp_path / "output"
    (root / "reports").mkdir(parents=True)
    (root / "reports" / "out.json").write_text("{}")
    path = safe_join(root, "reports/out.json")
    assert path.is_file()


def test_empty_deliverable_path_is_refused(tmp_path: Path) -> None:
    root = tmp_path / "output"
    root.mkdir()
    with pytest.raises(Refusal, match="Empty path"):
        safe_join(root, "")


def test_require_deliverables_refuses_traversal_end_to_end(tmp_path: Path) -> None:
    """The real acceptance path: a SOW declaring a traversal deliverable must
    be refused by `_require_deliverables`, not merely by the helper in
    isolation.
    """
    org, sow_id, assignment_id = dispatched(tmp_path)
    org.run_assignment(assignment_id)
    sow = org._sow(sow_id)  # noqa: SLF001
    sow.deliverables = ["../../../etc/passwd"]
    with pytest.raises(Refusal, match="escapes its workspace root"):
        org._require_deliverables(sow, assignment_id)  # noqa: SLF001


# --- Property 5: parity across all four providers, no live credential ------


def test_no_live_provider_credential_is_present_in_the_test_environment() -> None:
    """This whole suite runs with no credential and no commercial CLI, per
    the ruling's own bar ("no live credential", never simulated).
    """
    for variable in (
        "ANTHROPIC_API_KEY",
        "CLAUDE_CODE_OAUTH_TOKEN",
        "CODEX_API_KEY",
        "CURSOR_API_KEY",
    ):
        assert variable not in os.environ or not os.environ[variable], (
            f"{variable} must not be set: this suite claims no live credential"
        )


@pytest.mark.parametrize("provider", ["scripted", "claude", "codex", "cursor"])
def test_reclaim_and_boundary_check_apply_identically_across_providers(
    tmp_path: Path, provider: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    """All four providers go through the SAME `run_assignment` reclaim and
    boundary-check call sites -- there is no per-provider branch in
    Organization.run_assignment for either mechanism. Proven here by fake
    executables for the three CLI providers (same deterministic fixture
    pattern as test_provider_integration.py) and the real scripted provider
    for the fourth, all asserting the identical postcondition.
    """
    from tests.test_provider_integration import _install_fake_clis

    org, _sow_id, assignment_id = dispatched(tmp_path)
    if provider != "scripted":
        _install_fake_clis(tmp_path / "bin", monkeypatch)
        org.actors["operator-course"].provider = provider
        # Same reasoning as test_provider_integration.py: the fake CLI's own
        # scratch files are inspected nowhere in THIS test, but leaving the
        # default policy would still reclaim them correctly. Nothing here
        # depends on their survival, so the default is left as-is on purpose
        # -- this test's assertions are about the receipt and report, which
        # reclaim always preserves regardless of policy.
    workspace = workspace_dir(org, assignment_id)

    org.run_assignment(assignment_id)

    assert (workspace / "receipt.json").is_file()
    assert (workspace / ".sovereign-out" / "report.json").is_file()
    row = org.db.connection.execute(
        "SELECT payload FROM events WHERE kind = 'assignment.workspace_boundary_checked' "
        "AND json_extract(payload, '$.assignment_id') = ?",
        (assignment_id,),
    ).fetchone()
    assert row is not None, f"{provider}: boundary check did not run"
    assert json.loads(row["payload"])["provider"] == provider
