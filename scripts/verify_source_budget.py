"""Enforce the educational package's module, line, and export budgets."""

from __future__ import annotations

import ast
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PACKAGE = ROOT / "src" / "sovereign_agent"
MAX_MODULES = 40
# Raised from 6_000 to 6_250 by Principal ruling on PR #35 (F-U9-1): Unit 9's
# canonical-creation transaction had to compose create_sow/ready_sow/assign's
# own writes into one atomic db.immediate() block rather than five separate
# commits -- the fix a stranded, unrecoverable wake decision required -- and
# the honest cost of that composition (connection-taking _on helpers plus the
# revalidation this same defect's fix also required) did not fit the prior
# ceiling without cramping the code to force it. Module and export ceilings
# are unchanged. See docs/v1-unit9-pulse-proactive-work.md's own budget
# table for the before/after figures this ruling produced.
#
# Raised from 6_250 to 6_400 for the first-class OpenAI-compatible (ollama)
# provider (~154 nonblank lines) that closes the documented-but-inert
# SOVEREIGN_AGENT_LLM_* gap (org issue #210). A new provider cannot fit the
# prior ~40-line headroom; this bump is PROPOSED in the provider PR and stands
# only once Master/Principal sanction it on merge, exactly as the 6_000->6_250
# raise was ruled.
#
# Raised from 6_400 to 6_600 for the Operator-directed heartbeat mechanism
# (~152 nonblank lines: heartbeat.py, migration 17, CLI wiring) -- durable
# liveness records deliberately separate from the events ledger. The feature
# could not fit the prior 28-line headroom; this bump is PROPOSED in the
# heartbeat PR and stands only once sanctioned on merge, per the same
# precedent as both prior raises.
#
# Raised from 6_600 to 7_250 for the Operator-directed advanced mechanisms:
# six deliberately separate teaching contracts (isolation, automation,
# recoverable context, session coordination, tool discovery, and memory).
# The measured implementation is 668 nonblank package lines total -- about
# 111 per mechanism -- and introduces no runtime dependency. Keeping separate
# modules is part of the pedagogy: discovery must not look like authorization,
# and a schedule must not hide inside Pulse or heartbeat. The new ceiling
# leaves only 53 lines of headroom at first filing, so it records the real cost
# without turning the budget into permission for unrelated growth.
MAX_NONBLANK_LINES = 7_250
MAX_ROOT_EXPORTS = 30


def root_exports() -> list[str]:
    tree = ast.parse((PACKAGE / "__init__.py").read_text(encoding="utf-8"))
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(
            isinstance(target, ast.Name) and target.id == "__all__" for target in node.targets
        ):
            value = ast.literal_eval(node.value)
            if isinstance(value, list) and all(isinstance(item, str) for item in value):
                return value
    raise ValueError("sovereign_agent.__all__ must be a literal list of strings")


def main() -> int:
    modules = sorted(PACKAGE.rglob("*.py"))
    nonblank_lines = sum(
        1
        for path in modules
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    )
    exports = root_exports()
    failures: list[str] = []
    if len(modules) > MAX_MODULES:
        failures.append(f"{len(modules)} modules exceeds {MAX_MODULES}")
    if nonblank_lines > MAX_NONBLANK_LINES:
        failures.append(f"{nonblank_lines} nonblank lines exceeds {MAX_NONBLANK_LINES}")
    if len(exports) > MAX_ROOT_EXPORTS:
        failures.append(f"{len(exports)} root exports exceeds {MAX_ROOT_EXPORTS}")

    print(
        f"modules={len(modules)}/{MAX_MODULES} "
        f"nonblank_lines={nonblank_lines}/{MAX_NONBLANK_LINES} "
        f"root_exports={len(exports)}/{MAX_ROOT_EXPORTS}"
    )
    if failures:
        for failure in failures:
            print(f"FAIL: {failure}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
