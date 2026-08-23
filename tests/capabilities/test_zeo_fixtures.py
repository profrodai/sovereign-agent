from __future__ import annotations

import json
from pathlib import Path

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures" / "zeo"


def test_zeo_fixtures_are_executable_files() -> None:
    path = FIXTURES / "capability.read.json"
    payload = json.loads(path.read_text(encoding="utf-8"))
    assert payload["id"].endswith("@1.0.0")
    assert payload["projection_name"] == "read_file"
    assert "request_schema" in payload
    assert payload["effects"]["concurrency"]
    assert payload["cancellation"]["propagates"]


def test_examples_do_not_author_register_tool() -> None:
    root = Path(__file__).resolve().parents[2] / "examples"
    for path in root.rglob("*.py"):
        text = path.read_text(encoding="utf-8")
        assert "@register_tool" not in text, path
        assert "_RegisteredTool(" not in text, path
