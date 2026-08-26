"""The Scripted provider's failure matrix, driven through the REAL code path.

Every learner runs the Scripted provider and none of them need a credential for
it, yet the provider integration matrix parametrized ["claude","codex","cursor"]
only -- the one provider a reader actually exercises had no failure tests.

The first version of this file was worse than that gap. Five of its nine tests
patched `invoke_actor` with an ALREADY-CLASSIFIED `Refusal`, so they asserted
that `run_assignment` persists a refusal and never that timeout detection, JSONL
parsing or report validation happen at all. A test named for one property while
exercising another -- the exact defect this project exists to remove, committed
inside the fix for it. Reported on PR #25.

So every case here runs a REAL subprocess. The provider's `build_invocation` is
pointed at a scenario script that misbehaves in one specific way; everything
downstream -- process launch, stream capture, report parsing, receipt writing,
state transition -- is the production path.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

import sovereign_agent.organization as organization_module
from reference_organizations.store import seed
from sovereign_agent.errors import Refusal
from sovereign_agent.models import AssignmentState, Role
from sovereign_agent.providers.base import InvocationSpec
from sovereign_agent.providers.scripted import ScriptedProvider

# --- scenario scripts: real programs, each misbehaving in exactly one way -----

SCENARIOS: dict[str, str] = {
    # Writes a valid completed report, like the real fixture.
    "success": r"""
import json, pathlib, sys
out = pathlib.Path(sys.argv[1]); out.mkdir(parents=True, exist_ok=True)
(out / "report.json").write_text(json.dumps({
    "schema_version": 1, "status": "completed", "changed_artifacts": [],
    "proposed_restock_units": 6, "proposed_checks": [], "questions": [], "notes": "ok"}))
""",
    # Reports its own failure honestly.
    "provider_failure": r"""
import json, pathlib, sys
out = pathlib.Path(sys.argv[1]); out.mkdir(parents=True, exist_ok=True)
(out / "report.json").write_text(json.dumps({
    "schema_version": 1, "status": "failed", "changed_artifacts": [],
    "questions": [], "notes": "the shelf was locked"}))
""",
    # Emits unparseable JSONL on stdout, then a valid report.
    "malformed_stream": r"""
import json, pathlib, sys
sys.stdout.write("{this is not json\n")
sys.stdout.write("{\"also\": \"unterminated\"\n")
out = pathlib.Path(sys.argv[1]); out.mkdir(parents=True, exist_ok=True)
(out / "report.json").write_text(json.dumps({
    "schema_version": 1, "status": "completed", "changed_artifacts": [],
    "questions": [], "notes": ""}))
""",
    # report.json exists but is not JSON at all.
    "malformed_report": r"""
import pathlib, sys
out = pathlib.Path(sys.argv[1]); out.mkdir(parents=True, exist_ok=True)
(out / "report.json").write_text("{not json at all")
""",
    # Valid JSON that violates the ActorReport contract.
    "invalid_report": r"""
import json, pathlib, sys
out = pathlib.Path(sys.argv[1]); out.mkdir(parents=True, exist_ok=True)
(out / "report.json").write_text(json.dumps({"status": "banana", "surprise": True}))
""",
    # Exits non-zero, writing nothing.
    "nonzero_exit": r"""
import sys
sys.stderr.write("provider crashed\n")
raise SystemExit(3)
""",
    # Succeeds silently but never writes the mandatory report.
    "missing_report": r"""
import pathlib, sys
pathlib.Path(sys.argv[1]).mkdir(parents=True, exist_ok=True)
""",
    # Hangs, so the timeout must fire.
    "hang": r"""
