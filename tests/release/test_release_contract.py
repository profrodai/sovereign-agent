from __future__ import annotations

import tomllib
from pathlib import Path

import sovereign_agent
from scripts.verify_release import (
    API_V02,
    API_V03,
    API_V04,
    API_V05,
    API_V06,
    EXPECTED_VERSION,
    REQUIRED_FIXTURES,
    ZEOCORE_RANGE,
    _manifest,
    _source_exports,
    verify_source,
)


def test_release_source_contract_is_coherent() -> None:
    verify_source()
    assert sovereign_agent.__version__ == EXPECTED_VERSION
    project_deps = tomllib.loads(
        (Path(__file__).parents[2] / "pyproject.toml").read_text(encoding="utf-8")
    )["project"]["dependencies"]
    assert ZEOCORE_RANGE in project_deps
    assert all((Path(__file__).parents[2] / "src" / path).is_file() for path in REQUIRED_FIXTURES)


def test_v02_api_is_preserved_in_v03_manifest() -> None:
    v02 = set(_manifest(API_V02))
    v03 = set(_manifest(API_V03))
    v04 = set(_manifest(API_V04))
    v05 = set(_manifest(API_V05))
    v06 = set(_manifest(API_V06))
    assert len(v02) == 67
    assert len(v03) == 152
    assert v02 <= v03 == v04 <= v05 == v06
    assert sorted(sovereign_agent.__all__) == _source_exports()


def test_build_artifacts_are_ignored() -> None:
    ignore = (Path(__file__).parents[2] / ".gitignore").read_text(encoding="utf-8")
    assert "dist/" in ignore
    assert "build/" in ignore
    assert "*.egg-info/" in ignore
