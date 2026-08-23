"""Hashed filenames so logical IDs never become path components."""

from __future__ import annotations

import hashlib
from pathlib import Path


def digest(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def hashed_json_name(value: str) -> str:
    return f"{digest(value)}.json"


def hashed_jsonl_name(value: str) -> str:
    return f"{digest(value)}.jsonl"


def bind_hashed(parent: Path, value: str, *, suffix: str = ".json") -> Path:
    return parent / f"{digest(value)}{suffix}"
