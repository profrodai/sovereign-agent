"""Regression coverage for the proof-pack manifest verifier's lie-detector.

Sparring and Master independently found that `verify_proof_pack.py`'s
"NOT_RUN means PASS" check (governing ruling Holding 2) only ever fired
inside `provider_status` rows: an explicit `not_run_context: bool` parameter
was set True only by `check_provider_status`, so
`andrea_live_evaluation: {"status": "NOT_RUN", "note": "live evaluation
passed anyway"}` passed with zero failures -- the exact lie Holding 2 names,
just uncaught for that one field.

The fix makes `walk_and_validate_strings` derive lie-scan context
structurally, from each object's OWN recognized `status` field, rather than
from a caller-injected flag -- so any current or future status-bearing
object gets the same coverage for free. These tests pin that behavior
directly (so a future refactor cannot silently narrow it back to a single
field) and re-confirm the mutations the original implementation was already
correct on still are.
"""

from __future__ import annotations

import copy
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
VERIFY_PROOF_PACK = REPO_ROOT / "scripts" / "verify_proof_pack.py"
BASE_MANIFEST_PATH = REPO_ROOT / "docs" / "evidence" / "unit12" / "proof-pack.json"


def base_manifest() -> dict[str, Any]:
    return json.loads(BASE_MANIFEST_PATH.read_text(encoding="utf-8"))


def run_verifier(manifest: dict[str, Any], tmp_path: Path) -> subprocess.CompletedProcess[str]:
    manifest_path = tmp_path / "proof-pack.json"
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    return subprocess.run(  # noqa: S603 - fixed argv, no shell
        [sys.executable, str(VERIFY_PROOF_PACK), str(manifest_path)],
        capture_output=True,
        text=True,
        cwd=REPO_ROOT,
    )


def test_the_real_committed_manifest_passes(tmp_path: Path) -> None:
    result = run_verifier(base_manifest(), tmp_path)
    assert result.returncode == 0, result.stdout + result.stderr


def test_andrea_not_run_with_success_prose_is_rejected(tmp_path: Path) -> None:
    """The exact gap: NOT_RUN outside provider_status previously passed."""
    manifest = base_manifest()
    manifest["andrea_live_evaluation"] = {
        "status": "NOT_RUN",
        "note": "live evaluation passed anyway",
    }
    result = run_verifier(manifest, tmp_path)
    assert result.returncode == 1
    assert "andrea_live_evaluation.note" in result.stdout
    assert "NOT_RUN does not mean PASS" in result.stdout


def test_andrea_unknown_status_is_rejected(tmp_path: Path) -> None:
    manifest = base_manifest()
    manifest["andrea_live_evaluation"] = {"status": "BANANA", "note": "whatever"}
    result = run_verifier(manifest, tmp_path)
    assert result.returncode == 1
    assert "andrea_live_evaluation.status: unknown value 'BANANA'" in result.stdout


def test_provider_not_run_with_success_prose_still_rejected(tmp_path: Path) -> None:
    """Must not regress: this case already worked before the fix."""
    manifest = base_manifest()
    manifest["provider_status"]["claude"]["reason"] += " Actually the live evaluation passed."
    result = run_verifier(manifest, tmp_path)
    assert result.returncode == 1
    assert "provider_status.claude.reason" in result.stdout
    assert "NOT_RUN does not mean PASS" in result.stdout


def test_real_hex_commit_and_digest_values_pass(tmp_path: Path) -> None:
    """The verifier must not reject a real, long hex value as secret-shaped
    content -- the exact regression this SOW's own verifier contract broke
    on twice before."""
    manifest = base_manifest()
    manifest["source_commit"] = "a" * 40
    manifest["release_candidate_commit"] = "b" * 40
    manifest["artifact_digests"]["wheel_sha256"] = "c" * 64
    result = run_verifier(manifest, tmp_path)
    assert result.returncode == 0, result.stdout + result.stderr


def test_andrea_not_run_with_truthful_pre_check_only_prose_passes(tmp_path: Path) -> None:
    """A real nuance: truthfully saying only the pre-check passed, while the
    human live evaluation itself has not run, is NOT the lie Holding 2 names
    and must not be rejected."""
    manifest = base_manifest()
    manifest["andrea_live_evaluation"] = {
        "status": "NOT_RUN",
        "reason": (
            "The machine-checkable pre-check passed; the human live evaluation itself has not run."
        ),
        "pre_check_passed": True,
    }
    result = run_verifier(manifest, tmp_path)
    assert result.returncode == 0, result.stdout + result.stderr


def test_andrea_pass_with_evidence_consistent_prose_passes(tmp_path: Path) -> None:
    """Once the Andrea evaluation has genuinely run and passed, the verifier
    must allow it -- the fix must not treat PASS itself as suspicious."""
    manifest = base_manifest()
    manifest["andrea_live_evaluation"] = {
        "status": "PASS",
        "reason": (
            "The Andrea live evaluation session ran against "
            "docs/andrea-chapters-0-12-evaluation.md and the human evaluator "
            "passed every chapter checkpoint."
        ),
        "pre_check_passed": True,
    }
    result = run_verifier(manifest, tmp_path)
    assert result.returncode == 0, result.stdout + result.stderr


