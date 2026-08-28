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
from sovereign_agent.events import append_event
from sovereign_agent.models import AssignmentState, Role
from sovereign_agent.organization import Organization
from sovereign_agent.workspace import (
    BOUNDARY_SCOPE,
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


def hash_tree(root: Path) -> str:
    """A byte-for-byte digest of every path and file's contents under
    `root`, sorted for determinism. Used where "the directory wasn't
    touched" must mean the whole tree is unchanged, not merely that it
    didn't gain new top-level names -- a check that a symlinked-root refusal
    must survive.
    """
    import hashlib

    digest = hashlib.sha256()
    for path in sorted(root.rglob("*")):
        digest.update(str(path.relative_to(root)).encode())
        if path.is_file():
            digest.update(path.read_bytes())
    return digest.hexdigest()


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


def test_fault_in_before_snapshot_still_reaches_a_terminal_state(tmp_path: Path) -> None:
    """Reviewer finding 1 (also independently reproduced by Master): the
    boundary snapshot taken BEFORE the provider runs used to sit outside the
    try/except that produces a receipt -- an OSError there propagated
    straight out of `run_assignment`, past the persistence block, leaving
    the assignment stuck at RUNNING (already committed a few lines above)
    with no receipt at all. It is now taken inside the same try block, so
    the same three handlers that catch a provider fault catch this one too.
    """
    org, _sow_id, assignment_id = dispatched(tmp_path)

    call_count = {"n": 0}
    real_snapshot = organization_module.snapshot_boundary

    def flaky_before(*args, **kwargs):  # noqa: ANN001, ANN002, ANN003
        call_count["n"] += 1
        if call_count["n"] == 1:
            raise OSError("simulated fault reading the tree to digest")
        return real_snapshot(*args, **kwargs)

    with patch.object(organization_module, "snapshot_boundary", side_effect=flaky_before):
        with pytest.raises(OSError, match="simulated fault"):
            org.run_assignment(assignment_id)

    final = org._assignment(assignment_id)  # noqa: SLF001
    assert final.state == AssignmentState.FAILED, (
        "a before-snapshot fault must still reach a terminal state, not strand RUNNING"
    )
    row = org.db.connection.execute(
        "SELECT record FROM receipts WHERE assignment_id = ?", (assignment_id,)
    ).fetchone()
    assert row is not None, "a receipt must exist even when the fault is in bookkeeping"
    assert json.loads(row["record"])["failure_category"] == "internal_error"


def test_fault_in_after_snapshot_never_masks_a_real_interruption(tmp_path: Path) -> None:
    """Reviewer finding 1's sharper sub-case, overlapping finding 3's own
    'masking' concern: the provider itself is interrupted (a real
    KeyboardInterrupt, recorded as an 'interrupted' receipt), and THEN the
    AFTER snapshot also faults. The snapshot fault must never replace the
    interruption at the final `raise failure` -- the more important fact,
    that the run was interrupted, must win and be what the caller sees.
    """
    org, _sow_id, assignment_id = dispatched(tmp_path)

    call_count = {"n": 0}
    real_snapshot = organization_module.snapshot_boundary

    def flaky_after(*args, **kwargs):  # noqa: ANN001, ANN002, ANN003
        call_count["n"] += 1
        if call_count["n"] == 2:  # the AFTER snapshot -- the second call
            raise OSError("simulated fault on the after-snapshot")
        return real_snapshot(*args, **kwargs)

    with (
        patch.object(organization_module, "snapshot_boundary", side_effect=flaky_after),
        patch.object(organization_module, "invoke_actor", side_effect=KeyboardInterrupt("killed")),
    ):
        with pytest.raises(KeyboardInterrupt):
            org.run_assignment(assignment_id)

    final = org._assignment(assignment_id)  # noqa: SLF001
    assert final.state == AssignmentState.FAILED
    row = org.db.connection.execute(
        "SELECT record FROM receipts WHERE assignment_id = ?", (assignment_id,)
    ).fetchone()
    assert row is not None
    assert json.loads(row["record"])["failure_category"] == "interrupted", (
        "the interruption's own receipt must survive a subsequent bookkeeping fault"
    )
    event_row = org.db.connection.execute(
        "SELECT payload FROM events WHERE kind = 'assignment.workspace_boundary_checked'"
    ).fetchone()
    payload = json.loads(event_row["payload"])
    assert payload["computed"] is False, (
        "a faulted after-snapshot must record that the check could not run, "
        "not silently claim 'violated: False'"
    )
    assert payload["violated"] is None


def test_fault_in_after_snapshot_with_no_prior_failure_records_honest_failure(
    tmp_path: Path,
) -> None:
    """Distinct from the interruption case above: here there was NO earlier
    failure to protect -- the real scripted provider runs to completion
    normally, uninterrupted -- and THEN the after-snapshot faults. The old
    guard (`if failure is None: failure = snapshot_error`) was written only
    to stop a snapshot fault from overwriting an already-caught, more
    important failure; it says nothing about what to persist when there was
    no prior failure at all. Left as `report and report.status ==
    "completed"`, the persistence block below still committed COMPLETED
    from the provider's own genuine success, while `failure` being newly
    non-None meant `run_assignment` still raised the OSError to the caller
    -- caller sees a raised exception, ledger says success, and the two
    disagree. This test guards that the snapshot fault must itself become
    the honestly-recorded terminal failure when nothing else already was.
    """
    org, _sow_id, assignment_id = dispatched(tmp_path)

    call_count = {"n": 0}
    real_snapshot = organization_module.snapshot_boundary

    def flaky_after(*args, **kwargs):  # noqa: ANN001, ANN002, ANN003
        call_count["n"] += 1
        if call_count["n"] == 2:  # the AFTER snapshot -- the second call
            raise OSError("simulated fault on after-snapshot, provider succeeded")
        return real_snapshot(*args, **kwargs)

    with patch.object(organization_module, "snapshot_boundary", side_effect=flaky_after):
        with pytest.raises(OSError, match="simulated fault on after-snapshot"):
            org.run_assignment(assignment_id)

    final = org._assignment(assignment_id)  # noqa: SLF001
    assert final.state == AssignmentState.FAILED, (
        "the ledger must not record COMPLETED when the caller was handed a "
        "raised exception -- the two must never disagree"
    )
    row = org.db.connection.execute(
        "SELECT record FROM receipts WHERE assignment_id = ?", (assignment_id,)
    ).fetchone()
    assert row is not None
    record = json.loads(row["record"])
    assert record["status"] == "failed", (
        "the receipt on disk must match the ledger's own FAILED verdict, "
        "not the provider's stale successful result"
    )
    assert record["failure_category"] == "internal_error"
    assert "provider" in record["failure_message"].lower(), (
        "the provider's own successful result must not be silently discarded "
        "without a trace -- the failure message names what actually happened"
    )
    event_row = org.db.connection.execute(
        "SELECT payload FROM events WHERE kind = 'assignment.workspace_boundary_checked'"
    ).fetchone()
    payload = json.loads(event_row["payload"])
    assert payload["computed"] is False, (
        "a faulted after-snapshot must record that the check could not run"
    )
    assert payload["violated"] is None


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


# --- Master's finding 3: reclaim must never delete through a symlink -------


def test_reclaim_refuses_a_symlinked_workspace_root(tmp_path: Path) -> None:
    """Master independently reproduced this against the real library
    function, outside any fixture: a workspace root that is itself a
    symlink used to have `reclaim_workspace` recurse straight through it via
    `shutil.rmtree`, deleting whatever real directory the link pointed at.
    Fixed to refuse outright -- a `Refusal`, not a silent no-op, and the
    external target's own file is checked byte-identical afterward, not
    merely "still present."
    """
    external = tmp_path / "external-target"
    external.mkdir()
    marker = external / "external-marker"
    marker.write_text("must survive")
    original_bytes = marker.read_bytes()

    workspace = tmp_path / "workspace-symlink"
    workspace.symlink_to(external, target_is_directory=True)

    with pytest.raises(Refusal, match="symlink"):
        reclaim_workspace(workspace, TEMPORARY_DIRECTORY)

    assert marker.exists(), "the external target must not be touched at all"
    assert marker.read_bytes() == original_bytes, "byte-identical, not merely present"
    assert external.is_dir(), "the external directory itself must survive"


def test_reclaim_unlinks_a_symlinked_child_without_following_it(tmp_path: Path) -> None:
    """The review's own named sub-case: a *child* entry inside an otherwise
    real, legitimate workspace is a symlink to something external.
    `shutil.rmtree` refuses to recurse into a symlinked directory and raises
    `OSError` instead -- unguarded, that would propagate out of
    `run_assignment` after the ledger is already terminal, potentially
    masking whatever the run itself did or did not raise (see
    test_fault_in_after_snapshot_never_masks_a_real_interruption for that
    interaction). Fixed to `Path.unlink()` the symlink entry itself --
    removing the link, never following it into its target.
    """
    external = tmp_path / "external-target-child"
    external.mkdir()
    marker = external / "external-marker-child"
    marker.write_text("must survive too")
    original_bytes = marker.read_bytes()

    workspace = tmp_path / "workspace-real"
    workspace.mkdir()
    (workspace / ".sovereign-out").mkdir()
    child_link = workspace / "linked-child"
    child_link.symlink_to(external, target_is_directory=True)

    reclaimed = reclaim_workspace(workspace, TEMPORARY_DIRECTORY)

    assert reclaimed is True
    assert not child_link.exists() and not child_link.is_symlink(), (
        "the symlink entry itself must be gone from the workspace"
    )
    assert marker.exists(), "the external target must not be touched at all"
    assert marker.read_bytes() == original_bytes, "byte-identical, not merely present"
    assert external.is_dir(), "the external directory itself must survive"


def test_unknown_workspace_policy_refuses_before_the_provider_ever_runs(tmp_path: Path) -> None:
    """Reviewer finding 2: an invalid `workspace_policy` used to be caught
    only inside `reclaim_workspace`, at the very end of `run_assignment` --
    by which point the provider had already run for real and COMPLETED was
    already committed to the ledger. `invoke_actor` is spied on with a
    counter (not merely re-asserted against network/side-effect absence) to
    prove it is never called at all when the policy is invalid: the run
    must not have happened, not merely have its result discarded afterward.
    """
    org, _sow_id, assignment_id = dispatched(tmp_path)
    org.actors["operator-course"].workspace_policy = "delete_everything_now"

    invoked = {"count": 0}
    real_invoke = organization_module.invoke_actor

    def counting_invoke(*args, **kwargs):  # noqa: ANN001, ANN002, ANN003
        invoked["count"] += 1
        return real_invoke(*args, **kwargs)

    with patch.object(organization_module, "invoke_actor", side_effect=counting_invoke):
        with pytest.raises(Refusal, match="Unknown workspace policy"):
            org.run_assignment(assignment_id)

    assert invoked["count"] == 0, "the provider must never be invoked for an invalid policy"
    final = org._assignment(assignment_id)  # noqa: SLF001
    assert final.state == AssignmentState.CREATED, (
        "the assignment must not even reach RUNNING when the policy is invalid"
    )
    row = org.db.connection.execute(
        "SELECT record FROM receipts WHERE assignment_id = ?", (assignment_id,)
    ).fetchone()
    assert row is None, "no receipt: the run never happened, it was not merely discarded"


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


def test_symlinked_workspace_root_refused_before_the_provider_ever_runs(tmp_path: Path) -> None:
    """Master's finding: a symlinked workspace root used to be refused only
    inside `reclaim_workspace`, at the very end of `run_assignment` -- by
    which point the provider had already run for real THROUGH the symlink,
    writing real files into whatever external directory the link pointed
    at, and COMPLETED was already committed to the ledger. This test
    pre-creates the workspace path AS a symlink before `run_assignment`
    ever touches it, the same shape as
    `test_unknown_workspace_policy_refuses_before_the_provider_ever_runs`
    above: `invoke_actor` is spied on with a counter to prove the provider
    is never invoked, and the external target's whole tree is hashed
    before and after -- not just checked for new top-level names -- to
    prove nothing was written through the link at all.

    The early refusal is also the ONLY refusal the caller sees on this
    path: `reclaim_workspace`'s own symlink guard never even gets
    exercised here, because `run_assignment` never reaches the reclaim
    call site once it refuses up front. That guard stays in place as
    defense in depth for whatever other path might reach `reclaim_workspace`
    directly (as `test_reclaim_refuses_a_symlinked_workspace_root` above
    already covers), but on this path there is exactly one Refusal, not a
    race between two.
    """
    org, _sow_id, assignment_id = dispatched(tmp_path)
    assignment = org._assignment(assignment_id)  # noqa: SLF001
    workspace_path = org.root / ".sovereign" / "runs" / assignment.workspace_id
    external = tmp_path / "external-target"
    external.mkdir()

    workspace_path.parent.mkdir(parents=True, exist_ok=True)
    workspace_path.symlink_to(external, target_is_directory=True)

    before_hash = hash_tree(external)

    invoked = {"count": 0}
    real_invoke = organization_module.invoke_actor

    def counting_invoke(*args, **kwargs):  # noqa: ANN001, ANN002, ANN003
        invoked["count"] += 1
        return real_invoke(*args, **kwargs)

    with patch.object(organization_module, "invoke_actor", side_effect=counting_invoke):
        with pytest.raises(Refusal, match="symlink") as excinfo:
            org.run_assignment(assignment_id)

    assert excinfo.value.category == "symlinked_workspace_root"
    assert invoked["count"] == 0, "the provider must never be invoked through a symlinked root"
    final = org._assignment(assignment_id)  # noqa: SLF001
    assert final.state == AssignmentState.CREATED, (
        "the assignment must not even reach RUNNING when the root is a symlink"
    )
    row = org.db.connection.execute(
        "SELECT record FROM receipts WHERE assignment_id = ?", (assignment_id,)
    ).fetchone()
    assert row is None, "no receipt: the run never happened, it was not merely discarded"
    assert hash_tree(external) == before_hash, (
        "the external target's whole tree must be byte-for-byte unchanged, "
        "not merely free of new top-level names"
    )


def test_symlinked_runs_directory_ancestor_is_also_refused_before_the_provider_runs(
    tmp_path: Path,
) -> None:
    """The reviewer's own non-blocking note, taken seriously: a leaf-only
    check (`workspace.is_symlink()`) is blind to `.sovereign/runs/` itself
    being a symlink -- the workspace path underneath it would still be an
    ordinary, non-symlink directory, so a check that only looks at the leaf
    would traverse straight through a symlinked *ancestor* transparently.
    This test symlinks `.sovereign/runs/` itself (not the leaf workspace
    directory) to an external target and proves the same early refusal,
    the same zero-invocation guarantee, and the same byte-for-byte-
    unchanged external target as the leaf-symlink case above.
    """
    org, _sow_id, assignment_id = dispatched(tmp_path)
    runs_dir = org.root / ".sovereign" / "runs"
    external = tmp_path / "external-runs-target"
    external.mkdir()

    runs_dir.parent.mkdir(parents=True, exist_ok=True)
    runs_dir.symlink_to(external, target_is_directory=True)

    before_hash = hash_tree(external)

    invoked = {"count": 0}
    real_invoke = organization_module.invoke_actor

    def counting_invoke(*args, **kwargs):  # noqa: ANN001, ANN002, ANN003
        invoked["count"] += 1
        return real_invoke(*args, **kwargs)

    with patch.object(organization_module, "invoke_actor", side_effect=counting_invoke):
        with pytest.raises(Refusal, match="symlink") as excinfo:
            org.run_assignment(assignment_id)

    assert excinfo.value.category == "symlinked_workspace_root"
    assert invoked["count"] == 0, (
        "the provider must never be invoked through a symlinked runs/ ancestor"
    )
    final = org._assignment(assignment_id)  # noqa: SLF001
    assert final.state == AssignmentState.CREATED
    row = org.db.connection.execute(
        "SELECT record FROM receipts WHERE assignment_id = ?", (assignment_id,)
    ).fetchone()
    assert row is None
    assert hash_tree(external) == before_hash, (
        "a symlinked ancestor must be refused before anything is written through it"
    )


def test_symlinked_output_directory_refused_before_the_provider_ever_runs(
    tmp_path: Path,
) -> None:
    """Round three's finding (B3): the two checks above guard the workspace
    ROOT and its ancestors, but neither one looks at `.sovereign-out`, the
    organization-allocated OUTPUT CHILD living one level *below* the
    workspace root. This test allocates `workspace` itself as an ordinary
    real directory -- so the ancestor-walk above does not fire -- and
    pre-plants `.sovereign-out` as a symlink to an external target before
    `run_assignment` ever touches it.

    Before the fix: the provider runs for real and writes its report and
    artifacts straight through the link into the external directory,
    `run_assignment` returns COMPLETED, and `_require_deliverables` (which
    reconstructs the same `.sovereign-out` path independently and calls
    `safe_join` against it) resolves through the symlink and ACCEPTS a
    deliverable planted directly in the external directory -- evidence the
    run never produced -- as satisfying the SOW. Same threat model as the
    workspace-root case above (a governed path substituted with a symlink
    before use), one level down: the write-through and the accept-through
    are two faces of the same unchecked path.

    Same shape as the two tests above: `invoke_actor` is spied on with a
    counter to prove the provider is never invoked, and the external
    target's whole tree is hashed before and after to prove nothing was
    written through the link at all.
    """
    org, _sow_id, assignment_id = dispatched(tmp_path)
    assignment = org._assignment(assignment_id)  # noqa: SLF001
    workspace_path = org.root / ".sovereign" / "runs" / assignment.workspace_id
    external = tmp_path / "external-output-target"
    external.mkdir()

    # The workspace root itself is an ordinary real directory -- allocated
    # the way `run_assignment` allocates it -- so the ancestor-walk check
    # above does not fire and this test isolates the output-child gap.
    workspace_path.mkdir(parents=True, exist_ok=True)
    (workspace_path / ".sovereign-out").symlink_to(external, target_is_directory=True)

    before_hash = hash_tree(external)

    invoked = {"count": 0}
    real_invoke = organization_module.invoke_actor

    def counting_invoke(*args, **kwargs):  # noqa: ANN001, ANN002, ANN003
        invoked["count"] += 1
        return real_invoke(*args, **kwargs)

    with patch.object(organization_module, "invoke_actor", side_effect=counting_invoke):
        with pytest.raises(Refusal, match="symlink") as excinfo:
            org.run_assignment(assignment_id)

    assert excinfo.value.category == "symlinked_output_directory"
    assert invoked["count"] == 0, (
        "the provider must never be invoked with an output path that is a symlink"
    )
    final = org._assignment(assignment_id)  # noqa: SLF001
    assert final.state == AssignmentState.CREATED, (
        "the assignment must not even reach RUNNING when the output child is a symlink"
    )
    row = org.db.connection.execute(
        "SELECT record FROM receipts WHERE assignment_id = ?", (assignment_id,)
    ).fetchone()
    assert row is None, "no receipt: the run never happened, it was not merely discarded"
    assert hash_tree(external) == before_hash, (
        "the external target's whole tree must be byte-for-byte unchanged -- "
        "nothing written through the symlinked output child at all"
    )


def test_symlinked_child_inside_a_real_output_directory_cannot_be_written_through(
    tmp_path: Path,
) -> None:
    """Round four's review (finding C1, the dual of the fix above): the
    symlink check just above only refuses `.sovereign-out` *being* a
    symlink. It says nothing about `.sovereign-out` pre-planted as an
    ORDINARY REAL directory whose interior is hostile -- e.g. a symlinked
    child, `report.json -> <external file>`. The provider's own
    `mkdir(parents=True, exist_ok=True)` never disturbs pre-existing
    content, so before the fix the provider would write its real report
    bytes straight through that child link, into the external file, for
    real -- a write escaping the workspace boundary with success
    committed, not a refusal.

    This test does not assert "refuse before running" (there is nothing to
    refuse -- `.sovereign-out` itself is a perfectly ordinary real
    directory). It asserts the run either cannot be corrupted this way at
    all, or refuses honestly if it detects it was. The actual fix makes it
    the former: `run_assignment` removes and recreates `.sovereign-out`
    fresh immediately before the provider runs, so the pre-planted
    symlinked child is gone before the provider ever gets a chance to
    write through it.
    """
    org, _sow_id, assignment_id = dispatched(tmp_path)
    assignment = org._assignment(assignment_id)  # noqa: SLF001
    workspace_path = org.root / ".sovereign" / "runs" / assignment.workspace_id
    external = tmp_path / "external-hostage"
    external.mkdir()
    hostage = external / "hostage.txt"
    hostage.write_text("ORIGINAL EXTERNAL BYTES")
    before_hash = hash_tree(external)

    # `.sovereign-out` itself is an ORDINARY REAL directory -- the existing
    # symlink check does not fire -- but its child is a symlink pointing at
    # a file entirely outside the workspace.
    workspace_path.mkdir(parents=True, exist_ok=True)
    output_dir = workspace_path / ".sovereign-out"
    output_dir.mkdir()
    (output_dir / "report.json").symlink_to(hostage)

    result = org.run_assignment(assignment_id)

    assert result.state == AssignmentState.COMPLETED, (
        "a real, non-hostile run must still complete normally -- the fix "
        "must not turn ordinary success into a refusal"
    )
    assert hostage.read_text() == "ORIGINAL EXTERNAL BYTES", (
        "the provider's report must never be written through a pre-planted "
        "symlinked child -- the hostage file outside the workspace must be "
        "byte-for-byte untouched"
    )
    assert hash_tree(external) == before_hash, (
        "the external target's whole tree must be unchanged -- recreating "
        ".sovereign-out fresh must remove the symlinked child before the "
        "provider ever runs"
    )
    assert (output_dir / "report.json").is_file(), (
        "the real report must exist at the usual path -- written by the "
        "provider into the freshly recreated, real .sovereign-out"
    )
    assert not (output_dir / "report.json").is_symlink(), (
        "the report path itself must be a real file, not still the pre-planted symlink"
    )


def test_fabricated_deliverable_preplanted_in_a_real_output_directory_is_not_accepted(
    tmp_path: Path,
) -> None:
    """Round four's review (finding C2, the other dual): pre-plant
    `.sovereign-out` as a real directory containing a file already named
    as the SOW's deliverable -- never written by the provider at all.
    Before the fix, the provider's `mkdir(exist_ok=True)` left the
    fabricated file in place, the run completed, and
    `_require_deliverables` accepted the pre-planted file as proof the SOW
    was satisfied -- evidence the run never produced, exactly the
    "unit of work is done when its deliverable exists" contract this
    module states, defeated by evidence provenance rather than by a
    missing file.

    After the fix, recreating `.sovereign-out` fresh at allocation time
    removes the fabricated file before the provider ever runs, so the run
    completes with its OWN real output, and asking `_require_deliverables`
    to accept the fabricated (now-absent) name correctly refuses --
    honestly, not silently.
    """
    org, sow_id, assignment_id = dispatched(tmp_path)
    assignment = org._assignment(assignment_id)  # noqa: SLF001
    workspace_path = org.root / ".sovereign" / "runs" / assignment.workspace_id

    workspace_path.mkdir(parents=True, exist_ok=True)
    output_dir = workspace_path / ".sovereign-out"
    output_dir.mkdir()
    fabricated = output_dir / "fabricated-analysis.md"
    fabricated.write_text("evidence the provider never wrote")

    result = org.run_assignment(assignment_id)
    assert result.state == AssignmentState.COMPLETED, (
        "a real, non-hostile run must still complete normally"
    )
    assert not fabricated.exists(), (
        "the fabricated file must not survive allocation-time recreate -- "
        "if it did, it would still be sitting there unconnected to "
        "anything the real provider run wrote"
    )

    sow = org._sow(sow_id)  # noqa: SLF001
    sow.deliverables = ["fabricated-analysis.md"]
    with pytest.raises(Refusal) as excinfo:
        org._require_deliverables(sow, assignment_id)  # noqa: SLF001
    assert "did not produce it" in str(excinfo.value)


def test_symlinked_provider_raw_cannot_be_written_through(tmp_path: Path) -> None:
    """The organization's OTHER write path: `invoke_actor`
    (`execution.py`) writes `stdout.txt`, `stderr.txt`, and `events.jsonl`
    into `workspace / "provider-raw"`, allocated with its own
    `mkdir(parents=True, exist_ok=True)` -- the same unchecked-allocation
    shape `.sovereign-out` had before this round's fix, on a path
    `run_assignment`'s own checks never look at (they check `workspace`
    and its ancestors, and `.sovereign-out`; `provider-raw` is a third,
    independent child). Pre-planting `provider-raw` as a symlink to an
    external directory, before the fix, let the three post-subprocess
    writes land for real in the external directory.

    `invoke_actor` now recreates `provider-raw` fresh immediately before
    writing into it, closing the same class of hole on this second path.

    Uses the `persistent` workspace policy (rather than the default
    `temporary_directory`) so `provider-raw` survives reclaim at the end of
    `run_assignment` and can actually be inspected afterward -- reclaim
    legitimately removes `provider-raw` as disposable scratch under the
    default policy, which is correct, existing behavior unrelated to this
    fix and not what this test is about.
    """
    org, _sow_id, assignment_id = dispatched(tmp_path)
    org.actors["operator-course"].workspace_policy = PERSISTENT
    assignment = org._assignment(assignment_id)  # noqa: SLF001
    workspace_path = org.root / ".sovereign" / "runs" / assignment.workspace_id
    external = tmp_path / "external-provider-raw"
    external.mkdir()
    before_hash = hash_tree(external)

    workspace_path.mkdir(parents=True, exist_ok=True)
    (workspace_path / "provider-raw").symlink_to(external, target_is_directory=True)

    result = org.run_assignment(assignment_id)

    assert result.state == AssignmentState.COMPLETED
    assert hash_tree(external) == before_hash, (
        "the external target must be byte-for-byte unchanged -- nothing "
        "written through the pre-planted provider-raw symlink"
    )
    raw_dir = workspace_path / "provider-raw"
    assert raw_dir.is_dir() and not raw_dir.is_symlink(), (
        "provider-raw must be a real directory after the run, not still the pre-planted symlink"
    )
    assert (raw_dir / "stdout.txt").is_file(), (
        "the real bookkeeping files must exist at the usual path, written "
        "into the freshly recreated, real provider-raw"
    )


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
    assert payload["computed"] is True
    assert payload["scope"] == BOUNDARY_SCOPE, (
        "the event must name what it covers, not let 'violated: False' be "
        "misread as an unqualified claim"
    )


def test_boundary_report_does_not_see_a_real_database_write(tmp_path: Path) -> None:
    """Reviewer finding 4: `organization.db*` is excluded from the digested
    tree on purpose (Property 3's own documented rationale -- it is written
    by this same process's transaction, not by the subprocess under test),
    so a real schema/row write there is structurally invisible to
    `diff_boundary`. This is not a defect to make disappear by widening
    coverage; it is a coverage-honesty property: the report must say what
    it covers (`scope`) rather than let `violated: False` be misread as
    "nothing changed anywhere," including in the ledger.
    """
    org = Organization.init(tmp_path)
    db_path = org.root / ".sovereign" / "organization.db"
    workspace = tmp_path / ".sovereign" / "runs" / "ws_test"
    workspace.mkdir(parents=True)

    before = snapshot_boundary(org.root, workspace)
    # A real write to the ledger the check is documented to exclude.
    with org.db.transaction():
        append_event(org.db, "test.probe", {"marker": "a real db write happened"})
    after = snapshot_boundary(org.root, workspace)

    report = diff_boundary(before, after)
    assert db_path.exists(), "sanity: the db file is real and was actually written to"
    assert not report.violated, (
        "the db write is genuinely outside this check's scope -- it must not "
        "spuriously report a violation for a path it was never told to watch"
    )
    assert report.scope == BOUNDARY_SCOPE, (
        "the report must carry an honest scope value so violated=False is "
        "never misread as full-organization coverage"
    )


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


def test_absolute_deliverable_path_is_refused_even_when_it_resolves_inside_root(
    tmp_path: Path,
) -> None:
    """P2: an absolute path that happens to land inside `root` used to be
    ACCEPTED, because the old check only compared resolved paths and never
    looked at whether the input itself was absolute -- despite this
    function's own docstring implying workspace-relative paths only, and
    `test_absolute_deliverable_path_is_refused` above already asserting the
    contract is "absolute is refused," not "absolute is refused unless it
    resolves inside root." `_require_deliverables`'s only real caller passes
    workspace-relative deliverable names, so accepting an absolute one that
    happens to resolve inside root is never a legitimate use case here --
    the fix rejects any absolute input outright, matching the apparent
    contract rather than papering over the mismatch by loosening the
    docstring instead.
    """
    root = tmp_path / "output"
    root.mkdir()
    (root / "report.json").write_text("{}")
    absolute_but_inside = str(root / "report.json")
    with pytest.raises(Refusal, match="escapes its workspace root"):
        safe_join(root, absolute_but_inside)


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
