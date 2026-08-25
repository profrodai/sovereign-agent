"""Pure authority and state-machine transitions."""

from __future__ import annotations

from sovereign_agent.errors import Refusal
from sovereign_agent.models import AssignmentState, OutcomeState, Role, SowState

OUTCOME_TRANSITIONS: dict[OutcomeState, set[OutcomeState]] = {
    OutcomeState.PROPOSED: {OutcomeState.ACTIVE, OutcomeState.CANCELLED},
    OutcomeState.ACTIVE: {
        OutcomeState.VERIFYING,
        OutcomeState.BLOCKED,
        OutcomeState.FAILED,
        OutcomeState.CANCELLED,
    },
    OutcomeState.VERIFYING: {
        OutcomeState.ACCEPTED,
        OutcomeState.ACTIVE,
        OutcomeState.FAILED,
        OutcomeState.BLOCKED,
    },
    OutcomeState.BLOCKED: {OutcomeState.ACTIVE, OutcomeState.CANCELLED, OutcomeState.FAILED},
}

SOW_TRANSITIONS: dict[SowState, set[SowState]] = {
    SowState.DRAFT: {SowState.READY, SowState.FAILED},
    SowState.READY: {SowState.ASSIGNED, SowState.BLOCKED, SowState.FAILED},
    SowState.ASSIGNED: {SowState.RUNNING, SowState.BLOCKED, SowState.FAILED},
    SowState.RUNNING: {SowState.REVIEW, SowState.BLOCKED, SowState.FAILED},
    SowState.REVIEW: {SowState.ACCEPTED, SowState.CHANGES_REQUESTED, SowState.FAILED},
    SowState.CHANGES_REQUESTED: {SowState.ASSIGNED},
}

ROLE_AUTHORITY: dict[Role, set[str]] = {
    Role.PRINCIPAL: {"define_outcome", "accept", "grant_exception", "rule"},
    Role.MASTER: {"plan", "assign", "integrate", "request_ruling"},
    Role.OPERATOR: {"read", "write_workspace", "run_checks", "report"},
    Role.SPARRING: {"read", "review", "rule"},
    Role.VERIFIER: {"run_checks", "record_evidence"},
}


def require_authority(role: Role, action: str) -> None:
    if action not in ROLE_AUTHORITY[role]:
        raise Refusal(
            happened=f"Role {role} attempted {action}.",
            why="Authority is granted by role, not by a provider or a prompt.",
            inspect="sovereign-agent actor list",
            next_command="Choose an actor whose role includes this action.",
        )


def advance_outcome(current: OutcomeState, proposed: OutcomeState) -> OutcomeState:
    allowed = OUTCOME_TRANSITIONS.get(current, set())
    if proposed not in allowed:
        raise Refusal(
            happened=f"Outcome cannot move from {current} to {proposed}.",
            why="Outcome states are forward-only except documented recoveries.",
            inspect="sovereign-agent status",
            next_command="Use a legal transition or file a ruling.",
        )
    return proposed


def advance_sow(current: SowState, proposed: SowState) -> SowState:
    allowed = SOW_TRANSITIONS.get(current, set())
    if proposed not in allowed:
        raise Refusal(
            happened=f"SOW cannot move from {current} to {proposed}.",
            why="Work states change only through authorized events.",
            inspect="sovereign-agent status",
            next_command="Assign, run, review, or request changes using the CLI.",
        )
    return proposed


def forbid_self_approval(performer_id: str, accepter_id: str) -> None:
    if performer_id == accepter_id:
        raise Refusal(
            happened="The actor that performed the work tried to accept it.",
            why="No self-approval: review and acceptance require a different actor.",
            inspect="governance/outcomes and .sovereign/organization.db",
            next_command="sovereign-agent accept must be run by principal or sparring.",
        )


def assignment_may_run(state: AssignmentState) -> None:
    if state not in {AssignmentState.CREATED, AssignmentState.RUNNING}:
        raise Refusal(
            happened=f"Assignment in {state} cannot run.",
            why="Only created or recovered running assignments may be invoked.",
            inspect="sovereign-agent status",
            next_command="Create a new assignment or resume a blocked one.",
        )
