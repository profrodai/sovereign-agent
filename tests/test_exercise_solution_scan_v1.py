"""Static answer-import checks inspect Python syntax and preserve ordinary prose."""

from __future__ import annotations

import json
import runpy
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
check = runpy.run_path(str(ROOT / "scripts/verify_exercise_release_v5.py"))["check_student_code"]


@pytest.mark.parametrize(
    "source",
    [
        "from solutions import answer",
        "import course.solutions.answer",
        "runpy.run_path('chapter/solutions/answer.py')",
        "exec(Path('chapter/solutions/answer.py').read_text())",
        "importlib.import_module('chapter.solutions.answer')",
    ],
)
def test_literal_solution_loading_refuses(source: str) -> None:
    with pytest.raises(AssertionError, match="solution import"):
        check(source)


def test_prose_and_comments_are_not_imports() -> None:
    check('# execution and solutions\nprint("Compare execution with instructor solutions")')


def test_all_real_student_cells_are_accepted() -> None:
    release = json.loads((ROOT / "book/always_on/exercises/release-v3.json").read_text())
    paths = {row["notebook"] for row in release["units"]}
    paths.update(
        path.relative_to(ROOT).as_posix()
        for path in (ROOT / "book/always_on/exercises").glob("ch*/unit-*-v1.ipynb")
    )
    assert len(paths) == 32
    for path in paths:
        for cell in json.loads((ROOT / path).read_text())["cells"]:
            if cell["cell_type"] == "code":
                source = cell.get("source", "")
                check("".join(source) if isinstance(source, list) else source)