import time
time.sleep(30)
""",
}


@pytest.fixture
def scenario(tmp_path_factory: pytest.TempPathFactory):
    """Point the Scripted provider at a real script that misbehaves on cue."""
    scripts = tmp_path_factory.mktemp("scenarios")
    for name, body in SCENARIOS.items():
        (scripts / f"{name}.py").write_text(body, encoding="utf-8")

    def use(name: str, timeout: float = 60.0):
        script = scripts / f"{name}.py"

        def build(self: ScriptedProvider, request):  # noqa: ANN001
            return InvocationSpec(
                argv=[sys.executable, str(script), str(request.output), request.prompt],
                cwd=request.workspace,
            )

        # invoke_actor calls run_spec(spec) with no timeout argument, so the
        # 60s default is what production uses. Shorten it for the hang case by
        # wrapping the real run_spec rather than replacing it -- the timeout
        # that fires is still subprocess's, not a stub's.
        import sovereign_agent.execution as execution_module

        real_run_spec = execution_module.run_spec

        def shortened(spec, timeout_seconds: float = timeout):  # noqa: ANN001
            return real_run_spec(spec, timeout=timeout_seconds)

        return (
            patch.object(ScriptedProvider, "build_invocation", build),
            patch.object(execution_module, "run_spec", shortened),
        )

    return use


def dispatched(root: Path) -> tuple[organization_module.Organization, str]:
    org = organization_module.Organization.init(root)
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
    return org, org.assign(sow.id, "operator-course", "master-course").id


def receipts(org) -> list[dict]:  # noqa: ANN001
    return [
        json.loads(row["record"])
        for row in org.db.connection.execute("SELECT record FROM receipts").fetchall()
    ]


def assert_failed_closed(org, assignment_id: str, category: str | None = None) -> None:  # noqa: ANN001
    """The invariant every non-success case must satisfy, whatever went wrong."""
    state = org._assignment(assignment_id).state  # noqa: SLF001
    assert state is not AssignmentState.RUNNING, "left recorded as RUNNING: the ledger lies"
    assert state in {AssignmentState.FAILED, AssignmentState.BLOCKED}
    written = receipts(org)
    assert written, "no durable receipt: the failure left no record"
    assert written[-1]["status"] != "completed", "a failure was recorded as success"
    assert written[-1]["assignment_id"] == assignment_id
    assert written[-1]["failure_category"], "a failure with no category"
    if category is not None:
        assert written[-1]["failure_category"] == category
    return written[-1]["failure_category"]


def run(org, assignment_id: str, patches) -> BaseException | None:  # noqa: ANN001
    build_patch, timeout_patch = patches
    with build_patch, timeout_patch:
        try:
            org.run_assignment(assignment_id)
        except BaseException as error:  # noqa: BLE001 - the refusal IS the result
            return error
    return None


# --- 1. success -------------------------------------------------------------


def test_success_records_a_completed_receipt(tmp_path: Path, scenario) -> None:  # noqa: ANN001
    org, assignment_id = dispatched(tmp_path)
    assert run(org, assignment_id, scenario("success")) is None
    assert org._assignment(assignment_id).state is AssignmentState.COMPLETED  # noqa: SLF001
    assert receipts(org)[-1]["status"] == "completed"
    assert receipts(org)[-1]["failure_category"] is None


# --- 2. the provider reports its own failure --------------------------------


def test_provider_reported_failure(tmp_path: Path, scenario) -> None:  # noqa: ANN001
    org, assignment_id = dispatched(tmp_path)
    run(org, assignment_id, scenario("provider_failure"))
    assert_failed_closed(org, assignment_id, "actor_reported_failure")


# --- 3. timeout: a real hang, a real timeout --------------------------------


def test_a_hanging_provider_times_out(tmp_path: Path, scenario) -> None:  # noqa: ANN001
    """The scenario really sleeps; run_spec's timeout really fires."""
    org, assignment_id = dispatched(tmp_path)
    error = run(org, assignment_id, scenario("hang", timeout=1.0))
    assert isinstance(error, Refusal)
    assert_failed_closed(org, assignment_id, "timeout")


# --- 4. catchable interruption ----------------------------------------------


@pytest.mark.parametrize("interruption", [KeyboardInterrupt, SystemExit])
def test_catchable_interruption_never_leaves_a_running_assignment(
    tmp_path: Path, interruption: type[BaseException]
) -> None:
    """KeyboardInterrupt and SystemExit are NOT Exception.

    They escaped `run_assignment`, skipped the persistence block, and left the
    assignment recorded RUNNING with no receipt. Fail-open, in the unit whose
    subject is that a status must not outrun the world.

    This one legitimately injects at the boundary: the point is what the
    ORGANIZATION does when the interpreter interrupts it, not what a subprocess
    emits. A hard kill stays Unit 8 -- a process cannot record its own death.
    """
    org, assignment_id = dispatched(tmp_path)
    with patch.object(organization_module, "invoke_actor", side_effect=interruption("stop")):
        with pytest.raises(interruption):
            org.run_assignment(assignment_id)
    assert_failed_closed(org, assignment_id, "interrupted")


# --- 5. malformed JSONL stream ----------------------------------------------


def test_malformed_event_stream_fails_closed(tmp_path: Path, scenario) -> None:  # noqa: ANN001
    """Real unparseable lines on stdout, parsed by the real stream reader."""
    org, assignment_id = dispatched(tmp_path)
    run(org, assignment_id, scenario("malformed_stream"))
    category = assert_failed_closed(org, assignment_id)
    assert category in {"malformed_stream", "missing_terminal", "provider_error"}


# --- 6. malformed report (not JSON) -----------------------------------------


def test_malformed_report_fails_closed(tmp_path: Path, scenario) -> None:  # noqa: ANN001
    """The earlier version called a store helper and asserted no receipt at all."""
    org, assignment_id = dispatched(tmp_path)
    run(org, assignment_id, scenario("malformed_report"))
    assert_failed_closed(org, assignment_id, "invalid_report")


# --- 7. invalid report (valid JSON, violates the contract) ------------------


def test_invalid_report_fails_closed(tmp_path: Path, scenario) -> None:  # noqa: ANN001
    org, assignment_id = dispatched(tmp_path)
    run(org, assignment_id, scenario("invalid_report"))
    assert_failed_closed(org, assignment_id, "invalid_report")


# --- 8. no guessed success --------------------------------------------------


@pytest.mark.parametrize(
    "name",
    [
        "provider_failure",
        "malformed_stream",
        "malformed_report",
        "invalid_report",
        "nonzero_exit",
        "missing_report",
    ],
)
def test_no_failure_mode_is_ever_recorded_as_success(tmp_path: Path, scenario, name: str) -> None:  # noqa: ANN001
    """Sweep every REAL misbehaviour: none may yield status=completed.

    Parametrized over scenario scripts rather than over injected refusals, so a
    new failure path that forgets to write a receipt fails here instead of
    shipping as a silent success.
    """
    org, assignment_id = dispatched(tmp_path / name)
    run(org, assignment_id, scenario(name))
    assert_failed_closed(org, assignment_id)
