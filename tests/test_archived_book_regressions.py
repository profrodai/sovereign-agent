"""Retain all historical book regressions after moving their source archive."""

from scripts.book_archive_support_v1 import run


def test_all_historical_book_contracts_execute():
    run("tests")
