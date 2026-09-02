"""Public repository and distribution-boundary regression tests."""

from __future__ import annotations

import re
import subprocess
import tomllib
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
pytestmark = pytest.mark.skipif(
    not (ROOT / ".git").exists(),
    reason="repository-structure checks require a Git checkout",
)

COMMUNITY_FILES = (
    "CODE_OF_CONDUCT.md",
    "CONTRIBUTING.md",
    "LICENSE",
    "SECURITY.md",
    "SUPPORT.md",
    ".github/PULL_REQUEST_TEMPLATE.md",
    ".github/ISSUE_TEMPLATE/01-bug.yml",
    ".github/ISSUE_TEMPLATE/02-documentation.yml",
    ".github/ISSUE_TEMPLATE/03-feature.yml",
    ".github/ISSUE_TEMPLATE/config.yml",
)

CURRENT_DOCS = (
    ROOT / "README.md",
    ROOT / "CONTRIBUTING.md",
    ROOT / "SECURITY.md",
    ROOT / "SUPPORT.md",
    ROOT / "docs" / "index.md",
    ROOT / "docs" / "architecture.md",
    ROOT / "docs" / "API.md",
    ROOT / "docs" / "api_reference.md",
    ROOT / "docs" / "compatibility.md",
    ROOT / "docs" / "quickstart.md",
    ROOT / "docs" / "threat-model.md",
)


def tracked_paths() -> set[str]:
    result = subprocess.run(
        ["git", "ls-files", "-z"],
        cwd=ROOT,
        check=True,
        capture_output=True,
    )
    return {path.decode() for path in result.stdout.split(b"\0") if path}


def test_obsolete_manifest_is_not_public_source() -> None:
    tracked = tracked_paths()
    assert "MANIFEST-CRITICAL.txt" not in tracked


def test_github_community_health_surface_is_complete() -> None:
    for relative in COMMUNITY_FILES:
        path = ROOT / relative
        assert path.is_file(), f"missing public community-health file: {relative}"
        assert path.stat().st_size > 0, f"empty public community-health file: {relative}"


def test_license_is_the_complete_apache_2_text() -> None:
    text = (ROOT / "LICENSE").read_text(encoding="utf-8")
    assert "TERMS AND CONDITIONS FOR USE, REPRODUCTION, AND DISTRIBUTION" in text
    assert "1. Definitions." in text
    assert "9. Accepting Warranty or Additional Liability." in text
    assert "END OF TERMS AND CONDITIONS" in text


def test_package_metadata_uses_canonical_public_urls_and_declares_typing() -> None:
    metadata = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    project = metadata["project"]
    urls = project["urls"]
    assert urls["Repository"] == "https://github.com/profrodai/sovereign-agent"
    assert urls["Issues"] == "https://github.com/profrodai/sovereign-agent/issues"
    assert {"Documentation", "Changelog"} <= urls.keys()
    assert "Typing :: Typed" in project["classifiers"]
    assert (ROOT / "src" / "sovereign_agent" / "py.typed").is_file()
    assert metadata["tool"]["setuptools"]["package-data"]["sovereign_agent"] == ["py.typed"]


def test_current_markdown_links_resolve_inside_the_repository() -> None:
    link = re.compile(r"(?<!!)\[[^]]+\]\(([^)]+)\)")
    problems: list[str] = []
    for document in CURRENT_DOCS:
        text = document.read_text(encoding="utf-8")
        for target in link.findall(text):
            if target.startswith(("http://", "https://", "mailto:")):
                continue
            relative = target.split("#", 1)[0]
            if not relative:
                continue
            resolved = (document.parent / relative).resolve()
            try:
                resolved.relative_to(ROOT)
            except ValueError:
                problems.append(f"{document.relative_to(ROOT)}: link escapes repository: {target}")
                continue
            if not resolved.exists():
                problems.append(f"{document.relative_to(ROOT)}: missing link target: {target}")
    assert not problems, "\n".join(problems)