def test_credential_assignment_leak_still_rejected(tmp_path: Path) -> None:
    manifest = base_manifest()
    manifest["redactions_performed"] = [
        "ANTHROPIC_API_KEY=sk-ant-oat01-realvalue-not-a-placeholder"
    ]
    result = run_verifier(manifest, tmp_path)
    assert result.returncode == 1
    assert "unredacted credential assignment" in result.stdout


def test_bearer_token_leak_still_rejected(tmp_path: Path) -> None:
    manifest = base_manifest()
    manifest["non_claims"] = [
        *manifest["non_claims"],
        "Authorization used: Bearer abcdEFGH12345678",
    ]
    result = run_verifier(manifest, tmp_path)
    assert result.returncode == 1
    assert "literal Bearer-token shape" in result.stdout


def test_digest_mismatch_still_rejected(tmp_path: Path) -> None:
    manifest = base_manifest()
    manifest["evidence_files"][0]["sha256"] = "0" * 64
    result = run_verifier(manifest, tmp_path)
    assert result.returncode == 1
    assert "does not match the file's actual digest" in result.stdout


def test_path_escape_still_rejected(tmp_path: Path) -> None:
    manifest = base_manifest()
    manifest["evidence_files"][0]["path"] = "../../etc/passwd"
    result = run_verifier(manifest, tmp_path)
    assert result.returncode == 1
    assert "escapes docs/evidence/unit12/" in result.stdout


def test_missing_required_field_still_rejected(tmp_path: Path) -> None:
    manifest = base_manifest()
    del manifest["non_claims"]
    result = run_verifier(manifest, tmp_path)
    assert result.returncode == 1
    assert "missing required field: non_claims" in result.stdout


def test_unknown_provider_status_still_rejected(tmp_path: Path) -> None:
    manifest = base_manifest()
    manifest["provider_status"]["claude"]["status"] = "BANANA"
    result = run_verifier(manifest, tmp_path)
    assert result.returncode == 1
    assert "provider_status.claude.status: unknown value 'BANANA'" in result.stdout


def test_unbacked_live_pass_still_rejected(tmp_path: Path) -> None:
    manifest = base_manifest()
    manifest["provider_status"]["claude"]["status"] = "LIVE_PASS"
    manifest["provider_status"]["claude"]["evidence_path"] = "does_not_exist.txt"
    result = run_verifier(manifest, tmp_path)
    assert result.returncode == 1
    assert "unbacked LIVE_PASS claim" in result.stdout


@pytest.mark.parametrize(
    "status",
    ["NOT_RUN_UNAVAILABLE", "NOT_RUN_UNAUTHENTICATED"],
)
def test_provider_not_run_variants_still_reject_success_prose(status: str, tmp_path: Path) -> None:
    """Both NOT_RUN_* provider variants must still trigger the lie-scan --
    pinned separately since the fix changed HOW context is derived."""
    manifest = base_manifest()
    manifest["provider_status"]["claude"]["status"] = status
    manifest["provider_status"]["claude"]["reason"] = "live evaluation passed"
    result = run_verifier(manifest, tmp_path)
    assert result.returncode == 1
    assert "NOT_RUN does not mean PASS" in result.stdout


def test_not_run_context_propagates_to_nested_sibling_fields(tmp_path: Path) -> None:
    """Point 2 of the correction: NOT_RUN context must propagate to nested
    sibling fields of the status-bearing object, not just its own direct
    string values."""
    manifest = base_manifest()
    manifest["andrea_live_evaluation"] = {
        "status": "NOT_RUN",
        "detail": {"summary": "live evaluation passed anyway"},
    }
    result = run_verifier(manifest, tmp_path)
    assert result.returncode == 1
    assert "andrea_live_evaluation.detail.summary" in result.stdout
    assert "NOT_RUN does not mean PASS" in result.stdout


def test_andrea_not_run_prefixed_variant_also_triggers_lie_scan(tmp_path: Path) -> None:
    """The correction names NOT_RUN and NOT_RUN_* alike as context roots,
    even though ANDREA_STATUSES today only contains the bare NOT_RUN value --
    this exercises walk_and_validate_strings's prefix rule directly via a
    provider row (which does have NOT_RUN_* values) to confirm the shared
    prefix logic used for both domains is genuinely shared, not duplicated
    per-domain in a way that could silently diverge."""
    manifest = base_manifest()
    manifest["provider_status"]["codex"]["status"] = "NOT_RUN_UNAVAILABLE"
    manifest["provider_status"]["codex"]["reason"] = "verified live nonetheless"
    result = run_verifier(manifest, tmp_path)
    assert result.returncode == 1
    assert "provider_status.codex.reason" in result.stdout


def test_verify_function_import_matches_cli_behavior(tmp_path: Path) -> None:
    """Sanity check that the in-process verify() the SOW's own matrix was
    also exercised against agrees with the CLI subprocess path, so the two
    never silently diverge."""
    sys.path.insert(0, str(REPO_ROOT / "scripts"))
    from verify_proof_pack import verify  # noqa: PLC0415

    manifest = base_manifest()
    manifest["andrea_live_evaluation"] = {
        "status": "NOT_RUN",
        "note": "live evaluation passed anyway",
    }
    in_process_failures = verify(copy.deepcopy(manifest))
    cli_result = run_verifier(manifest, tmp_path)
    assert bool(in_process_failures) == (cli_result.returncode != 0)
