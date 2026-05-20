"""v0.3 lint-cleanup — make M1 + M2 patches pass project ruff.

The patches in M1 and M2 were anchored against the v0.2 source and produced
working code, but didn't account for the project's ruff rules:

  - I001 (import sorting) — new imports landed in non-alphabetical order
  - UP017 (datetime.UTC alias) — pre-3.11 style timezone.utc usage in
    M1's tests (this codebase is py312+)
  - UP037 (quoted annotations) — `from __future__ import annotations`
    makes these unnecessary
  - F401 (unused re-exports) — channels names in package __init__.py
    aren't recognized as re-exports

This script applies the minimal fixes. Each patch is anchored and
idempotent. Run after M1 + M2 have already landed.
"""

from __future__ import annotations

import os
import re
import sys
from dataclasses import dataclass
from pathlib import Path

SRC = Path(os.environ.get("SA_PKG_ROOT") or "sovereign_agent")
TESTS = Path("tests")


@dataclass
class Patch:
    path: Path
    label: str
    marker: str   # if present in file, patch is already applied -> skip
    anchor: str   # unique substring to replace
    replacement: str


# ---------------------------------------------------------------------------
# 1. orchestrator/main.py — strip quoted annotations (UP037), fix import order
# ---------------------------------------------------------------------------
ORCH_MAIN = [
    Patch(
        path=SRC / "orchestrator" / "main.py",
        label="orchestrator/main.py: unquote `list[ChannelAdapter] | None`",
        marker="adapters: list[ChannelAdapter] | None = None",
        anchor='        adapters: "list[ChannelAdapter] | None" = None,\n',
        replacement="        adapters: list[ChannelAdapter] | None = None,\n",
    ),
    Patch(
        path=SRC / "orchestrator" / "main.py",
        label="orchestrator/main.py: unquote add_adapter's ChannelAdapter annotation",
        marker="async def add_adapter(self, adapter: ChannelAdapter) -> None:",
        anchor='    async def add_adapter(self, adapter: "ChannelAdapter") -> None:\n',
        replacement="    async def add_adapter(self, adapter: ChannelAdapter) -> None:\n",
    ),
    Patch(
        path=SRC / "orchestrator" / "main.py",
        label="orchestrator/main.py: reorder AutoApprover import (alphabetical)",
        # marker doubles as the desired end state — once we see this pair
        # already adjacent in the right order, we skip.
        marker=(
            "from sovereign_agent.orchestrator.auto_approver import AutoApprover\n"
            "from sovereign_agent.orchestrator.credentials import CredentialGateway\n"
        ),
        anchor=(
            "from sovereign_agent.orchestrator.credentials import CredentialGateway\n"
            "from sovereign_agent.orchestrator.auto_approver import AutoApprover\n"
        ),
        replacement=(
            "from sovereign_agent.orchestrator.auto_approver import AutoApprover\n"
            "from sovereign_agent.orchestrator.credentials import CredentialGateway\n"
        ),
    ),
    Patch(
        path=SRC / "orchestrator" / "main.py",
        label="orchestrator/main.py: reorder TYPE_CHECKING imports (alphabetical)",
        marker=(
            "    from sovereign_agent.channels.adapter import ChannelAdapter\n"
            "    from sovereign_agent.orchestrator.worker import WorkerOutcome\n"
        ),
        anchor=(
            "    from sovereign_agent.orchestrator.worker import WorkerOutcome\n"
            "    from sovereign_agent.channels.adapter import ChannelAdapter\n"
        ),
        replacement=(
            "    from sovereign_agent.channels.adapter import ChannelAdapter\n"
            "    from sovereign_agent.orchestrator.worker import WorkerOutcome\n"
        ),
    ),
]


# ---------------------------------------------------------------------------
# 2. M1 channel test files — modernize datetime usage (UP017)
# ---------------------------------------------------------------------------
# These files reference `timezone.utc` in multiple call sites. We:
#   - rewrite the import line to use `UTC` (and drop the now-unused `timezone`)
#   - rewrite every `timezone.utc` call site to `UTC`
# The substitution is idempotent: once `UTC` is the import and `timezone.utc`
# no longer appears in the file, the patcher exits cleanly with "skipped".


M1_TEST_FILES = [
    TESTS / "test_channels_protocol.py",
    TESTS / "test_channels_router.py",
    TESTS / "test_channels_integration.py",
    TESTS / "test_channels_cli.py",
]


def _modernize_datetime_usage(path: Path) -> str:
    """Rewrite a test file from `timezone.utc` to `UTC` in both the import
    and every call site. Returns 'applied' | 'skipped' | 'absent'."""
    if not path.exists():
        return "absent"
    text = path.read_text(encoding="utf-8")

    needs_import_fix = "from datetime import datetime, timezone" in text
    has_callsite = "timezone.utc" in text

    # Already modern? — no timezone.utc anywhere AND no broken import.
    if not needs_import_fix and not has_callsite:
        return "skipped"

    new_text = text

    # 1. Fix the import line, if present in this exact shape.
    if needs_import_fix:
        new_text = new_text.replace(
            "from datetime import datetime, timezone",
            "from datetime import UTC, datetime",
            1,
        )

    # 2. Replace all call sites.
    if "timezone.utc" in new_text:
        new_text = new_text.replace("timezone.utc", "UTC")

    if new_text == text:
        return "skipped"
    path.write_text(new_text, encoding="utf-8")
    return "applied"


