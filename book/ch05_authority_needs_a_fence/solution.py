"""Chapter 5: authority needs a fence, not just a rulebook.

Exercises the production fencing primitives directly (`acquire_actor_lease`,
`acquire_execution_attempt`) and then proves the stale-worker refusal path
end to end: two genuinely separate `Organization` instances -- standing in
for two separate operating-system processes -- contend for the SAME actor,
through the real `run_assignment` path every other caller uses. Imports the
production package throughout; nothing here reimplements a lease.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from sovereign_agent import fencing
from sovereign_agent.errors import Refusal
from sovereign_agent.models import Role
from sovereign_agent.organization import Organization


def explore_fencing(root: Path) -> dict[str, Any]:
    org = Organization.init(root)

    # 1. acquire_actor_lease is a compare-and-set: the first caller wins, a
    # second process id is refused outright while the lease is live.
    process_a = fencing.new_process_identity()
    process_b = fencing.new_process_identity()
    lease_a = fencing.acquire_actor_lease(org.db, "operator-course", process_a)
    lease_results: dict[str, str] = {
        "process_a_acquired": f"token={lease_a.fencing_token}",
    }
    try:
        fencing.acquire_actor_lease(org.db, "operator-course", process_b)
        lease_results["process_b_while_a_holds_it"] = "ALLOWED (this would be a bug)"
    except Refusal as error:
        lease_results["process_b_while_a_holds_it"] = f"refused: {error.category}"

    # release_actor_lease is a compare-and-set too: only the exact
    # (process_identity, fencing_token) pair that acquired it may release it.
    released = fencing.release_actor_lease(org.db, "operator-course", process_a, lease_a.fencing_token)
    lease_results["process_a_released"] = str(released)
    lease_b = fencing.acquire_actor_lease(org.db, "operator-course", process_b)
    lease_results["process_b_now_acquires_cleanly"] = f"token={lease_b.fencing_token}"
    fencing.release_actor_lease(org.db, "operator-course", process_b, lease_b.fencing_token)

    # 2. acquire_execution_attempt requires a CURRENT actor lease, re-verified
    # against the durable row inside its own transaction -- not merely
    # trusted from an earlier read.
    outcome = org.create_outcome(
        "Chapter 5", "authority is fenced, not merely assumed", ["receipt"], "principal-human"
    )
    org.activate(outcome.id, "master-course")
    sow = org.create_sow(outcome.id, "Write the required offline report.", Role.OPERATOR, "master-course")
    org.ready_sow(sow.id)
    assignment = org.assign(sow.id, "operator-course", "master-course")

    fresh_process = fencing.new_process_identity()
    fresh_lease = fencing.acquire_actor_lease(org.db, "operator-course", fresh_process)
    attempt = fencing.acquire_execution_attempt(
        org.db, assignment.id, "operator-course", fresh_process, fresh_lease.fencing_token
    )
    attempt_results: dict[str, str] = {"acquired": f"attempt_id={attempt.id}"}
    try:
        fencing.acquire_execution_attempt(
            org.db, assignment.id, "operator-course", fresh_process, fresh_lease.fencing_token
        )
        attempt_results["second_attempt_same_assignment"] = "ALLOWED (this would be a bug)"
    except Refusal as error:
        attempt_results["second_attempt_same_assignment"] = f"refused: {error.category}"
    try:
        fencing.acquire_execution_attempt(
            org.db, assignment.id, "operator-course", fresh_process, actor_lease_fencing_token=-1
        )
        attempt_results["stale_lease_token"] = "ALLOWED (this would be a bug)"
    except Refusal as error:
        attempt_results["stale_lease_token"] = f"refused: {error.category}"
    fencing.release_actor_lease(org.db, "operator-course", fresh_process, fresh_lease.fencing_token)

    # 3. The stale-worker refusal path, end to end, through the REAL
    # production run_assignment path: a genuinely live actor lease held by
    # a DIFFERENT process identity refuses a second, different assignment
    # for the SAME actor, before the provider is ever invoked -- the exact
    # process-level exclusivity gap the governing ruling named. A live
    # not-yet-expired lease is established directly with the same primitive
    # run_assignment itself calls at its own top (matching
    # tests/test_fencing.py::
    # test_the_ordinary_run_assignment_path_cannot_bypass_the_actor_lease),
    # rather than stalling a real invocation with threading -- simpler and
    # deterministic for a teaching exercise, proving the identical fence.
    sow2 = org.create_sow(
        outcome.id, "Write a second required offline report.", Role.OPERATOR, "master-course"
    )
    org.ready_sow(sow2.id)
    assignment2 = org.assign(sow2.id, "operator-course", "master-course")

    other_process = fencing.new_process_identity()
    other_lease = fencing.acquire_actor_lease(org.db, "operator-course", other_process)

    process_org = Organization(root)  # a genuinely separate Organization instance
    two_process_result: dict[str, Any]
    try:
        process_org.run_assignment(assignment2.id)
        two_process_result = {"outcome": "ALLOWED (this would be a bug)"}
    except Refusal as error:
        two_process_result = {"outcome": "refused", "category": error.category}
    still_created = process_org._assignment(assignment2.id).state  # noqa: SLF001

    fencing.release_actor_lease(org.db, "operator-course", other_process, other_lease.fencing_token)

    # Now that the competing lease is released, the second assignment for
    # the SAME actor runs cleanly under a fresh process.
    finished2 = org.run_assignment(assignment2.id)

    return {
        "actor_lease_cas": lease_results,
        "execution_attempt_fencing": attempt_results,
        "second_process_same_actor_different_assignment": two_process_result,
        "assignment_never_reached_running": still_created,
        "same_actor_next_assignment_after_release": finished2.state,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(explore_fencing(args.root), indent=2, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
