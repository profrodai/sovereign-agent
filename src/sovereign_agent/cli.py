"""The stdlib-only command-line entry point."""

from __future__ import annotations

import argparse
import importlib.metadata
import platform
import sys
from collections.abc import Sequence

from sovereign_agent import __version__


def _installed_version(distribution: str) -> str:
    try:
        return importlib.metadata.version(distribution)
    except importlib.metadata.PackageNotFoundError:
        return "not installed"


def _doctor(_: argparse.Namespace) -> int:
    """Explain whether this interpreter can run the educational package."""
    python_ok = sys.version_info >= (3, 14)
    pydantic_version = _installed_version("pydantic")
    pydantic_ok = pydantic_version != "not installed"

    print("Sovereign Agent doctor")
    print(f"  Python:   {platform.python_version()} {'OK' if python_ok else 'NEEDS 3.14+'}")
    print(f"  Pydantic: {pydantic_version} {'OK' if pydantic_ok else 'MISSING'}")
    print("  Network:  not required")
    print("  Tokens:   not required")

    if python_ok and pydantic_ok:
        print("Ready for the offline curriculum.")
        return 0

    if not python_ok:
        print("Next: install Python 3.14, then rerun `sovereign-agent doctor`.")
    elif not pydantic_ok:
        print("Next: reinstall sovereign-agent so its sole runtime dependency is present.")
    return 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="sovereign-agent",
        description="Learn how outcomes become governed, evidence-backed work.",
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    subparsers = parser.add_subparsers(dest="command", required=True)

    doctor = subparsers.add_parser("doctor", help="check the offline learning environment")
    doctor.set_defaults(handler=_doctor)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Run the command-line interface."""
    namespace = build_parser().parse_args(argv)
    return int(namespace.handler(namespace))


if __name__ == "__main__":
    raise SystemExit(main())
