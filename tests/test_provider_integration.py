from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path

import pytest

from sovereign_agent.errors import Refusal
from sovereign_agent.models import AssignmentState, Role, SowState
from sovereign_agent.organization import Organization

FAKE_CLI = r"""#!/usr/bin/env python3
import json
import os
import sys
from pathlib import Path

name = Path(sys.argv[0]).name
args = sys.argv[1:]
if args == ["--version"]:
    print(f"{name} 1.0.0-test")
    raise SystemExit(0)
if name == "codex" and args == ["exec", "--help"]:
    print("Usage: codex exec [OPTIONS] [PROMPT]\n  --json\n  --sandbox")
    raise SystemExit(0)
if name == "codex" and args == ["exec", "resume", "--help"]:
    print("Usage: codex exec resume [OPTIONS] [SESSION_ID] [PROMPT]\n  --json\n  --sandbox")
    raise SystemExit(0)
if args == ["--help"]:
    if name == "claude":
        print(
            "-p --print --output-format stream-json --verbose --resume "
            "--permission-mode [default|acceptEdits]"
        )
    else:
        print("-p --print --output-format stream-json --resume --workspace --force")
    raise SystemExit(0)

envelope = json.loads(args[-1])
workspace = Path(envelope["workspace"]["root"])
output = Path(envelope["output"]["directory"])
if name == "codex":
    sandbox = args.index("--sandbox") if "--sandbox" in args else -1
    if sandbox < 0 or args[sandbox + 1] != "workspace-write":
        print(json.dumps({"type": "turn.failed", "error": {"message": "read-only sandbox"}}))
        raise SystemExit(9)
elif name == "claude":
    permission = args.index("--permission-mode") if "--permission-mode" in args else -1
    if permission < 0 or args[permission + 1] != "acceptEdits":
        print(json.dumps({"type": "result", "subtype": "error", "is_error": True}))
        raise SystemExit(9)
elif "--force" not in args:
    print(json.dumps({"type": "result", "subtype": "error", "is_error": True}))
    raise SystemExit(9)
output.mkdir(parents=True, exist_ok=True)
(workspace / "observed-envelope.json").write_text(json.dumps(envelope, sort_keys=True))
(workspace / "observed-argv.json").write_text(json.dumps(args[:-1]))
(output / "messages").mkdir(exist_ok=True)
(output / "report.json").write_text(json.dumps({
    "schema_version": 1,
    "status": "completed",
    "changed_artifacts": [],
    "proposed_checks": ["fixture_check"],
    "questions": [],
    "notes": "fake provider completed the governed envelope"
}))

scope = envelope["statement_of_work"]["scope"]
scenario = scope.removeprefix("scenario:") if scope.startswith("scenario:") else "success"
if name == "codex":
    if scenario != "no_session":
        print(json.dumps({"type": "thread.started", "thread_id": "thread_fake"}))
    if scenario == "malformed":
        print("not json")
    if scenario == "unknown":
        print(json.dumps({"type": "future.event", "redacted": True}))
    if scenario == "provider_error":
        print(json.dumps({"type": "turn.failed", "error": {"message": "redacted"}}))
    elif scenario != "truncated":
        print(json.dumps({"type": "turn.completed", "usage": {
            "input_tokens": 10, "cached_input_tokens": 0, "output_tokens": 2,
            "reasoning_output_tokens": 0
        }}))
else:
    system = {"type": "system", "subtype": "init"}
    if scenario != "no_session":
        system["session_id"] = f"{name}_fake"
    print(json.dumps(system))
    if scenario == "malformed":
        print("not json")
    if scenario == "unknown":
        print(json.dumps({"type": "future.event", "redacted": True}))
    if scenario == "provider_error":
        print(json.dumps({
            "type": "result", "subtype": "error", "is_error": True,
            "session_id": f"{name}_fake"
        }))
    elif scenario != "truncated":
        print(json.dumps({
            "type": "result", "subtype": "success", "is_error": False,
            **({} if scenario == "no_session" else {"session_id": f"{name}_fake"}),
            "usage": {"input_tokens": 10, "output_tokens": 2}
        }))
raise SystemExit(7 if scenario == "nonzero" else 0)
"""


