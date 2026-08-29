"""Durable Pydantic records. Extra fields are forbidden."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

SCHEMA_VERSION = 1


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")
    schema_version: int = SCHEMA_VERSION


class OutcomeState(StrEnum):
    PROPOSED = "PROPOSED"
    ACTIVE = "ACTIVE"
    VERIFYING = "VERIFYING"
    ACCEPTED = "ACCEPTED"
    BLOCKED = "BLOCKED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


class SowState(StrEnum):
    DRAFT = "DRAFT"
    READY = "READY"
    ASSIGNED = "ASSIGNED"
    RUNNING = "RUNNING"
    REVIEW = "REVIEW"
    ACCEPTED = "ACCEPTED"
    CHANGES_REQUESTED = "CHANGES_REQUESTED"
    BLOCKED = "BLOCKED"
    FAILED = "FAILED"


class AssignmentState(StrEnum):
    CREATED = "CREATED"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    BLOCKED = "BLOCKED"


class MessageState(StrEnum):
    NEW = "NEW"
    CLAIMED = "CLAIMED"
    DONE = "DONE"
    DEAD = "DEAD"


class Role(StrEnum):
    PRINCIPAL = "principal"
    MASTER = "master"
    OPERATOR = "operator"
    SPARRING = "sparring"
    VERIFIER = "verifier"


class Outcome(StrictModel):
    """A state of the world someone wants, and how to check it.

    `subject` is what the checks are ABOUT — the SKU, in the store. It lives on
    the outcome rather than being passed in at verification time, because a
    caller who chooses the subject chooses which world gets inspected, and can
    point acceptance at a healthy product while the real one sits empty.
    """

    id: str
    title: str
    desired_state: str
    subject: str = ""
    acceptance_checks: list[str]
    state: OutcomeState
    owner_actor_id: str
    created_at: datetime


class StatementOfWork(StrictModel):
    """A unit of work: a deliverable and the test for having delivered it.

    `required_effect_kind` says whether this SOW must change the world, and how.
    Not every legitimate SOW does — an investigation or a report may deliver
    without moving inventory — so "the execution must have contributed" cannot
    be a universal rule. It is a rule the SOW declares about itself, and
    acceptance then enforces exactly what was declared.
    """

    id: str
    outcome_id: str
    scope: str
    required_effect_kind: str | None = None
    non_goals: list[str]
    deliverables: list[str]
    done_when: str
    assignee_role: Role
    state: SowState
    created_at: datetime


class Ruling(StrictModel):
    id: str
    question: str
    decision: str
    authority_actor_id: str
    applies_to: str
    state: str
    created_at: datetime


class Actor(StrictModel):
    id: str
    role: Role
    provider: str
    authority: list[str]
    workspace_policy: str = "temporary_directory"
    status: str = "active"


class Assignment(StrictModel):
    id: str
    sow_id: str
    actor_id: str
    prompt_ref: str
    workspace_id: str
    state: AssignmentState
    created_at: datetime


class Message(StrictModel):
    id: str
    sender: str
    recipient: str
    subject: str
    body: str
    reply_to: str | None = None
    state: MessageState
    claim_owner: str | None = None
    claim_expires_at: datetime | None = None
    # Unit 8: minted fresh every time a claim is won (never on the idempotent
    # same-owner-unexpired return). complete()/dead_letter() must present the
    # exact token bound at claim time, verified atomically -- closes F-U4-1's
    # "returns the stale lease without renewing it" defect by making the
    # returned lease carry proof of whether it is fresh or stale.
    fencing_token: int | None = None
    retry_count: int = 0
    created_at: datetime


class Approval(StrictModel):
    id: str
    assignment_id: str
    effect_digest: str
    requested_by: str
    decided_by: str | None = None
    decision: str = "pending"
    created_at: datetime


class Evidence(StrictModel):
    """A record of one check having been run, bound to what it proves.

    `outcome_id`, `check_id` and `assignment_id` are the binding: they say which
    question was asked, about which outcome, during which execution. Without
    them an evidence id is just a filename, and acceptance cannot tell proof
    from decoration.
    """

    id: str
    assignment_id: str
    kind: str
    command: list[str]
    exit_code: int
    artifact_refs: list[str]
    digest: str
    created_at: datetime
    outcome_id: str = ""
    check_id: str = ""
    success: bool = False
    observed: dict[str, Any] = Field(default_factory=dict)
    state_digest: str = ""
    verifier_actor_id: str = ""


class Receipt(StrictModel):
    """What an execution did. `assignment_id` ties it to the work it describes.

    Without that field a receipt floats free: acceptance cannot tell whether the
    successful receipt it found belongs to the execution being accepted.
    """

    id: str
    assignment_id: str = ""
    actor_id: str
    provider: str
    provider_session_ref: str | None
    provider_usage: dict[str, int] = Field(default_factory=dict)
    started_at: datetime
    ended_at: datetime
    status: str
    failure_category: str | None = None
    failure_message: str | None = None
    evidence_refs: list[str]


class Verification(StrictModel):
    """One complete run of an outcome's declared checks.

    A batch, not a loose pile. Review binds to one verification id and
    acceptance requires a review of the exact batch it is accepting on, so
    "Sparring reviewed this outcome" cannot silently mean "Sparring reviewed
    some earlier evidence that has since been replaced".
    """

    id: str
    outcome_id: str
    sow_id: str
    assignment_id: str
    evidence_refs: list[str]
    check_ids: list[str]
    aggregate_digest: str
    passed: bool
    created_at: datetime


class Review(StrictModel):
    """An independent actor's durable judgement of one SOW.

    Bound to the evidence it read and the state it read them against, so a later
    reader can ask what the reviewer actually saw rather than trusting that a
    status field once changed.
    """

    id: str
    sow_id: str
    outcome_id: str
    reviewer_actor_id: str
    performer_actor_ids: list[str]
    verification_id: str
    evidence_refs: list[str]
    decision: str
    state_digest: str
    created_at: datetime


class Acceptance(StrictModel):
    outcome_id: str
    accepted_by: str
    evidence_refs: list[str]
    accepted_at: datetime


class Signal(StrictModel):
    id: str
    kind: str
    source: str
    subject_ref: str
    severity: str
    observed_at: datetime
    payload_digest: str
    dedupe_key: str


class ActorReport(StrictModel):
    """What an actor reports back. Advisory, not authoritative.

    `proposed_checks` and `proposed_restock_units` are REQUESTS. Deterministic
    Python decides which checks actually run and whether the proposal is sound.
    """

    status: str = Field(pattern="^(completed|blocked|failed)$")
    proposed_restock_units: int | None = None
    changed_artifacts: list[str] = Field(default_factory=list)
    proposed_checks: list[str] = Field(default_factory=list)
    questions: list[str] = Field(default_factory=list)
    notes: str = ""


class PulseOrigin(StrictModel):
    """The structured, queryable answer to "manual or Pulse, and from what?"

    Ruling 2026-08-29-unit9-pulse-is-separate-from-supervisor, holding 2:
    absence of a CLI invocation, process logs, or a manual-origin row is
    NOT proof. Every SOW -- manually planned or Pulse-created -- gets
    exactly one of these rows, so "which kind is this" is always a column
    read, never an inference from what is missing.
    """

    id: str
    origin_kind: str
    sow_id: str
    assignment_id: str | None = None
    wake_decision_id: str | None = None
    pulse_event_id: str | None = None
    created_at: datetime


class EventRecord(StrictModel):
    seq: int | None = None
    id: str
    kind: str
    payload: dict[str, Any]
    created_at: datetime
