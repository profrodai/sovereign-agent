"""Fail unless Pydantic is the sole direct runtime dependency."""

from __future__ import annotations

import sys
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def dependency_name(requirement: str) -> str:
    """Return a normalized distribution name from a simple requirement."""
    token = requirement.split(";", 1)[0].strip()
    for marker in ("[", "<", ">", "=", "!", "~", " "):
        token = token.split(marker, 1)[0]
    return token.lower().replace("_", "-")


def main() -> int:
    metadata = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    requirements = metadata["project"].get("dependencies", [])
    names = [dependency_name(requirement) for requirement in requirements]

    if names != ["pydantic"]:
        print(f"FAIL: expected exactly pydantic; found {names or 'no dependencies'}")
        return 1

    print("pydantic")
    return 0


if __name__ == "__main__":
    sys.exit(main())
