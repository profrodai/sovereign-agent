"""Chapter 12: the pilot begins with a receipt.

Executes the pilot-start mechanism this unit builds (`reference_
organizations.store.pilot.start_pilot`) against an EXERCISE-SCOPED,
DISPOSABLE pilot identity -- never the real named pilot organization. The
real pilot-start act is a separate, later, separately-authorized act,
entirely outside this book's own curriculum (see `docs/v1-unit11-store-
expansion-pilot-start.md`'s own "what this unit did not do" section).

`EXERCISE_PILOT_ID` below is structurally distinct from any real pilot
identity: it carries a `book-ch12-exercise-` prefix that no real pilot-start
call anywhere in this project's own production code or tests ever uses, so
running this chapter's exercise -- or the curriculum gate that runs it
automatically -- can never collide with, or be mistaken for, a real pilot.

Distinguishes STARTED from FINISHED explicitly: this chapter's own exercise
proves a pilot record and a `pilot.started` event exist, durable and
queryable. It does not, and could not, claim the pilot is complete -- there
is no completion mechanism in this unit at all; that is Unit 12's own future
territory.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from reference_organizations.store.pilot import active_pilot_id, start_pilot
from sovereign_agent.database import Database

# Structurally distinct from a real pilot identity: this prefix is reserved
# for this chapter's own exercise and appears nowhere in this project's own
# real-pilot tooling (there is none yet -- Unit 12's own territory). Running
# this exercise, or the curriculum gate that runs it, can never reach a real
# pilot database or a real pilot identity by accident.
EXERCISE_PILOT_ID = "book-ch12-exercise-pilot"
EXERCISE_STORE_ORG_ID = "book-ch12-exercise-store-org"
EXERCISE_PILOT_PROFILE_ID = "book-ch12-exercise-profile"
EXERCISE_EVIDENCE_NAMESPACE = "book-ch12-exercise-evidence-ns"


def the_pilot_begins_with_a_receipt(root: Path) -> dict[str, Any]:
    db = Database(root / ".sovereign" / "organization.db")

    first = start_pilot(
        db,
        pilot_id=EXERCISE_PILOT_ID,
        store_org_id=EXERCISE_STORE_ORG_ID,
        pilot_profile_id=EXERCISE_PILOT_PROFILE_ID,
        evidence_namespace=EXERCISE_EVIDENCE_NAMESPACE,
    )
    # A replay of the SAME disposable identity: idempotent, no second row,
    # no second event -- the exact property proven under real concurrency in
    # tests/test_pilot.py, shown here as a single-process replay.
    second = start_pilot(
        db,
        pilot_id=EXERCISE_PILOT_ID,
        store_org_id=EXERCISE_STORE_ORG_ID,
        pilot_profile_id=EXERCISE_PILOT_PROFILE_ID,
        evidence_namespace=EXERCISE_EVIDENCE_NAMESPACE,
    )

    pilot_row = db.connection.execute(
        "SELECT pilot_id, started_at, store_org_id, pilot_profile_id, evidence_namespace "
        "FROM pilots WHERE pilot_id = ?",
        (EXERCISE_PILOT_ID,),
    ).fetchone()
    pilot_events = db.connection.execute(
        "SELECT COUNT(*) AS c FROM events WHERE kind = 'pilot.started'"
    ).fetchone()["c"]
    pilots_row_count = db.connection.execute("SELECT COUNT(*) AS c FROM pilots").fetchone()["c"]

    return {
        "disposable_identity": {
            "exercise_pilot_id": EXERCISE_PILOT_ID,
            "structurally_distinct_prefix": EXERCISE_PILOT_ID.startswith("book-ch12-exercise-"),
        },
        "first_start": {
            "idempotent_replay": first.idempotent_replay,
            "pilot_id": first.pilot_id,
        },
        "replay": {
            "idempotent_replay": second.idempotent_replay,
            "same_started_at_as_first": second.started_at == first.started_at,
        },
        "durable_record": {
            "pilot_row_exists": pilot_row is not None,
            "store_org_id": pilot_row["store_org_id"] if pilot_row else None,
            "pilot_profile_id": pilot_row["pilot_profile_id"] if pilot_row else None,
            "evidence_namespace": pilot_row["evidence_namespace"] if pilot_row else None,
        },
        "durable_event": {
            "pilot_started_event_count": pilot_events,
            "exactly_one_despite_the_replay_above": pilot_events == 1,
        },
        "no_duplicate_pilot_row": {"pilots_row_count": pilots_row_count},
        "active_pilot": {"pilot_id": active_pilot_id(db)},
        "started_is_not_finished": {
            "claim": "This pilot record proves the pilot STARTED. Nothing in "
            "this database, this function, or this project claims it has "
            "FINISHED -- there is no completion mechanism yet. That is Unit "
            "12's own future territory, not this chapter's.",
            "no_completion_table_exists": db.connection.execute(
                "SELECT COUNT(*) AS c FROM sqlite_master WHERE type = 'table' "
                "AND name LIKE '%pilot%complet%'"
            ).fetchone()["c"]
            == 0,
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(the_pilot_begins_with_a_receipt(args.root), indent=2, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
