"""Atomic JSON/TOML/Markdown writes and a tiny TOML emitter."""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
from typing import Any


def atomic_write(path: Path, data: bytes) -> None:
    """Write via a unique sibling tempfile, fsync, then ``os.replace``."""
    path.parent.mkdir(parents=True, exist_ok=True)
    handle_id, tmp_name = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
    tmp = Path(tmp_name)
    try:
        with os.fdopen(handle_id, "wb") as handle:
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(tmp, path)
    finally:
        tmp.unlink(missing_ok=True)


def write_json(path: Path, payload: dict[str, Any]) -> None:
    atomic_write(path, json.dumps(payload, indent=2, sort_keys=True, default=str).encode())


def write_text(path: Path, text: str) -> None:
    atomic_write(path, text.encode())


def dump_toml(value: Any, indent: int = 0) -> str:
    """Emit the limited TOML this package writes during ``init``."""
    if isinstance(value, dict):
        lines: list[str] = []
        tables: list[tuple[str, Any]] = []
        array_tables: list[tuple[str, list[Any]]] = []
        prefix = "  " * indent
        for key, item in value.items():
            if isinstance(item, dict):
                tables.append((key, item))
            elif isinstance(item, list) and item and isinstance(item[0], dict):
                array_tables.append((key, item))
            else:
                lines.append(f"{prefix}{key} = {_toml_atom(item)}")
        for key, item in tables:
            lines.append("")
            lines.append(f"{prefix}[{key}]")
            lines.append(dump_toml(item, indent))
        for key, items in array_tables:
            for item in items:
                lines.append("")
                lines.append(f"{prefix}[[{key}]]")
                lines.append(dump_toml(item, indent))
        return "\n".join(line for line in lines if line is not None).strip() + "\n"
    return _toml_atom(value) + "\n"


def _toml_atom(value: Any) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (int, float)):
        return str(value)
    if isinstance(value, list):
        return "[ " + ", ".join(_toml_atom(item) for item in value) + " ]"
    escaped = str(value).replace("\\", "\\\\").replace('"', '\\"')
    return f'"{escaped}"'
