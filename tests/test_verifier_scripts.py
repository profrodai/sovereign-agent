"""The verifiers must be able to FAIL, and must not repair while verifying.

A verifier that only ever passes tells you nothing. A verifier that edits the
thing it is checking tells you something false. Both were true on PR #24.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

from reference_organizations.store.demo import run_simulated
from sovereign_agent.organization import Organization

REPO_ROOT = Path(__file__).resolve().parent.parent
VERIFY_OUTCOME = REPO_ROOT / "scripts" / "verify_store_outcome.py"
VERIFY_PROJECTIONS = REPO_ROOT / "scripts" / "verify_projections.py"


def run_script(script: Path, *arguments: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(  # noqa: S603 - fixed argv, no shell
        [sys.executable, str(script), *arguments], capture_output=True, text=True, cwd=REPO_ROOT
    )


@pytest.fixture
def store(tmp_path: Path) -> Path:
    run_simulated(tmp_path)
    return tmp_path


def test_verifier_passes_a_truthful_store(store: Path) -> None:
    result = run_script(VERIFY_OUTCOME, str(store))
    assert result.returncode == 0, result.stdout + result.stderr
    assert "ACCEPTED and true" in result.stdout


def test_verifier_fails_closed_on_an_empty_subject(store: Path) -> None:
    """`outcome.subject or SKU` silently re-pointed a subjectless outcome at tea."""
    org = Organization(store)
    org.db.connection.execute("UPDATE outcomes SET record = json_set(record, '$.subject', '')")
    org.db.connection.commit()
    org.db.close()
    result = run_script(VERIFY_OUTCOME, str(store))
    assert result.returncode == 1
    assert "declares no subject" in result.stdout


def test_verifier_requires_a_review_record(store: Path) -> None:
    org = Organization(store)
    # reviews are append-only at the database boundary; drop the guard for this
    # one statement to test the VERIFIER, not the trigger.
    for guard in ("update", "delete", "replace"):
        org.db.connection.execute(f"DROP TRIGGER IF EXISTS reviews_no_{guard}")
    org.db.connection.execute("DELETE FROM reviews")
    org.db.connection.commit()
    org.db.close()
    result = run_script(VERIFY_OUTCOME, str(store))
    assert result.returncode == 1
    assert "has no review of its current verification" in result.stdout


def test_verifier_requires_the_receipt_digest_sidecar(store: Path) -> None:
    """Checking the sidecar only when present made deleting it a non-event."""
    for sidecar in store.rglob("receipt.json.sha256"):
        sidecar.unlink()
    result = run_script(VERIFY_OUTCOME, str(store))
    assert result.returncode == 1
    assert "receipt.json.sha256 is missing" in result.stdout


def test_verifier_detects_a_receipt_whose_column_and_record_disagree(store: Path) -> None:
    org = Organization(store)
    org.db.connection.execute("UPDATE receipts SET status = 'failed'")
    org.db.connection.commit()
    org.db.close()
    result = run_script(VERIFY_OUTCOME, str(store))
    assert result.returncode == 1
    assert "receipt column and record disagree" in result.stdout


def test_verifier_compares_every_projected_file(store: Path) -> None:
    """It previously compared only `state`, so a falsified SOW scope passed."""
    sow_path = next((store / "governance" / "outcomes").glob("*/sows/*.json"))
    record = json.loads(sow_path.read_text(encoding="utf-8"))
    record["scope"] = "HAND EDITED FALSE SCOPE"
    sow_path.write_text(json.dumps(record, indent=2), encoding="utf-8")
    result = run_script(VERIFY_OUTCOME, str(store))
    assert result.returncode == 1
    assert "does not match the ledger" in result.stdout


def test_projection_verification_is_pure(store: Path) -> None:
    """Verification must REPORT drift, never silently repair it."""
    sow_path = next((store / "governance" / "outcomes").glob("*/sows/*.json"))
    record = json.loads(sow_path.read_text(encoding="utf-8"))
    record["scope"] = "HAND EDITED FALSE SCOPE"
    tampered = json.dumps(record, indent=2)
    sow_path.write_text(tampered, encoding="utf-8")

    result = run_script(VERIFY_PROJECTIONS, str(store))
    assert result.returncode == 1
    assert "does not match the ledger" in result.stdout
    assert sow_path.read_text(encoding="utf-8") == tampered, "verification rewrote the file"


def test_reconcile_repairs_only_when_asked(store: Path) -> None:
    sow_path = next((store / "governance" / "outcomes").glob("*/sows/*.json"))
    record = json.loads(sow_path.read_text(encoding="utf-8"))
    record["scope"] = "HAND EDITED FALSE SCOPE"
    sow_path.write_text(json.dumps(record, indent=2), encoding="utf-8")

    repaired = run_script(VERIFY_PROJECTIONS, str(store), "--reconcile")
    assert repaired.returncode == 0
    assert "reconciled" in repaired.stdout
    assert run_script(VERIFY_PROJECTIONS, str(store)).returncode == 0
    assert "HAND EDITED" not in sow_path.read_text(encoding="utf-8")


def test_projection_verification_detects_an_extra_sow_file(store: Path) -> None:
    directory = next((store / "governance" / "outcomes").glob("*")) / "sows"
    (directory / "sow_GHOST.json").write_text('{"id": "sow_GHOST"}', encoding="utf-8")
    result = run_script(VERIFY_PROJECTIONS, str(store))
    assert result.returncode == 1
    assert "not in the ledger" in result.stdout
