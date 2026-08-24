from __future__ import annotations

from typer.testing import CliRunner

from sovereign_agent.cli import app


def test_doctor_skip_llm_needs_no_api_key(monkeypatch, tmp_path) -> None:
    """The documented offline preflight must work without credentials."""
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.delenv("NEBIUS_KEY", raising=False)

    result = CliRunner().invoke(app, ["doctor", "--skip-llm"])

    assert result.exit_code == 0, result.output
    assert "LLM API key skipped (NEBIUS_KEY)" in result.output
    assert "All checks passed." in result.output
