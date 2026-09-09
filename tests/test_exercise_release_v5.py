"""The source-bound release gate rejects incomplete and contradictory receipts."""

from __future__ import annotations

import json
import runpy
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
EXERCISES = ROOT / "book/always_on/exercises"
verify = runpy.run_path(str(ROOT / "scripts/verify_exercise_release_v5.py"))["verify"]
pytestmark = pytest.mark.skipif(
    not (ROOT / ".git").exists(),
    reason="Git object verification needs repository history; onboarding archive lacks it",
)


def test_complete_release_matches_actual_git_objects() -> None:
    verify()


@pytest.mark.parametrize(
    ("corruption", "message"),
    [
        ("runtime_omitted", "runtime inventory drift"),
        ("holdout_omitted", "hidden case inventory drift"),
        ("duplicated_unit", "unit set drift"),
        ("unknown_field", "unknown or missing release field"),
        ("boolean_counter", "invalid execution counter type"),
        ("changed_byte_hash", "working file drift"),
    ],
)
def test_corrupted_receipt_refuses(corruption: str, message: str, tmp_path: Path) -> None:
    release = json.loads((EXERCISES / "release-v5.json").read_text())
    if corruption == "runtime_omitted":
        release["runtimeFiles"].pop()
    elif corruption == "holdout_omitted":
        release["instructorFiles"] = [
            row for row in release["instructorFiles"] if "runtime-transfer" not in row["path"]
        ]
    elif corruption == "duplicated_unit":
        release["units"][-1] = release["units"][0]
    elif corruption == "unknown_field":
        release["accepted_by_assertion"] = True
    elif corruption == "boolean_counter":
        release["units"][0]["execution"]["failed"] = False
    elif corruption == "changed_byte_hash":
        release["studentFiles"][0]["sha256"] = "0" * 64
    path = tmp_path / "corrupted.json"
    path.write_text(json.dumps(release))
    with pytest.raises(AssertionError, match=message):
        verify(path)
