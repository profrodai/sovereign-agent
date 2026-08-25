"""Sortable, timestamp-prefixed identifiers from the standard library."""

from __future__ import annotations

import secrets
from datetime import UTC, datetime


def new_id(prefix: str) -> str:
    """Return ``prefix_YYYYMMDDTHHMMSSZ_xxxxxxxx``."""
    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    return f"{prefix}_{stamp}_{secrets.token_hex(4)}"


def utc_now() -> datetime:
    """Return an aware UTC timestamp."""
    return datetime.now(UTC)
