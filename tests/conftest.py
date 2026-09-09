"""Pytest fixtures shared across the suite."""

from __future__ import annotations

from pathlib import Path

import pytest

from .helpers import governed_assignment

# Old edition contracts execute together in a temporary historical topology.
# The ordinary suite still runs them through test_archived_book_regressions.py;
# they are not silently skipped or allowed to grade the active nineteen chapters.
if (Path(__file__).resolve().parents[1] / "docs/archive/book-20260909").is_dir():
    from scripts.book_archive_support_v1 import HISTORICAL_TESTS

    collect_ignore = list(HISTORICAL_TESTS)


@pytest.fixture
def governed(tmp_path: Path):
    """A seeded store with one completed, authorized assignment."""
    return governed_assignment(tmp_path)