def _install_fake_clis(path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    path.mkdir()
    for executable in ("claude", "codex", "agent"):
        target = path / executable
        target.write_text(FAKE_CLI, encoding="utf-8")
        target.chmod(0o755)
    monkeypatch.setenv("PATH", f"{path}{os.pathsep}{os.environ['PATH']}")


def _assignment(
    root: Path, provider: str, scenario: str = "success"
) -> tuple[Organization, str, str]:
    org = Organization.init(root)
    org.actors["operator-course"].provider = provider
    outcome = org.create_outcome("fixture", "report exists", ["receipt valid"], "principal-human")
    org.activate(outcome.id, "master-course")
    sow = org.create_sow(
        outcome.id,
        (
            "Inspect the workspace and write the required report."
            if scenario == "success"
            else f"scenario:{scenario}"
        ),
        Role.OPERATOR,
        "master-course",
    )
    org.ready_sow(sow.id)
    assignment = org.assign(sow.id, "operator-course", "master-course")
    return org, sow.id, assignment.id


@pytest.mark.parametrize("provider", ["claude", "codex", "cursor"])
def test_fake_provider_reaches_review_with_truthful_receipt(
    provider: str,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _install_fake_clis(tmp_path / "bin", monkeypatch)
    org, sow_id, assignment_id = _assignment(tmp_path / "org", provider)
    assignment = org.run_assignment(assignment_id)

    assert assignment.state == AssignmentState.COMPLETED
    assert org._sow(sow_id).state == SowState.REVIEW  # noqa: SLF001
    workspace = org.root / ".sovereign" / "runs" / assignment.workspace_id
    envelope = json.loads((workspace / "observed-envelope.json").read_text())
    assert envelope["actor"]["id"] == "operator-course"
    assert envelope["actor"]["authority"] == org.actors["operator-course"].authority
    assert envelope["statement_of_work"]["id"] == sow_id
    assert envelope["output"]["report"].endswith(".sovereign-out/report.json")
    assert envelope["report_contract"]["schema"]["title"] == "ActorReport"
    observed_argv = json.loads((workspace / "observed-argv.json").read_text())
    if provider == "codex":
        assert observed_argv == ["exec", "--json", "--sandbox", "workspace-write"]
    elif provider == "claude":
        assert observed_argv[-2:] == ["--permission-mode", "acceptEdits"]
    else:
        assert "--force" in observed_argv

    receipt_text = (workspace / "receipt.json").read_text(encoding="utf-8")
    row = org.db.connection.execute("SELECT record FROM receipts").fetchone()
    assert row is not None and row["record"] == receipt_text
    receipt = json.loads(receipt_text)
    assert receipt["actor_id"] == "operator-course"
    assert receipt["provider"] == provider
    assert receipt["provider_session_ref"]
    assert receipt["status"] == "completed"
    digest = hashlib.sha256(receipt_text.encode()).hexdigest()
    assert (workspace / "receipt.json.sha256").read_text().strip() == digest


@pytest.mark.parametrize(
    ("scenario", "expected"),
    [
        ("malformed", AssignmentState.FAILED),
        ("truncated", AssignmentState.FAILED),
        ("provider_error", AssignmentState.FAILED),
        ("nonzero", AssignmentState.FAILED),
        ("no_session", AssignmentState.FAILED),
        ("unknown", AssignmentState.COMPLETED),
    ],
)
@pytest.mark.parametrize("provider", ["claude", "codex", "cursor"])
def test_protocol_failures_never_guess_success(
    provider: str,
    scenario: str,
    expected: AssignmentState,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _install_fake_clis(tmp_path / "bin", monkeypatch)
    org, _, assignment_id = _assignment(tmp_path / "org", provider, scenario)
    assignment = org.run_assignment(assignment_id)
    assert assignment.state == expected
    if expected == AssignmentState.FAILED:
        row = org.db.connection.execute("SELECT record FROM receipts").fetchone()
        assert row is not None
        assert json.loads(row["record"])["failure_category"]


@pytest.mark.parametrize(
    "error",
    [
        Refusal(
            "Provider timed out.",
            "The fixture simulated a timeout.",
            "provider-raw",
            "Retry.",
            category="timeout",
        ),
        ValueError("programmer defect"),
    ],
)
def test_escaped_failures_are_durable(
    error: Exception,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _install_fake_clis(tmp_path / "bin", monkeypatch)
    org, sow_id, assignment_id = _assignment(tmp_path / "org", "claude")
    created = org._assignment(assignment_id)  # noqa: SLF001

    def fail(*args: object, **kwargs: object) -> object:
        raise error

    monkeypatch.setattr("sovereign_agent.organization.invoke_actor", fail)
    with pytest.raises(type(error)):
        org.run_assignment(assignment_id)

    assert org._assignment(assignment_id).state == AssignmentState.FAILED  # noqa: SLF001
    assert org._sow(sow_id).state == SowState.FAILED  # noqa: SLF001
    workspace = org.root / ".sovereign" / "runs" / created.workspace_id
    receipt_text = (workspace / "receipt.json").read_text(encoding="utf-8")
    row = org.db.connection.execute("SELECT record FROM receipts").fetchone()
    assert row is not None and row["record"] == receipt_text
    receipt = json.loads(receipt_text)
    assert receipt["status"] == "failed"
    expected = "timeout" if isinstance(error, Refusal) else "internal_error"
    assert receipt["failure_category"] == expected
