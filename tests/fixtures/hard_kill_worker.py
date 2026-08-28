"""A real worker process, for the hard-kill recovery proof.

Run as `python hard_kill_worker.py <root> <assignment_id>`. Opens its own
`Organization` (its own SQLite connection, its own process identity -- a
real, separate process, not a mock), points the Scripted provider at a
script that sleeps well past this test's patience, and calls
`run_assignment`. The parent test process SIGKILLs *this* process while it
is blocked inside `subprocess.run` waiting on the sleeping provider -- a
real process boundary, not a `Refusal` injected in place of a real crash.
Nothing here ever completes normally: reaching the sleep and then dying is
the entire point.
"""

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from sovereign_agent.organization import Organization  # noqa: E402
from sovereign_agent.providers.base import InvocationSpec  # noqa: E402
from sovereign_agent.providers.scripted import ScriptedProvider  # noqa: E402


def main() -> None:
    root = Path(sys.argv[1])
    assignment_id = sys.argv[2]

    def build(self: ScriptedProvider, request: object) -> InvocationSpec:  # noqa: ANN001
        return InvocationSpec(
            argv=[sys.executable, "-c", "import time; time.sleep(120)"],
            cwd=Path(root),
        )

    with patch.object(ScriptedProvider, "build_invocation", build):
        org = Organization(root)
        # This call blocks inside subprocess.run for up to 120s (or until
        # this whole process is killed, whichever comes first -- the parent
        # test always kills it first). If it somehow returned, that would be
        # a test-infrastructure bug, not a real outcome to report.
        org.run_assignment(assignment_id)


if __name__ == "__main__":
    main()
