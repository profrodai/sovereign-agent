from __future__ import annotations

import tomllib
from pathlib import Path

import sovereign_agent


def test_no_sandcastle_in_runtime_dependencies() -> None:
    project = tomllib.loads(
        (Path(__file__).parents[2] / "pyproject.toml").read_text(encoding="utf-8")
    )
    blob = str(project).lower()
    assert "sandcastle" not in blob
    assert "sandcastle" not in Path(sovereign_agent.__file__).read_text(encoding="utf-8").lower()


def test_optional_extras_are_declared() -> None:
    extras = tomllib.loads(
        (Path(__file__).parents[2] / "pyproject.toml").read_text(encoding="utf-8")
    )["project"]["optional-dependencies"]
    assert "slack" in extras
    assert "email" in extras
    assert "docker" not in extras["all"]
