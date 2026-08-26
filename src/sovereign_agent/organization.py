"""Organization root: config, SQLite ledger, and governance projections."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from sovereign_agent.actors import load_actors, write_config
from sovereign_agent.checks import CheckResult, run_check
from sovereign_agent.database import Database
from sovereign_agent.errors import Refusal
from sovereign_agent.events import append_event
from sovereign_agent.evidence import digest_payload
from sovereign_agent.execution import invoke_actor, write_failed_receipt
from sovereign_agent.governance import project_outcome, project_ruling
from sovereign_agent.ids import new_id, utc_now
from sovereign_agent.models import (
    Acceptance,
    Actor,
    Assignment,
    AssignmentState,
    Evidence,
    Message,
    Outcome,
    OutcomeState,
    Receipt,
    Review,
    Role,
    Ruling,
    SowState,
    StatementOfWork,
    Verification,
)
from sovereign_agent.policy import (
    advance_outcome,
    advance_sow,
    assignment_may_run,
    forbid_self_approval,
    require_authority,
)
from sovereign_agent.providers import get_provider
from sovereign_agent.relay import inbox as relay_inbox
from sovereign_agent.relay import send as relay_send


class Organization:
    def __init__(self, root: Path) -> None:
        self.root = root.resolve()
        self.config_path = self.root / "sovereign.toml"
        self.db = Database(self.root / ".sovereign" / "organization.db")
        self.actors = (
            {actor.id: actor for actor in load_actors(self.config_path)}
            if self.config_path.exists()
            else {}
        )

    @classmethod
    def init(cls, root: Path) -> Organization:
        root.mkdir(parents=True, exist_ok=True)
        write_config(root / "sovereign.toml")
        (root / "governance" / "outcomes").mkdir(parents=True, exist_ok=True)
        (root / "governance" / "rulings").mkdir(parents=True, exist_ok=True)
        (root / "artifacts").mkdir(exist_ok=True)
        org = cls(root)
        with org.db.transaction():
            for actor in org.actors.values():
                org.db.put("actors", actor.id, actor.model_dump(mode="json"))
            append_event(org.db, "organization.initialized", {"root": str(root)})
        return org

    def actor(self, actor_id: str) -> Actor:
        if actor_id not in self.actors:
            raise Refusal(
                "Unknown actor.",
                "Actor ids are instance ids, not roles.",
                "actor list",
                "Use an id from sovereign.toml.",
            )
        return self.actors[actor_id]

    def rebind_actor(self, actor_id: str, provider: str, authority_id: str) -> Actor:
        authority = self.actor(authority_id)
        require_authority(authority.role, "rule")
        get_provider(provider)
        actor = self.actor(actor_id)
        actor.provider = provider
        config = {
            "schema_version": 1,
            "actors": [item.model_dump(mode="json") for item in self.actors.values()],
        }
        write_config(self.config_path, config)
        with self.db.transaction():
            self.db.put("actors", actor.id, actor.model_dump(mode="json"))
            append_event(
                self.db,
                "actor.provider_rebound",
                {"actor_id": actor.id, "provider": provider, "by": authority_id},
            )
        return actor

    def create_outcome(
        self,
        title: str,
        desired_state: str,
        checks: list[str],
        owner: str,
        subject: str = "",
    ) -> Outcome:
        actor = self.actor(owner)
        require_authority(actor.role, "define_outcome")
        outcome = Outcome(
            id=new_id("out"),
            title=title,
            desired_state=desired_state,
            subject=subject,
            acceptance_checks=checks,
            state=OutcomeState.PROPOSED,
            owner_actor_id=owner,
            created_at=utc_now(),
        )
        with self.db.transaction():
            self.db.put("outcomes", outcome.id, outcome.model_dump(mode="json"))
            append_event(self.db, "outcome.created", {"id": outcome.id})
        project_outcome(self.root, outcome, [])
        return outcome

    def activate(self, outcome_id: str, actor_id: str) -> Outcome:
        actor = self.actor(actor_id)
        require_authority(actor.role, "plan")
        outcome = self._outcome(outcome_id)
        outcome.state = advance_outcome(outcome.state, OutcomeState.ACTIVE)
        self._save_outcome(outcome, "outcome.activated")
        return outcome

    def create_sow(
        self,
        outcome_id: str,
        scope: str,
        role: Role,
        actor_id: str,
        required_effect_kind: str | None = None,
    ) -> StatementOfWork:
        actor = self.actor(actor_id)
        require_authority(actor.role, "plan")
        sow = StatementOfWork(
            id=new_id("sow"),
            outcome_id=outcome_id,
            scope=scope,
            required_effect_kind=required_effect_kind,
            non_goals=["expand authority", "skip evidence"],
            deliverables=["report.json"],
            done_when="Evidence exists and a different actor has reviewed it.",
            assignee_role=role,
            state=SowState.DRAFT,
            created_at=utc_now(),
        )
        with self.db.transaction():
            self.db.put("sows", sow.id, sow.model_dump(mode="json"))
            append_event(self.db, "sow.created", {"id": sow.id})
        self._project_outcome(outcome_id)
        return sow

    def ready_sow(self, sow_id: str) -> StatementOfWork:
        sow = self._sow(sow_id)
        sow.state = advance_sow(sow.state, SowState.READY)
        self._save_sow(sow, "sow.ready")
        return sow

    def assign(self, sow_id: str, actor_id: str, planner_id: str) -> Assignment:
        planner = self.actor(planner_id)
        require_authority(planner.role, "assign")
        worker = self.actor(actor_id)
        sow = self._sow(sow_id)
        if worker.role != sow.assignee_role:
            raise Refusal(
                "Role mismatch.",
                "Assignments bind one actor instance to one SOW.",
                "actor list",
                "Pick an actor with the SOW role.",
            )
        # READY -> ASSIGNED is the first attempt; CHANGES_REQUESTED -> ASSIGNED
        # is recovery. Policy always allowed the second transition and nothing
        # ever used it, so a SOW that had changes requested was terminal: the
        # only way forward was to delete the organization and start over. That
        # is the opposite of what Chapter 2 teaches about refusal.
        # Refuse every source state except the two that can legitimately start
        # work. `assign()` used to create a row from ANY state and only advance
        # from these two, so a double-click left a second assignment that could
        # never run -- and `_latest_assignment_id` immediately treated it as the
        # proof identity, invalidating an otherwise sound outcome.
        if sow.state not in {SowState.READY, SowState.CHANGES_REQUESTED}:
            raise Refusal(
                f"A SOW in {sow.state} cannot be assigned.",
                "Only work that is ready, or that has had changes requested, "
                "can be handed to an actor. A retry must not silently create a "
                "second execution that can never run.",
                "sovereign-agent status",
                "Wait for the current execution, or request changes first.",
            )

        assignment = Assignment(
            id=new_id("asg"),
            sow_id=sow.id,
            actor_id=actor_id,
            prompt_ref=sow.scope,
            workspace_id=new_id("ws"),
            state=AssignmentState.CREATED,
            created_at=utc_now(),
        )
        # The state check, the transition and the insert share one immediate
        # transaction, so two connections cannot both pass the check.
        with self.db.immediate() as connection:
            current = json.loads(
                connection.execute("SELECT record FROM sows WHERE id = ?", (sow.id,)).fetchone()[
                    "record"
                ]
            )["state"]
            if current not in {SowState.READY.value, SowState.CHANGES_REQUESTED.value}:
                raise Refusal(
                    f"A SOW in {current} cannot be assigned.",
                    "Another connection claimed this SOW first.",
                    "sovereign-agent status",
                    "Wait for the current execution.",
                )
            sow.state = advance_sow(SowState(current), SowState.ASSIGNED)
            connection.execute(
                "INSERT OR REPLACE INTO sows(id, outcome_id, record) VALUES (?, ?, ?)",
                (sow.id, sow.outcome_id, sow.model_dump_json()),
            )
            connection.execute(
                "INSERT INTO assignments(id, sow_id, actor_id, record) VALUES (?, ?, ?, ?)",
                (assignment.id, sow.id, actor_id, assignment.model_dump_json()),
            )
            append_event(self.db, "assignment.created", {"id": assignment.id, "actor_id": actor_id})
        self._project_outcome(sow.outcome_id)
        return assignment

    def run_assignment(self, assignment_id: str) -> Assignment:
        assignment = self._assignment(assignment_id)
        assignment_may_run(assignment.state)
        worker = self.actor(assignment.actor_id)
        sow = self._sow(assignment.sow_id)
        sow.state = advance_sow(sow.state, SowState.RUNNING)
        workspace = self.root / ".sovereign" / "runs" / assignment.workspace_id
        output = workspace / ".sovereign-out"
        workspace.mkdir(parents=True, exist_ok=True)
        assignment.state = AssignmentState.RUNNING
        self._save_assignment(assignment, sow, "assignment.running")
        started_at = utc_now()
        failure: Exception | None = None
        try:
            receipt, report = invoke_actor(
                worker, sow, workspace, output, assignment_id=assignment.id
            )
        except Refusal as error:
            receipt = write_failed_receipt(
                worker,
                workspace,
                error.category,
                str(error),
                started_at,
                assignment_id=assignment.id,
            )
            report = None
            failure = error
        except Exception as error:
            receipt = write_failed_receipt(
                worker,
                workspace,
                "internal_error",
                f"{type(error).__name__}: {error}",
                started_at,
                assignment_id=assignment.id,
            )
            report = None
            failure = error
        receipt_json = (workspace / "receipt.json").read_text(encoding="utf-8")
        with self.db.transaction():
            self.db.put_serialized("receipts", receipt.id, receipt_json)
            if report and report.status == "completed":
                assignment.state = AssignmentState.COMPLETED
                sow.state = advance_sow(SowState.RUNNING, SowState.REVIEW)
            elif report and report.status == "blocked":
                assignment.state = AssignmentState.BLOCKED
                sow.state = advance_sow(SowState.RUNNING, SowState.BLOCKED)
            else:
                assignment.state = AssignmentState.FAILED
                sow.state = advance_sow(SowState.RUNNING, SowState.FAILED)
            self.db.put("assignments", assignment.id, assignment.model_dump(mode="json"))
            self.db.put("sows", sow.id, sow.model_dump(mode="json"))
            append_event(
                self.db, "assignment.finished", {"id": assignment.id, "status": assignment.state}
            )
        self._project_outcome(sow.outcome_id)
        if failure is not None:
            raise failure
        return assignment

    def review(self, sow_id: str, reviewer_id: str) -> Review:
        """An independent actor reviews the work and leaves a durable record.

        No `performer_id` parameter: the performers come from the assignments in
        the ledger. A caller that names the performer supplies the evidence for
        its own separation check.

        The review binds to the evidence that exists at review time and the state
        digest it was read against, so `accept()` can ask what the reviewer
        actually saw. Reviewing before any evidence exists is refused -- the
        SOW's own `done_when` requires evidence, so approving without it would
        contradict the document being approved.
        """
        reviewer = self.actor(reviewer_id)
        require_authority(reviewer.role, "review")
        sow = self._sow(sow_id)
        performers = self.performers_for(sow.outcome_id)
        for performer_id in sorted(performers):
            forbid_self_approval(performer_id, reviewer_id)

        # Only the CURRENT batch. Scanning every historical row meant one failed
        # check poisoned every later review forever, so a corrected world could
        # never be re-reviewed.
        # THIS SOW's own verification, selected by sow_id rather than by row
        # order across the outcome. The relational chain is checked rather than
        # assumed: verification.sow_id -> assignment.sow_id -> the reviewed SOW.
        verification = self.verification_for_sow(sow_id)
        if verification is not None:
            execution = self.completed_assignment_for_sow(sow_id)
            if verification.sow_id != sow_id or verification.assignment_id != execution:
                raise Refusal(
                    f"Verification {verification.id} does not belong to SOW {sow_id}.",
                    "A SOW is independently governed work: its review must rest "
                    "on its own execution, not on a sibling's.",
                    "sovereign-agent verify",
                    "Verify this SOW's own assignment.",
                )
        if verification is None:
            raise Refusal(
                "No verification to review.",
                "The SOW's done_when requires evidence. Reviewing before it "
                "exists approves a document that contradicts itself.",
                "sovereign-agent verify",
                "Run verification first, then review.",
            )
        rows = self.db.connection.execute(
            "SELECT id, success, state_digest FROM evidence WHERE verification_id = ?",
            (verification.id,),
        ).fetchall()
        decision = "accepted" if verification.passed else "changes_requested"

        review = Review(
            id=new_id("rev"),
            sow_id=sow_id,
            outcome_id=sow.outcome_id,
            reviewer_actor_id=reviewer_id,
            performer_actor_ids=sorted(performers),
            verification_id=verification.id,
            evidence_refs=[str(row["id"]) for row in rows],
            decision=decision,
            # A digest over the WHOLE batch, not the last row that happened to
            # come back from the query.
            state_digest=verification.aggregate_digest,
            created_at=utc_now(),
        )
        if decision == "accepted":
            sow.state = advance_sow(sow.state, SowState.ACCEPTED)
        elif sow.state != SowState.CHANGES_REQUESTED:
            sow.state = advance_sow(sow.state, SowState.CHANGES_REQUESTED)

        with self.db.transaction():
            self.db.connection.execute(
                "INSERT INTO reviews(id, sow_id, outcome_id, reviewer_actor_id, decision, "
                "record, verification_id) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (
                    review.id,
                    sow_id,
                    sow.outcome_id,
                    reviewer_id,
                    decision,
                    review.model_dump_json(),
                    verification.id,
                ),
            )
            self.db.put("sows", sow.id, sow.model_dump(mode="json"))
            append_event(
                self.db,
                "sow.reviewed",
                {"id": sow.id, "review": review.id, "decision": decision, "by": reviewer_id},
            )
        for performer_id in sorted(performers):
            relay_send(self.db, reviewer_id, performer_id, "review", f"SOW {sow_id} {decision}")
        self._project_outcome(sow.outcome_id)
        return review

    def verify_sow(self, sow_id: str, verifier_id: str) -> list[CheckResult]:
        """Execute the declared checks FOR ONE NAMED SOW's execution.

        The caller says which work is being verified. The previous API took only
        an outcome and picked a SOW implicitly by row order, so with two
        completed SOWs one of them became permanently unreviewable and which one
        was arbitrary -- `sows_for()` has no ordering contract.
        """
        verifier = self.actor(verifier_id)
        require_authority(verifier.role, "run_checks")
        sow = self._sow(sow_id)
        outcome = self._outcome(sow.outcome_id)
        if outcome.state != OutcomeState.VERIFYING:
            outcome.state = advance_outcome(outcome.state, OutcomeState.VERIFYING)
            self._save_outcome(outcome, "outcome.verifying")

        execution_id = self.completed_assignment_for_sow(sow_id)
        if not execution_id:
            raise Refusal(
                f"SOW {sow_id} has no completed execution to verify.",
                "Verification inspects the result of work that has run.",
                "sovereign-agent status",
                "Run this SOW's assignment first.",
            )

        subject = outcome.subject
        results = [run_check(self.db, check_id, subject) for check_id in outcome.acceptance_checks]

        verification_id = new_id("ver")
        evidence_ids = [new_id("evd") for _ in results]
        aggregate = digest_payload(
            {
                "outcome_id": sow.outcome_id,
                "sow_id": sow_id,
                "assignment_id": execution_id,
                "checks": [
                    {"check_id": r.check_id, "success": r.success, "digest": r.state_digest}
                    for r in results
                ],
            }
        )
        verification = Verification(
            id=verification_id,
            outcome_id=sow.outcome_id,
            sow_id=sow_id,
            assignment_id=execution_id,
            evidence_refs=evidence_ids,
            check_ids=[r.check_id for r in results],
            aggregate_digest=aggregate,
            passed=all(r.success for r in results),
            created_at=utc_now(),
        )

        with self.db.transaction():
            self.db.connection.execute(
                "INSERT INTO verifications(id, outcome_id, sow_id, assignment_id, "
                "aggregate_digest, passed, record, created_at) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    verification_id,
                    sow.outcome_id,
                    sow_id,
                    execution_id,
                    aggregate,
                    1 if verification.passed else 0,
                    verification.model_dump_json(),
                    verification.created_at.isoformat(),
                ),
            )
            for evidence_id, result in zip(evidence_ids, results, strict=True):
                evidence = Evidence(
                    id=evidence_id,
                    assignment_id=execution_id,
                    outcome_id=sow.outcome_id,
                    check_id=result.check_id,
                    success=result.success,
                    observed=result.observed,
                    state_digest=result.state_digest,
                    kind=result.check_id,
                    command=["sovereign-agent", "verify", result.check_id],
                    exit_code=0 if result.success else 1,
                    artifact_refs=[],
                    digest=digest_payload(
                        {
                            "check_id": result.check_id,
                            "outcome_id": sow.outcome_id,
                            "success": result.success,
                            "observed": result.observed,
                        }
                    ),
                    verifier_actor_id=verifier_id,
                    created_at=utc_now(),
                )
                self.db.connection.execute(
                    "INSERT INTO evidence(id, assignment_id, record, outcome_id, check_id, "
                    "success, state_digest, verification_id) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                    (
                        evidence.id,
                        execution_id,
                        evidence.model_dump_json(),
                        sow.outcome_id,
                        result.check_id,
                        1 if result.success else 0,
                        result.state_digest,
                        verification_id,
                    ),
                )
            append_event(
                self.db,
                "sow.verified",
                {
                    "outcome_id": sow.outcome_id,
                    "sow_id": sow_id,
                    "verification_id": verification_id,
                    "by": verifier_id,
                    "passed": sum(1 for r in results if r.success),
                    "total": len(results),
                },
            )
        return results

    def verify_outcome(self, outcome_id: str, verifier_id: str) -> list[CheckResult]:
        """Verify every SOW of an outcome that has a completed execution.

        A convenience over `verify_sow`, kept because the single-SOW demo reads
        better without naming the SOW. It never guesses: it verifies them all.
        """
        results: list[CheckResult] = []
        verified_any = False
        for sow in self.sows_for(outcome_id):
            if self.completed_assignment_for_sow(sow.id):
                results = self.verify_sow(sow.id, verifier_id)
                verified_any = True
        if not verified_any:
            raise Refusal(
                f"Outcome {outcome_id} has no completed execution to verify.",
                "Verification inspects the result of work that has run.",
                "sovereign-agent status",
                "Run an assignment first.",
            )
        return results

    def verification_for_sow(self, sow_id: str) -> Verification | None:
        """The most recent verification OF THIS SOW."""
        row = self.db.connection.execute(
            "SELECT record FROM verifications WHERE sow_id = ? ORDER BY rowid DESC LIMIT 1",
            (sow_id,),
        ).fetchone()
        return Verification.model_validate_json(row["record"]) if row else None

    def latest_verification(self, outcome_id: str) -> Verification | None:
        """The most recent complete batch for this outcome."""
        row = self.db.connection.execute(
            "SELECT record FROM verifications WHERE outcome_id = ? ORDER BY rowid DESC LIMIT 1",
            (outcome_id,),
        ).fetchone()
        return Verification.model_validate_json(row["record"]) if row else None

    def completed_assignment_for_sow(self, sow_id: str) -> str:
        """The current completed execution OF THIS SOW. Empty if none has run.

        Proof is per-SOW because governance is per-SOW. Selecting the newest
        completed assignment across the whole outcome let one SOW's execution,
        evidence and effect stand as proof for a different SOW that did nothing.
        Narrowing "newest row" to "newest COMPLETED row" kept the shape and the
        defect; the shape was the defect.
        """
        rows = self.db.connection.execute(
            "SELECT id, record FROM assignments WHERE sow_id = ? ORDER BY rowid DESC",
            (sow_id,),
        ).fetchall()
        for row in rows:
            if json.loads(row["record"]).get("state") == AssignmentState.COMPLETED.value:
                return str(row["id"])
        return ""

    def _latest_assignment_id(self, outcome_id: str) -> str:
        """The completed execution of the outcome's most recently worked SOW.

        Retained only for the outcome-level world-check evidence binding; every
        per-SOW proof goes through `completed_assignment_for_sow`.
        """
        for sow in reversed(self.sows_for(outcome_id)):
            execution = self.completed_assignment_for_sow(sow.id)
            if execution:
                return execution
        return ""

    def contributing_executions(self, outcome_id: str) -> set[str]:
        """Executions that actually changed the world for this outcome.

        Read from the structured `effects` edge, not inferred from world state.
        """
        rows = self.db.connection.execute(
            "SELECT DISTINCT assignment_id FROM effects WHERE outcome_id = ?",
            (outcome_id,),
        ).fetchall()
        return {str(row["assignment_id"]) for row in rows}

    def effect_kinds_for_execution(self, assignment_id: str) -> set[str]:
        """What this specific execution changed, by kind."""
        rows = self.db.connection.execute(
            "SELECT DISTINCT kind FROM effects WHERE assignment_id = ?", (assignment_id,)
        ).fetchall()
        return {str(row["kind"]) for row in rows}

    def performers_for(self, outcome_id: str) -> set[str]:
        """Who actually did the work, DERIVED FROM THE LEDGER.

        Never ask the caller who performed the work. A caller that supplies the
        performer supplies the evidence for its own separation check.
        """
        sow_ids = {sow.id for sow in self.sows_for(outcome_id)}
        rows = self.db.connection.execute("SELECT sow_id, actor_id FROM assignments").fetchall()
        return {str(row["actor_id"]) for row in rows if row["sow_id"] in sow_ids}

    def _trusted_receipt(self, assignment_id: str) -> Receipt:
        """Load one receipt, validating every source against the others.

        The indexed columns and the canonical JSON are two representations of
        one fact. Reading only the column let an edit to the record alone pass
        acceptance while the external verifier called the same state
        unverifiable -- an accepted state known to be false by another tool.
        """
        row = self.db.connection.execute(
            "SELECT record, assignment_id, status FROM receipts WHERE assignment_id = ?",
            (assignment_id,),
        ).fetchone()
        if row is None:
            raise Refusal(
                f"No receipt for execution {assignment_id or '(none)'}.",
                "An execution with no receipt left no evidence that it ran.",
                "sovereign-agent status",
                "Run the assignment.",
            )
        receipt = Receipt.model_validate_json(row["record"])
        if receipt.assignment_id != str(row["assignment_id"]):
            raise Refusal(
                f"Receipt {receipt.id} disagrees with its index on assignment.",
                "Two representations of one fact must agree, or neither is trusted.",
                "sovereign-agent status",
                "Re-run the assignment.",
            )
        if receipt.status != str(row["status"]):
            raise Refusal(
                f"Receipt {receipt.id} says {receipt.status}, its index says {row['status']}.",
                "Two representations of one fact must agree, or neither is trusted.",
                "sovereign-agent status",
                "Re-run the assignment.",
            )
        if receipt.status != "completed":
            raise Refusal(
                f"The execution receipt reports status {receipt.status}.",
                "Work that did not succeed cannot support an accepted outcome.",
                "sovereign-agent status",
                "Fix the failure and re-run the assignment.",
            )
        return receipt

    def _require_deliverables(self, sow: StatementOfWork, execution: str) -> None:
        """Every declared deliverable must exist in the execution's workspace.

        A non-effectful SOW changes nothing in the world, so the only thing
        distinguishing "delivered" from "ran and returned" is the artifact it
        promised. Judging such a SOW by the outcome's store checks would be the
        name/value mismatch this unit exists to remove, one scope up.
        """
        assignment = self._assignment(execution)
        output = self.root / ".sovereign" / "runs" / assignment.workspace_id / ".sovereign-out"
        for deliverable in sow.deliverables:
            if not (output / deliverable).is_file():
                raise Refusal(
                    f"SOW {sow.id} promised {deliverable} and did not produce it.",
                    "A unit of work is done when its deliverable exists, not "
                    "when its execution returns.",
                    str(output),
                    "Re-run the assignment so it writes its deliverable.",
                )

    def _trusted_review(self, row: Any) -> Review:
        """Load one review, validating the record against its indexed columns."""
        review = Review.model_validate_json(row["record"])
        for field, column in (
            (review.decision, "decision"),
            (review.reviewer_actor_id, "reviewer_actor_id"),
            (review.verification_id, "verification_id"),
        ):
            if field != str(row[column]):
                raise Refusal(
                    f"Review {review.id} disagrees with its index on {column}.",
                    "Two representations of one fact must agree, or neither is trusted.",
                    "sovereign-agent status",
                    "Obtain a fresh review.",
                )
        return review

    def accept(self, outcome_id: str, accepter_id: str) -> Acceptance:
        """Accept only if the declared outcome is TRUE RIGHT NOW.

        Acceptance does not trust a list of evidence ids handed to it. A caller
        that supplies its own proof is not being checked. Instead this:

        1. re-derives who performed the work, from assignments in the ledger;
        2. requires every SOW to be accepted;
        3. RE-EXECUTES every declared check against current state;
        4. requires stored evidence for every declared check, bound to this
           outcome and this execution, and successful;
        5. requires the stored evidence to still describe the world it was
           written about (state digest agreement).

        Step 3 is the one that matters. Evidence is an audit record of what was
        observed; the guarantee comes from asking the world again at the moment
        of acceptance. Stock sold between verification and acceptance makes the
        claim false, and this refuses.
        """
        accepter = self.actor(accepter_id)
        require_authority(accepter.role, "accept")
        outcome = self._outcome(outcome_id)

        performers = self.performers_for(outcome_id)
        for performer_id in sorted(performers):
            forbid_self_approval(performer_id, accepter_id)

        sows = self.sows_for(outcome_id)
        if not sows:
            raise Refusal(
                "No SOW exists for this outcome.",
                "An outcome with no work cannot have been delivered.",
                "sovereign-agent status",
                "Create and complete a SOW first.",
            )
        if any(sow.state != SowState.ACCEPTED for sow in sows):
            raise Refusal(
                "SOWs remain open.",
                "Acceptance requires every SOW to be accepted.",
                "sovereign-agent status",
                "Finish review first.",
            )
        if not outcome.acceptance_checks:
            raise Refusal(
                "Outcome declares no acceptance checks.",
                "An outcome nobody can check cannot be proved true.",
                "governance/outcomes",
                "Declare at least one acceptance check.",
            )

        execution_id = self._latest_assignment_id(outcome_id)
        # Subject is read from the outcome, not supplied. Otherwise acceptance
        # could be pointed at a healthy product while the real one sits empty.
        current = {
            check_id: run_check(self.db, check_id, outcome.subject)
            for check_id in outcome.acceptance_checks
        }
        failed_now = sorted(cid for cid, result in current.items() if not result.success)
        if failed_now:
            raise Refusal(
                f"Checks failing at acceptance time: {', '.join(failed_now)}.",
                "Accepted means the declared outcome is true NOW, not that it was "
                "true once when a check happened to run.",
                "sovereign-agent verify",
                "Fix the world, then verify and accept again.",
            )

        # The work must have SUCCEEDED. Acceptance previously never looked at
        # receipts, so an outcome whose only receipt said "failed" still accepted.
        self._trusted_receipt(execution_id)

        # The bound execution must have CONTRIBUTED. Ruling
        # 2026-08-26-outcomes-are-conditions-sows-are-work: an outcome is a
        # standing condition and a SOW is a unit of work, so acceptance asserts
        # both that the condition holds now AND that this execution produced an
        # effect. Without this, an assignment that did nothing inherits credit
        # for a restock done last week, because the checks find replenishments
        # by SKU and the world is still in the state the earlier work left it.
        # Every SOW is validated on ITS OWN proof, then the outcome's world
        # condition is re-checked. Previously one execution could satisfy the
        # whole outcome, so a SOW that did nothing rode on a sibling's work.
        for sow in sows:
            execution = self.completed_assignment_for_sow(sow.id)
            if not execution:
                raise Refusal(
                    f"SOW {sow.id} has no completed execution.",
                    "Every unit of work must have been done by someone.",
                    "sovereign-agent status",
                    "Run this SOW's assignment.",
                )
            self._trusted_receipt(execution)
            # Every SOW must have DELIVERED, effectful or not. For an
            # investigation the deliverable IS the proof: outcome-level store
            # checks say nothing about whether a report was written.
            self._require_deliverables(sow, execution)
            if sow.required_effect_kind is None:
                continue
            # No `if contributors and ...` guard: the empty case is the STRONGEST
            # form of "this execution did nothing", and guarding the requirement
            # with it made the requirement vacuous exactly when it mattered most.
            kinds = self.effect_kinds_for_execution(execution)
            if sow.required_effect_kind not in kinds:
                raise Refusal(
                    f"Execution {execution} produced no {sow.required_effect_kind} "
                    f"effect for SOW {sow.id}.",
                    "This SOW declares that it must change the world. The "
                    "condition may well hold, but it holds because of other work, "
                    "and accepting here would credit this execution with a change "
                    "it did not make.",
                    "sovereign-agent status",
                    "Do the work this SOW declares, or drop its required effect.",
                )

        # Acceptance rests on ONE verification batch, and the review must be of
        # that exact batch. Previously acceptance used whatever evidence existed
        # now while the review referenced whatever existed then, so a second
        # verification could replace every reviewed row and acceptance would
        # still report that the work had been reviewed.
        # Each SOW's proof chain is validated on its own verification. The
        # outcome-level evidence binding below then uses the verification of the
        # SOW that was verified last, which is the batch describing the world as
        # acceptance sees it.
        verification = None
        for sow in sows:
            sow_verification = self.verification_for_sow(sow.id)
            if sow_verification is None:
                raise Refusal(
                    f"SOW {sow.id} has not been verified.",
                    "Acceptance rests on a completed run of the declared checks "
                    "for every unit of work.",
                    "sovereign-agent verify",
                    "Verify each SOW.",
                )
            sow_reviews = self.db.connection.execute(
                "SELECT record, decision, reviewer_actor_id, verification_id FROM reviews "
                "WHERE sow_id = ? AND verification_id = ?",
                (sow.id, sow_verification.id),
            ).fetchall()
            if not sow_reviews:
                raise Refusal(
                    f"SOW {sow.id} has no review of its current verification.",
                    "The evidence supporting acceptance must be the evidence a "
                    "reviewer actually saw, not an earlier batch it replaced.",
                    "sovereign-agent status",
                    "Have a reviewer review this SOW's current verification.",
                )
            verification = sow_verification
        if verification is None:
            raise Refusal(
                "No verification for this outcome.",
                "Acceptance rests on a completed run of the declared checks.",
                "sovereign-agent verify",
                "Run verification first.",
            )
        review_rows = self.db.connection.execute(
            "SELECT record, decision, reviewer_actor_id, verification_id FROM reviews "
            "WHERE outcome_id = ? ORDER BY rowid DESC",
            (outcome_id,),
        ).fetchall()
        if not review_rows:
            raise Refusal(
                "No review record for this outcome.",
                "Acceptance requires an independent actor to have reviewed the work.",
                "sovereign-agent status",
                "Have a reviewer review the SOW.",
            )
        current_reviews = [
            row for row in review_rows if str(row["verification_id"]) == verification.id
        ]
        if not current_reviews:
            raise Refusal(
                "The current verification has not been reviewed.",
                "The evidence supporting acceptance must be the evidence a "
                "reviewer actually saw, not an earlier batch it replaced.",
                "sovereign-agent status",
                "Have a reviewer review the current verification.",
            )
        for row in current_reviews:
            self._trusted_review(row)
            if str(row["decision"]) != "accepted":
                raise Refusal(
                    f"Review by {row['reviewer_actor_id']} decided {row['decision']}.",
                    "An outcome cannot be accepted over an unresolved review.",
                    "sovereign-agent status",
                    "Repair the work, verify again, and obtain a new review.",
                )
            if str(row["reviewer_actor_id"]) == accepter_id:
                raise Refusal(
                    f"{accepter_id} reviewed this work and cannot also accept it.",
                    "Review and acceptance are separate acts by separate actors.",
                    "sovereign-agent actor list",
                    "Have the Principal accept.",
                )
        reviewed_evidence = set(self._trusted_review(current_reviews[0]).evidence_refs)

        rows = self.db.connection.execute(
            "SELECT id, check_id, success, state_digest, assignment_id FROM evidence "
            "WHERE outcome_id = ? AND verification_id = ?",
            (outcome_id, verification.id),
        ).fetchall()
        if {str(row["id"]) for row in rows} != reviewed_evidence:
            raise Refusal(
                "The reviewed evidence is not the evidence supporting acceptance.",
                "Evidence was added or removed after the review.",
                "sovereign-agent status",
                "Verify again and obtain a fresh review.",
            )
        by_check: dict[str, list[Any]] = {}
        for row in rows:
            by_check.setdefault(str(row["check_id"]), []).append(row)

        accepted_refs: list[str] = []
        for check_id in outcome.acceptance_checks:
            candidates = by_check.get(check_id, [])
            if not candidates:
                raise Refusal(
                    f"No evidence for declared check '{check_id}'.",
                    "Every declared check needs a record of having been run.",
                    "sovereign-agent verify",
                    "Run verification before accepting.",
                )
            usable = [row for row in candidates if int(row["success"]) == 1]
            if not usable:
                raise Refusal(
                    f"Evidence for '{check_id}' reports failure.",
                    "Failed evidence is a record of a problem, not a permission.",
                    "sovereign-agent verify",
                    "Fix the underlying problem and verify again.",
                )
            bound = [row for row in usable if str(row["assignment_id"]) == execution_id]
            if not bound:
                raise Refusal(
                    f"Evidence for '{check_id}' is not bound to this execution.",
                    "Evidence from another run does not prove this one.",
                    "sovereign-agent verify",
                    "Verify against the current assignment.",
                )
            fresh = [
                row for row in bound if str(row["state_digest"]) == current[check_id].state_digest
            ]
            if not fresh:
                raise Refusal(
                    f"Evidence for '{check_id}' is stale.",
                    "The state changed after this evidence was written, so it "
                    "describes a world that no longer exists.",
                    "sovereign-agent verify",
                    "Re-run verification against current state.",
                )
            accepted_refs.append(str(fresh[-1]["id"]))

        outcome.state = advance_outcome(outcome.state, OutcomeState.ACCEPTED)
        acceptance = Acceptance(
            outcome_id=outcome_id,
            accepted_by=accepter_id,
            evidence_refs=accepted_refs,
            accepted_at=utc_now(),
        )
        with self.db.transaction():
            self.db.put("outcomes", outcome.id, outcome.model_dump(mode="json"))
            self.db.connection.execute(
                "INSERT OR REPLACE INTO acceptance(outcome_id, record) VALUES (?, ?)",
                (outcome_id, acceptance.model_dump_json()),
            )
            append_event(
                self.db,
                "outcome.accepted",
                {"id": outcome_id, "by": accepter_id, "evidence": accepted_refs},
            )
        # NOT part of the transaction above: see docs/persistence-boundary.md.
        project_outcome(self.root, outcome, sows)
        return acceptance

    def rule(self, question: str, decision: str, authority_id: str, applies_to: str) -> Ruling:
        actor = self.actor(authority_id)
        require_authority(actor.role, "rule")
        ruling = Ruling(
            id=new_id("rul"),
            question=question,
            decision=decision,
            authority_actor_id=authority_id,
            applies_to=applies_to,
            state="decided",
            created_at=utc_now(),
        )
        with self.db.transaction():
            self.db.put("rulings", ruling.id, ruling.model_dump(mode="json"))
            append_event(self.db, "ruling.decided", {"id": ruling.id})
        project_ruling(self.root, ruling)
        return ruling

    def inbox(self, actor_id: str) -> list[Message]:
        return relay_inbox(self.db, actor_id)

    def sows_for(self, outcome_id: str) -> list[StatementOfWork]:
        rows = self.db.connection.execute("SELECT record FROM sows").fetchall()
        return [
            StatementOfWork.model_validate_json(row["record"])
            for row in rows
            if StatementOfWork.model_validate_json(row["record"]).outcome_id == outcome_id
        ]

    def _outcome(self, outcome_id: str) -> Outcome:
        raw = self.db.get("outcomes", "id", outcome_id)
        if raw is None:
            raise Refusal(
                "Outcome not found.", "Ids are stable.", "status", "Create an outcome first."
            )
        return Outcome.model_validate(raw)

    def _sow(self, sow_id: str) -> StatementOfWork:
        raw = self.db.get("sows", "id", sow_id)
        if raw is None:
            raise Refusal("SOW not found.", "Ids are stable.", "status", "Create a SOW first.")
        return StatementOfWork.model_validate(raw)

    def _assignment(self, assignment_id: str) -> Assignment:
        raw = self.db.get("assignments", "id", assignment_id)
        if raw is None:
            raise Refusal(
                "Assignment not found.", "Ids are stable.", "status", "Assign work first."
            )
        return Assignment.model_validate(raw)

    def _save_outcome(self, outcome: Outcome, kind: str) -> None:
        with self.db.transaction():
            self.db.put("outcomes", outcome.id, outcome.model_dump(mode="json"))
            append_event(self.db, kind, {"id": outcome.id, "state": outcome.state})
        self._project_outcome(outcome.id)

    def _save_sow(self, sow: StatementOfWork, kind: str) -> None:
        with self.db.transaction():
            self.db.put("sows", sow.id, sow.model_dump(mode="json"))
            append_event(self.db, kind, {"id": sow.id, "state": sow.state})
        self._project_outcome(sow.outcome_id)

    def _save_assignment(self, assignment: Assignment, sow: StatementOfWork, kind: str) -> None:
        with self.db.transaction():
            self.db.put("assignments", assignment.id, assignment.model_dump(mode="json"))
            self.db.put("sows", sow.id, sow.model_dump(mode="json"))
            append_event(self.db, kind, {"id": assignment.id})

    def _project_outcome(self, outcome_id: str) -> None:
        project_outcome(self.root, self._outcome(outcome_id), self.sows_for(outcome_id))

    def status_text(self, outcome_id: str) -> str:
        outcome = self._outcome(outcome_id)
        sows = self.sows_for(outcome_id)
        lines = [f"{outcome.id} {outcome.state} {outcome.title}"]
        lines.extend(f"  {sow.id} {sow.state} {sow.scope}" for sow in sows)
        return "\n".join(lines)
