from __future__ import annotations

from pathlib import Path

from sovereign_agent.cli import main


def test_demo_store_simulated(tmp_path: Path, capsys) -> None:
    assert main(["demo", "store", "--mode", "simulated", "--root", str(tmp_path)]) == 0
    output = capsys.readouterr().out
    assert "outcome ACCEPTED" in output
