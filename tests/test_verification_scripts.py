from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def run_script(name: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(ROOT / "scripts" / name)],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )


def test_runtime_dependency_gate() -> None:
    result = run_script("verify_runtime_dependencies.py")
    assert result.stdout.strip() == "pydantic"


def test_source_budget_gate() -> None:
    result = run_script("verify_source_budget.py")
    assert "modules=" in result.stdout
    assert "root_exports=" in result.stdout
