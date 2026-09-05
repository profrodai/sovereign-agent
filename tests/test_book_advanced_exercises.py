"""Behavioral smoke tests for the five chapter extensions covering six mechanisms."""

from __future__ import annotations

import json
import subprocess
import sys
from collections.abc import Callable
from pathlib import Path
from typing import Any

import pytest

ROOT = Path(__file__).resolve().parent.parent


@pytest.mark.parametrize(
    ("chapter", "assertion"),
    [
        (
            "ch01_organization_remembers",
            lambda data: data["visible_ids"] == ["public", "alice-only"],
        ),
        (
            "ch03_actor_is_not_a_model",
            lambda data: (
                data["context"]["source_rows"] == 7 and data["tools"]["authorization"] == "REFUSED"
            ),
        ),
        (
            "ch04_work_stays_inside_its_boundary",
            lambda data: (
                data["plane_verdicts"]["process"] == "UNAVAILABLE"
                and set(data["refusals"].values()) == {"REFUSED"}
            ),
        ),
        (
            "ch05_authority_needs_a_fence",
            lambda data: data["incarnations"] == [1, 2] and data["stale_finish"] == "REFUSED",
        ),
        (
            "ch07_the_organization_wakes_itself",
            lambda data: (
                data["statuses"] == ["NO_FIRE", "SUCCEEDED"]
                and data["payload_received_durable_run_id"]
            ),
        ),
    ],
)
def test_advanced_chapter_exercise_runs_from_an_empty_root(
    tmp_path: Path, chapter: str, assertion: Callable[[dict[str, Any]], bool]
) -> None:
    script = ROOT / "book" / chapter / "advanced_exercise.py"
    result = subprocess.run(
        [sys.executable, str(script), "--root", str(tmp_path / chapter)],
        check=True,
        capture_output=True,
        text=True,
    )
    data = json.loads(result.stdout)
    assert assertion(data)
