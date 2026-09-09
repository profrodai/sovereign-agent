"""Independent runtime cases reject the chapter defect and validate the real solution."""

from __future__ import annotations

import ast
import json
import runpy
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
EXERCISES = ROOT / "book/always_on/exercises"
TASKS = json.loads((EXERCISES / "source-tasks-v1.json").read_text())["chapters"]
SourceTask = runpy.run_path(str(EXERCISES / "source_tasks_v1.py"))["SourceTask"]


def reference(chapter: int) -> str:
    path = EXERCISES / f"ch{chapter:02d}/solutions/unit-a-solution-v1.py"
    node = next(node for node in ast.parse(path.read_text()).body if isinstance(node, ast.Assign))
    value = ast.literal_eval(node.value)
    assert isinstance(value, str)
    return value


@pytest.mark.parametrize("chapter", [row["chapter"] for row in TASKS])
def test_complete_function_connects_and_transfers(chapter: int, tmp_path: Path) -> None:
    task = SourceTask(ROOT, chapter)
    try:
        task.install(reference(chapter))
        result = task.visible()
        assert result["status"] == "PASS", result
        handoff = tmp_path / "handoff.json"
        task.save(handoff, result)
        task.load(handoff)
        result = task.transfer(EXERCISES / f"ch{chapter:02d}/holdouts/runtime-transfer-v1.py")
        assert result["status"] == "PASS", result
    finally:
        task.close()


@pytest.mark.parametrize("chapter", [row["chapter"] for row in TASKS])
def test_plausible_chapter_defect_fails_hidden_transfer(chapter: int) -> None:
    task = SourceTask(ROOT, chapter)
    try:
        task.install(reference(chapter))
        task.inject_failure()
        result = task.transfer(EXERCISES / f"ch{chapter:02d}/holdouts/runtime-transfer-v1.py")
        assert result["status"] == "FAILED", result
        assert result["returncode"] == 1 and "AssertionError" in result["stderr"], result
    finally:
        task.close()


def test_tampered_or_wrong_chapter_handoff_refuses(tmp_path: Path) -> None:
    task = SourceTask(ROOT, 4)
    try:
        task.install(reference(4))
        result = task.visible()
        path = tmp_path / "handoff.json"
        task.save(path, result)
        original = json.loads(path.read_text())
        for key, value in (("chapter", 5), ("implementation", "def preferences(): return []")):
            changed = {**original, key: value}
            path.write_text(json.dumps(changed))
            with pytest.raises(ValueError, match="handoff identity"):
                task.load(path)
        with pytest.raises(FileNotFoundError):
            task.load(tmp_path / "missing.json")
    finally:
        task.close()
