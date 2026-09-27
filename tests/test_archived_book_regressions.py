"""Retain all historical book regressions after moving their source archive."""

import pytest

from scripts.book_archive_support_v1 import (
    HISTORICAL_RUNTIME,
    historical_runtime_available,
    run,
)


@pytest.mark.skipif(
    not historical_runtime_available(),
    reason=f"the archive runs on runtime {HISTORICAL_RUNTIME[:7]}, which needs the Git history "
    "(this is a clone without it); `make verify` in a full checkout runs it",
)
def test_all_historical_book_contracts_execute():
    run("tests")
