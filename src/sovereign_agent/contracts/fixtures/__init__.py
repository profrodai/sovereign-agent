"""Bundled contract fixtures. Executable from an installed wheel."""

from __future__ import annotations

import json
from importlib.resources import files
from pathlib import Path
from typing import Any

FIXTURE_NAMES = (
    "capability-manifest.valid.json",
    "governed-execution-request.valid.json",
    "execution-receipt.valid.json",
    "compatibility-matrix.json",
)


def fixture_path(name: str) -> Path:
    if name not in FIXTURE_NAMES:
        raise ValueError(f"unknown contract fixture: {name}")
    return Path(str(files(__package__).joinpath(name)))


def read_fixture(name: str) -> bytes:
    if name not in FIXTURE_NAMES:
        raise ValueError(f"unknown contract fixture: {name}")
    return files(__package__).joinpath(name).read_bytes()


def load_fixture(name: str) -> Any:
    return json.loads(read_fixture(name).decode("utf-8"))


__all__ = ["FIXTURE_NAMES", "fixture_path", "load_fixture", "read_fixture"]
