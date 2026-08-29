"""Chapter 6: the organization recovers, the dead worker never does.

Runs a REAL child process, SIGKILLs it while it is genuinely blocked inside
a subprocess call (the exact fixture and polling pattern
`tests/test_supervisor.py`'s own hard-kill proof matrix uses -- not a
`Refusal` injected in place of a crash, since a Python exception handler
never runs at all for SIGKILL), then proves the supervisor -- never the
dead process itself -- recovers the assignment it left behind. Imports the
production package throughout.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from datetime import timedelta
from pathlib import Path
from typing import Any

from sovereign_agent import fencing
from sovereign_agent import supervisor as supervisor_module
from sovereign_agent.ids import utc_now
from sovereign_agent.models import AssignmentState, Role
from sovereign_agent.organization import Organization

FIXTURE = Path(__file__).resolve().parents[2] / "tests" / "fixtures" / "hard_kill_worker.py"


def _far_future_clock() -> Any:
    """A clock fixed well past any TTL this module uses -- the same
    deterministic pattern `tests/test_supervisor.py` uses so recovery tests
    never depend on a real 15-minute wall-clock wait for the execution
    attempt's own TTL to lapse naturally."""
    return utc_now() + timedelta(hours=1)


def recover_from_a_real_hard_kill(root: Path) -> dict[str, Any]:
    org = Organization.init(root)
    outcome = org.create_outcome(
        "Chapter 6", "the organization recovers from a hard kill", ["receipt"], "principal-human"
    )
    org.activate(outcome.id, "master-course")
    sow = org.create_sow(
        outcome.id, "Write the required offline report.", Role.OPERATOR, "master-course"
    )
    org.ready_sow(sow.id)
    assignment = org.assign(sow.id, "operator-course", "master-course")
    assignment_id = assignment.id
    org.db.close()

    worker = subprocess.Popen(  # noqa: S603 - fixed argv, no shell
        [sys.executable, str(FIXTURE), str(root), assignment_id]
    )
    reached_running = False
    try:
        deadline = time.monotonic() + 10
        while time.monotonic() < deadline:
            probe = Organization(root)
            state = probe._assignment(assignment_id).state  # noqa: SLF001
            probe.db.close()
            if state == AssignmentState.RUNNING:
                reached_running = True
                break
            time.sleep(0.1)
    finally:
        worker.kill()
        worker.wait(timeout=10)

    org2 = Organization(root)
    before_recovery = org2._assignment(assignment_id)  # noqa: SLF001
    attempt_row = org2.db.connection.execute(
        "SELECT current_execution_attempt FROM assignments WHERE id = ?", (assignment_id,)
    ).fetchone()

    # The supervisor -- never the dead process -- decides this attempt is
    # abandoned. A far-future clock stands in for waiting out the real
    # 15-minute execution-attempt TTL; the recovery logic itself is
    # unmodified production code, exercised exactly as `sovereign-agent
    # supervisor --once` would exercise it.
    first_tick = supervisor_module.tick(org2, clock=_far_future_clock)
    second_tick = supervisor_module.tick(org2, clock=_far_future_clock)

    after_recovery = org2._assignment(assignment_id)  # noqa: SLF001
    receipt_row = org2.db.connection.execute(
        "SELECT json_extract(record, '$.status') AS status, "
        "json_extract(record, '$.failure_category') AS failure_category "
        "FROM receipts WHERE json_extract(record, '$.assignment_id') = ?",
        (assignment_id,),
    ).fetchone()

    return {
        "worker_reached_running_before_sigkill": reached_running,
        "worker_died_abnormally": worker.returncode != 0,
        "before_recovery": {
            "assignment_state": before_recovery.state.value,
            "execution_attempt_still_referenced": attempt_row["current_execution_attempt"]
            is not None,
        },
        "first_tick": {
            "recovered_count": len(first_tick.recovered_assignments),
        },
        "second_tick_is_idempotent": {
            "recovered_count": len(second_tick.recovered_assignments),
        },
        "after_recovery": {
            "assignment_state": after_recovery.state.value,
            "receipt_status": receipt_row["status"],
            "receipt_failure_category": receipt_row["failure_category"],
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(recover_from_a_real_hard_kill(args.root), indent=2, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
