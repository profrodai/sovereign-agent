"""Pulse: sale -> signal -> deterministic wake gate -> proactive governed work.

A distinct mechanism from `supervisor.py`, per the governing ruling
(`docs/rulings/2026-08-29-unit9-pulse-is-separate-from-supervisor.md`):
`Supervisor.tick()` never imports this module, never calls it, and this
module never imports `supervisor.py`. The two compose only through a
foreground caller running each as its own separate operation with its own
separate receipt -- never as a fourth reconciliation step.

One deterministic pass (`run_pulse_once`) does exactly what the governing SOW
requires, in order:

1. Resume every already-fired signal whose canonical assignment is still
   `CREATED` -- the crash-window case: canonical creation committed, but no
   process ever reached `run_assignment` for it.
2. Read durable signals not yet evaluated to a wake decision, oldest first.
3. Ask the caller-supplied wake gate whether each one fires.
4. Atomically claim the canonical decision and create the SOW, assignment,
   Pulse event, and origin links (`Organization.create_pulse_work`).
5. Invoke the existing production `Organization.run_assignment()` for a
   newly created or safely resumable assignment.
6. Return a structured report.

The wake gate itself is intentionally NOT here: this module is
domain-agnostic (a signal in, a decision or nothing out), and the Store's own
gate -- "is this SKU still below reorder, does exactly one active outcome
match" -- lives in `reference_organizations/store`, outside this package's
budget, exactly as the governing SOW asks ("a Store-specific gate over
parallel abstractions").
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from functools import partial

from sovereign_agent.errors import Refusal
from sovereign_agent.models import Assignment, AssignmentState, Role, Signal
from sovereign_agent.organization import Organization


@dataclass(frozen=True)
class WakeDecision:
    """What the wake gate decided, when a signal qualifies to fire.

    Carries everything `Organization.create_pulse_work` needs to create the
    canonical SOW and assignment -- the gate decides the WHAT (which
    outcome, which scope, which actors); `create_pulse_work` alone decides
    the HOW (atomically, exactly once per source signal).
    """

    outcome_id: str
    scope: str
    role: Role
    planner_id: str
    worker_id: str
    required_effect_kind: str | None = None


WakeGate = Callable[[Organization, Signal], WakeDecision | None]


@dataclass(frozen=True)
class PulseItem:
    """One signal's outcome for this pass, for the structured report."""

    signal_id: str
    status: str  # created | replayed | skipped | refused | already_running
    sow_id: str | None = None
    assignment_id: str | None = None
    assignment_state: str | None = None
    detail: str = ""


@dataclass(frozen=True)
class PulseReport:
    items: tuple[PulseItem, ...] = field(default_factory=tuple)

    @property
    def created(self) -> tuple[PulseItem, ...]:
        return tuple(item for item in self.items if item.status == "created")


def _unevaluated_signals(org: Organization) -> list[Signal]:
    """Every durable signal with no wake decision yet, oldest first.

    A signal that already has a `pulse_wake_decisions` row (fired or not --
    the row exists the instant this process wins the CAS, before the SOW
    itself is created) is never re-offered to the GATE: re-evaluating it
    would either race the canonical creation transaction pointlessly or, for
    a signal the gate would now refuse, produce no new information. Read
    fresh, from the current authoritative Store state, exactly as the SOW
    requires -- this is a live SELECT, not a cached list. A signal that
    already fired but whose assignment has not yet reached a terminal or
    running state is picked up separately, by `_resumable_signals` below --
    this function is only ever about NEW gate evaluations.
    """
    rows = org.db.connection.execute(
        "SELECT s.record AS record FROM signals s "
        "LEFT JOIN pulse_wake_decisions wd ON wd.source_signal_id = s.id "
        "WHERE wd.id IS NULL ORDER BY s.rowid"
    ).fetchall()
    return [Signal.model_validate_json(row["record"]) for row in rows]


def _resumable_signals(org: Organization) -> list[tuple[Signal, str, Assignment]]:
    """Every signal that already fired but whose canonical assignment is
    still `CREATED` -- the crash-window case: canonical creation committed,
    but no process ever reached `run_assignment` for it (a hard kill between
    the two, or simply a prior pass that created it and exited). Resuming
    invokes that SAME assignment; it never creates a second one, because the
    signal already has its one, unique `pulse_wake_decisions` row.
    """
    rows = org.db.connection.execute(
        "SELECT s.record AS signal_record, po.sow_id, po.assignment_id, a.record AS asg_record "
        "FROM signals s "
        "JOIN pulse_wake_decisions wd ON wd.source_signal_id = s.id "
        "JOIN pulse_origins po ON po.wake_decision_id = wd.id "
        "JOIN assignments a ON a.id = po.assignment_id "
        "WHERE json_extract(a.record, '$.state') = 'CREATED' "
        "ORDER BY s.rowid"
    ).fetchall()
    return [
        (
            Signal.model_validate_json(row["signal_record"]),
            str(row["sow_id"]),
            Assignment.model_validate_json(row["asg_record"]),
        )
        for row in rows
    ]


