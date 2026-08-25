"""Opt-in live probes and assignments. Excluded from default pytest."""

from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path

import pytest

from sovereign_agent.models import ActorReport, AssignmentState, Role, SowState
from sovereign_agent.organization import Organization
from sovereign_agent.providers import PROVIDERS

pytestmark = pytest.mark.live


@pytest.mark.parametrize("name", ["claude", "codex", "cursor"])
def test_installed_cli_probe_does_not_submit_work(name: str) -> None:
    provider = PROVIDERS[name]
    caps = provider.probe()
    if not caps.available:
        pytest.skip(f"{provider.executable} is not on PATH")
    assert caps.available
    assert caps.evidence
    assert all(item.exit_code == 0 for item in caps.evidence if item.error is None)


def _git(root: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=root,
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


def _fixture_repo(root: Path) -> Organization:
    org = Organization.init(root)
    (root / "README.md").write_text("# Disposable provider smoke\n", encoding="utf-8")
    (root / ".gitignore").write_text(
        ".sovereign/\nartifacts/\ngovernance/\nsovereign.toml\n",
        encoding="utf-8",
    )
    _git(root, "init", "-q")
    _git(root, "add", ".")
    _git(
        root,
        "-c",
        "user.name=Sovereign Agent",
        "-c",
        "user.email=fixture@example.invalid",
        "commit",
        "-qm",
        "fixture trunk",
    )
    return org


@pytest.mark.parametrize("name", ["claude", "codex", "cursor"])
@pytest.mark.parametrize("mode", ["read-only", "workspace-write"])
def test_live_assignment_reaches_review_without_moving_trunk(
    name: str,
    mode: str,
    tmp_path: Path,
) -> None:
    if os.environ.get("SOVEREIGN_AGENT_LIVE_ASSIGNMENTS") != "1":
        pytest.skip("set SOVEREIGN_AGENT_LIVE_ASSIGNMENTS=1 (this submits a short prompt)")
    provider = PROVIDERS[name]
    if not provider.probe().available:
        pytest.skip(f"{provider.executable} is not on PATH")

    org = _fixture_repo(tmp_path / f"{name}-{mode}")
    org.actors["operator-course"].provider = name
    before_head = _git(org.root, "rev-parse", "HEAD")
    scope = (
        "Read README.md without changing tracked files, then write only the required report."
        if mode == "read-only"
        else (
            "Create lesson.txt containing exactly 'actor is not provider\\n', "
            "then write the required report."
        )
    )
    outcome = org.create_outcome("live smoke", "truthful receipt", ["report"], "principal-human")
    org.activate(outcome.id, "master-course")
    sow = org.create_sow(outcome.id, scope, Role.OPERATOR, "master-course")
    org.ready_sow(sow.id)
    assignment = org.assign(sow.id, "operator-course", "master-course")
    finished = org.run_assignment(assignment.id)

    assert finished.state == AssignmentState.COMPLETED
    assert org._sow(sow.id).state == SowState.REVIEW  # noqa: SLF001
    assert _git(org.root, "rev-parse", "HEAD") == before_head
    workspace = org.root / ".sovereign" / "runs" / assignment.workspace_id
    receipt = (workspace / "receipt.json").read_text(encoding="utf-8")
    ActorReport.model_validate_json(
        (workspace / ".sovereign-out" / "report.json").read_text(encoding="utf-8")
    )
    assert f'"provider":"{name}"' in receipt
    assert '"provider_session_ref":null' not in receipt
    assert '"status":"completed"' in receipt
    normalized = [
        json.loads(line)
        for line in (workspace / "provider-raw" / "events.jsonl").read_text().splitlines()
    ]
    assert normalized[-1]["terminal"] is True
    if mode == "read-only":
        assert _git(org.root, "status", "--porcelain") == ""
    else:
        assert (workspace / "lesson.txt").read_text() == "actor is not provider\n"
