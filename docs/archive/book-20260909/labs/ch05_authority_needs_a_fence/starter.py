"""Starter for Chapter 5's durable mailbox and fencing lab."""

from __future__ import annotations

import sqlite3
from pathlib import Path

STUDENT_TODO = True
LEASE_TICKS = 10


def mint_token(connection: sqlite3.Connection) -> int:
    """Mint the next durable, monotonically increasing authority token."""
    # TODO(1): Insert into a sequence table and return its integer primary key.
    raise NotImplementedError


def claim(connection: sqlite3.Connection, actor: str, now: int) -> tuple[bool, int | None]:
    """Claim NEW or expired work with one compare-and-set transition."""
    # TODO(2): Preserve an unexpired same-owner token, otherwise mint inside a
    # transaction and UPDATE only NEW or expired rows. Roll back a lost claim.
    raise NotImplementedError


def complete(connection: sqlite3.Connection, actor: str, token: int) -> bool:
    """Complete only while actor and fencing token still match durable state."""
    # TODO(3): Put state, owner, and token in the UPDATE predicate; rowcount is
    # the authority verdict.
    raise NotImplementedError


def exercise(root: Path) -> dict[str, object]:
    """Reproduce the race, then repair it with CAS and fencing."""
    # TODO(4): Create the SQLite schema, force the naive double-read race, then
    # report CAS winners, retry/takeover tokens, and both completion attempts.
    raise NotImplementedError("Implement the Chapter 5 mailbox experiment")
