"""Pytest fixtures shared across the suite."""

from __future__ import annotations

from pathlib import Path

import pytest

from .helpers import governed_assignment


@pytest.fixture
def governed(tmp_path: Path):
    """A seeded store with one completed, authorized assignment."""
    return governed_assignment(tmp_path)
