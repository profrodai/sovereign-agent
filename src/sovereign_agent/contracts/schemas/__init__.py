"""Bundled JSON Schema resources for the external wire contracts."""

from __future__ import annotations

from importlib.resources import files
from pathlib import Path

SCHEMA_NAMES = (
    "capability-manifest.schema.json",
    "execution-receipt.schema.json",
    "governed-execution-request.schema.json",
)


def schema_path(name: str) -> Path:
    """Return a filesystem path when resources are installed unpacked."""
    if name not in SCHEMA_NAMES:
        raise ValueError(f"unknown contract schema: {name}")
    resource = files(__package__).joinpath(name)
    return Path(str(resource))


def read_schema(name: str) -> bytes:
    if name not in SCHEMA_NAMES:
        raise ValueError(f"unknown contract schema: {name}")
    return files(__package__).joinpath(name).read_bytes()


__all__ = ["SCHEMA_NAMES", "read_schema", "schema_path"]