def _source_event_id(org: Organization, signal_id: str) -> str | None:
    """The `sale.committed` event that this signal was minted alongside.

    Looked up by the same `json_extract` pattern `organization.py`'s
    `effect_kinds_for_execution` already uses -- the signal and its
    committing event are two rows written inside ONE transaction
    (`record_sale`), so an event that cannot be found here means the source
    relationship is missing or inconsistent, which the wake gate's own
    fail-closed contract (SOW section "Store wake gate") must refuse on.
    """
    row = org.db.connection.execute(
        "SELECT id FROM events WHERE kind = 'sale.committed' "
        "AND json_extract(payload, '$.signal_id') = ?",
        (signal_id,),
    ).fetchone()
    return str(row["id"]) if row is not None else None


def _still_qualifies(org: Organization, gate: WakeGate, signal: Signal) -> bool:
    """The `revalidate` callback `create_pulse_work` calls INSIDE its own
    open transaction (F-U9-1's fix) -- re-asks the SAME gate a second time,
    under the write lock, rather than trusting the read `run_pulse_once`
    took before the transaction existed."""
    return gate(org, signal) is not None


def run_pulse_once(org: Organization, gate: WakeGate) -> PulseReport:
    """One deterministic pass. No sleeping, no looping, no retry policy."""
    items: list[PulseItem] = []
    for signal, sow_id, assignment in _resumable_signals(org):
        items.append(_invoke_or_report(org, signal.id, sow_id, assignment, created=False))
    for signal in _unevaluated_signals(org):
        source_event_id = _source_event_id(org, signal.id)
        if source_event_id is None:
            items.append(
                PulseItem(
                    signal.id,
                    "skipped",
                    detail="no source sale.committed event found for this signal",
                )
            )
            continue
        decision = gate(org, signal)
        if decision is None:
            items.append(PulseItem(signal.id, "skipped", detail="wake gate did not fire"))
            continue
        # F-U9-1's fix: re-ask the SAME gate again, INSIDE create_pulse_work's
        # own open transaction, immediately before anything is written. The
        # condition this gate checked a moment ago (read outside any lock)
        # could have changed by the time the transaction actually acquires
        # its write lock -- a concurrent apply_restock resolving the exact
        # signal this pass is about to act on, for instance. Re-checking
        # only under the lock is what makes "still qualifies" mean something
        # at the moment it is acted on, not merely at the moment it was read.
        try:
            result = org.create_pulse_work(
                source_signal_id=signal.id,
                source_event_id=source_event_id,
                subject=signal.subject_ref,
                outcome_id=decision.outcome_id,
                scope=decision.scope,
                role=decision.role,
                planner_id=decision.planner_id,
                worker_id=decision.worker_id,
                required_effect_kind=decision.required_effect_kind,
                revalidate=partial(_still_qualifies, org, gate, signal),
            )
        except Refusal as error:
            items.append(PulseItem(signal.id, "refused", detail=str(error)))
            continue
        if result is None:
            items.append(
                PulseItem(
                    signal.id,
                    "skipped",
                    detail="wake gate no longer fired once the transaction's lock was held",
                )
            )
            continue
        sow, assignment, created = result
        items.append(_invoke_or_report(org, signal.id, sow.id, assignment, created))
    return PulseReport(tuple(items))


def _invoke_or_report(
    org: Organization, signal_id: str, sow_id: str, assignment: Assignment, created: bool
) -> PulseItem:
    """Run the canonical assignment if it is CREATED; otherwise report its
    current terminal or in-flight state without bypassing Unit 8 fencing.

    `RUNNING` is reported, never invoked again -- a second `run_assignment`
    call on an already-RUNNING assignment would go through the exact same
    actor-lease and execution-attempt fencing every other caller does and
    would simply be refused there; reporting it here avoids manufacturing
    that refusal and is more honest about what this pass actually observed.
    `COMPLETED`, `BLOCKED`, and `FAILED` are terminal: Pulse never guesses
    success and never invents an automatic retry policy (SOW section 5).
    """
    if assignment.state == AssignmentState.RUNNING:
        return PulseItem(
            signal_id,
            "already_running",
            sow_id,
            assignment.id,
            assignment.state.value,
            "an execution attempt is already live for this canonical assignment",
        )
    if assignment.state != AssignmentState.CREATED:
        return PulseItem(
            signal_id,
            "replayed",
            sow_id,
            assignment.id,
            assignment.state.value,
            "canonical work is terminal; not re-invoked",
        )
    try:
        ran = org.run_assignment(assignment.id)
    except Refusal as error:
        return PulseItem(signal_id, "refused", sow_id, assignment.id, None, str(error))
    return PulseItem(
        signal_id,
        "created" if created else "replayed",
        sow_id,
        ran.id,
        ran.state.value,
    )
