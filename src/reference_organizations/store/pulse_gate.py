"""The Store's own wake gate: a genuine sale-origin signal, still below
reorder, mapped unambiguously to one active governed outcome.

Lives outside `sovereign_agent`'s own budget on purpose (the governing SOW:
"a Store-specific gate over parallel abstractions") -- this is domain logic
about tea and shelves, not a general Pulse mechanism. `sovereign_agent.pulse`
knows nothing about SKUs, reorder points, or the Store's actor roster; it
only knows how to call a `WakeGate` and act atomically on what it returns.
"""

from __future__ import annotations

import json

from reference_organizations.store import below_reorder
from sovereign_agent.models import OutcomeState, Role, Signal
from sovereign_agent.organization import Organization
from sovereign_agent.pulse import WakeDecision

# The same actor roster the Store's own manual demo (`demo.py`) already uses.
# Pulse dispatches through the identical production `assign`/`run_assignment`
# path a human operator would, to the same actors -- no Pulse-only role.
PLANNER_ACTOR_ID = "master-course"
WORKER_ACTOR_ID = "operator-course"


def store_wake_gate(org: Organization, signal: Signal) -> WakeDecision | None:
    """Fail closed on every ambiguity named in the governing SOW.

    A qualifying trigger is a genuine sale-origin `inventory.changed` signal
    whose subject is CURRENTLY below its reorder point (re-checked now, not
    trusted from the signal's own `severity` at the time it was written --
    stock may have already been replenished since) and maps to EXACTLY one
    ACTIVE outcome naming that subject.
    """
    if signal.kind != "inventory.changed" or signal.source != "sale":
        return None
    sku = signal.subject_ref
    if sku not in below_reorder(org.db):
        return None  # the condition that triggered this signal has already resolved

    rows = org.db.connection.execute("SELECT record FROM outcomes").fetchall()
    matching = []
    for row in rows:
        record = json.loads(row["record"])
        if record.get("subject") == sku and record.get("state") == OutcomeState.ACTIVE.value:
            matching.append(record)
    if len(matching) != 1:
        return None  # zero or ambiguous -- no durable rule disambiguates more than one

    outcome_id = str(matching[0]["id"])
    return WakeDecision(
        outcome_id=outcome_id,
        scope=f"Pulse-dispatched replenishment after signal {signal.id}",
        role=Role.OPERATOR,
        planner_id=PLANNER_ACTOR_ID,
        worker_id=WORKER_ACTOR_ID,
        required_effect_kind="replenishment",
    )