# ---------------------------------------------------------------------------
# 3. Package __init__.py — make channels re-exports survive F401
# ---------------------------------------------------------------------------
# ruff recognizes `from X import Y as Y` as an intentional re-export and
# stops flagging F401. This is cleaner than scrubbing __all__ (which we
# can't safely string-replace because every project formats it differently;
# see Module 1 carry-forward #10) and cleaner than per-line noqa.


def _patch_package_init() -> str:
    path = SRC / "__init__.py"
    if not path.exists():
        raise SystemExit(f"FATAL: target file missing: {path}")
    text = path.read_text(encoding="utf-8")

    # If already in the redundant-alias form, skip.
    if "ChannelAdapter as ChannelAdapter" in text:
        return "skipped"

    # We rewrite the block written by M1. It's deterministic shape:
    # "from sovereign_agent.channels import (\n    Name,\n    ...,\n)\n"
    pattern = re.compile(
        r"from sovereign_agent\.channels import \(\s*"
        r"((?:\s*[A-Za-z_][A-Za-z0-9_]*,?\s*)+)"
        r"\)\s*\n"
    )
    m = pattern.search(text)
    if m is None:
        raise SystemExit(
            f"FATAL: could not find the channels import block in {path}. "
            "Did Module 1 run successfully?"
        )

    # Parse the captured names.
    names = [n.strip() for n in m.group(1).replace("\n", "").split(",") if n.strip()]
    if not names:
        raise SystemExit(f"FATAL: channels import block in {path} is empty.")

    rebuilt = "".join(
        f"from sovereign_agent.channels import {n} as {n}\n" for n in names
    )
    path.write_text(text[: m.start()] + rebuilt + text[m.end() :], encoding="utf-8")
    return "applied"


# ---------------------------------------------------------------------------
# Driver
# ---------------------------------------------------------------------------
ALL_PATCHES = ORCH_MAIN


def apply(patch: Patch) -> str:
    if not patch.path.exists():
        # Some users may not have the M1 tests (they're not strictly required
        # to run M1). Treat as already-fine rather than fatal.
        return "absent"
    text = patch.path.read_text(encoding="utf-8")
    if patch.marker in text:
        return "skipped"
    if patch.anchor not in text:
        # Anchor missing AND marker missing. Two interpretations:
        #   (a) The file's already in the desired post-state by some other
        #       route (ruff auto-fix, a hand edit). The patch's job is done.
        #   (b) The file has truly drifted off the expected shape.
        # We can't reliably tell from here, so we report "skipped" and trust
        # the post-install ruff check to catch a real (b). False positives
        # for (a) — like ruff already reordering imports — are common and
        # shouldn't FATAL the run.
        return "skipped"
    if text.count(patch.anchor) != 1:
        raise SystemExit(
            f"FATAL: anchor for {patch.label!r} is not unique "
            f"({text.count(patch.anchor)} matches) in {patch.path}."
        )
    patch.path.write_text(text.replace(patch.anchor, patch.replacement, 1), encoding="utf-8")
    return "applied"


def main() -> int:
    if not SRC.exists():
        raise SystemExit(f"FATAL: package directory not found: {SRC}")
    applied = skipped = absent = 0
    print(f"Applying v0.3 lint-cleanup patches under {SRC} (idempotent):\n")
    for patch in ALL_PATCHES:
        outcome = apply(patch)
        marker = {"applied": "+", "skipped": "=", "absent": "·"}[outcome]
        print(f"  {marker} {patch.label}  [{outcome}]")
        applied += outcome == "applied"
        skipped += outcome == "skipped"
        absent += outcome == "absent"

    # M1 channel tests — bespoke because we rewrite both the import and
    # every call site, not a single anchored substring.
    for path in M1_TEST_FILES:
        outcome = _modernize_datetime_usage(path)
        marker = {"applied": "+", "skipped": "=", "absent": "·"}[outcome]
        label = f"{path}: timezone.utc → UTC (import + call sites)"
        print(f"  {marker} {label}  [{outcome}]")
        applied += outcome == "applied"
        skipped += outcome == "skipped"
        absent += outcome == "absent"

    # Package __init__.py — bespoke because it edits an arbitrary block shape.
    init_outcome = _patch_package_init()
    marker = "+" if init_outcome == "applied" else "="
    print(f"  {marker} sovereign_agent/__init__.py: re-export channels names (X as X)  [{init_outcome}]")
    if init_outcome == "applied":
        applied += 1
    else:
        skipped += 1

    print(
        f"\n  {applied} applied, {skipped} already present, {absent} absent (target file missing)."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
