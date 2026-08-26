"""Organization root: config, SQLite ledger, and governance projections."""

from __future__ import annotations

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
    Review,
    Role,
    Ruling,
    SowState,
    StatementOfWork,
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

    def create_sow(self, outcome_id: str, scope: str, role: Role, actor_id: str) -> StatementOfWork:
        actor = self.actor(actor_id)
        require_authority(actor.role, "plan")
        sow = StatementOfWork(
            id=new_id("sow"),
            outcome_id=outcome_id,
            scope=scope,
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
        if sow.state == SowState.READY:
            sow.state = advance_sow(sow.state, SowState.ASSIGNED)
        assignment = Assignment(
            id=new_id("asg"),
            sow_id=sow.id,
            actor_id=actor_id,
            prompt_ref=sow.scope,
            workspace_id=new_id("ws"),
            state=AssignmentState.CREATED,
            created_at=utc_now(),
        )
        with self.db.transaction():
            self.db.put("sows", sow.id, sow.model_dump(mode="json"))
            self.db.put("assignments", assignment.id, assignment.model_dump(mode="json"))
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

        rows = self.db.connection.execute(
            "SELECT id, success, state_digest FROM evidence WHERE outcome_id = ?",
            (sow.outcome_id,),
        ).fetchall()
        if not rows:
            raise Refusal(
                "No evidence to review.",
                "The SOW's done_when requires evidence. Reviewing before it "
                "exists approves a document that contradicts itself.",
                "sovereign-agent verify",
                "Run verification first, then review.",
            )
        failing = [str(row["id"]) for row in rows if int(row["success"]) != 1]
        decision = "changes_requested" if failing else "accepted"

        review = Review(
            id=new_id("rev"),
            sow_id=sow_id,
            outcome_id=sow.outcome_id,
            reviewer_actor_id=reviewer_id,
            performer_actor_ids=sorted(performers),
            evidence_refs=[str(row["id"]) for row in rows],
            decision=decision,
            state_digest=str(rows[-1]["state_digest"]),
            created_at=utc_now(),
        )
        if decision == "accepted":
            sow.state = advance_sow(sow.state, SowState.ACCEPTED)
        else:
            sow.state = advance_sow(sow.state, SowState.CHANGES_REQUESTED)

        with self.db.transaction():
            self.db.connection.execute(
                "INSERT INTO reviews(id, sow_id, outcome_id, reviewer_actor_id, decision, "
                "record) VALUES (?, ?, ?, ?, ?, ?)",
                (
                    review.id,
                    sow_id,
                    sow.outcome_id,
                    reviewer_id,
                    decision,
                    review.model_dump_json(),
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

    def verify_outcome(self, outcome_id: str, verifier_id: str) -> list[CheckResult]:
        """Actually execute every declared acceptance check and persist evidence.

        This used to advance a state field and nothing else. A verification that
        runs no checks is a rubber stamp with a spinner.

        Unknown, malformed, or erroring checks fail closed. Evidence is written
        for every declared check, pass or fail, so a failed verification leaves a
        durable record of WHY rather than a silent absence.
        """
        verifier = self.actor(verifier_id)
        require_authority(verifier.role, "run_checks")
        outcome = self._outcome(outcome_id)
        if outcome.state != OutcomeState.VERIFYING:
            outcome.state = advance_outcome(outcome.state, OutcomeState.VERIFYING)
            self._save_outcome(outcome, "outcome.verifying")

        execution_id = self._latest_assignment_id(outcome_id)
        # The SUBJECT comes from the outcome, never from the caller. A caller
        # that picks the subject picks which world gets inspected.
        subject = outcome.subject
        results = [run_check(self.db, check_id, subject) for check_id in outcome.acceptance_checks]
        with self.db.transaction():
            for result in results:
                evidence = Evidence(
                    id=new_id("evd"),
                    assignment_id=execution_id,
                    outcome_id=outcome_id,
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
                            "outcome_id": outcome_id,
                            "success": result.success,
                            "observed": result.observed,
                        }
                    ),
                    verifier_actor_id=verifier_id,
                    created_at=utc_now(),
                )
                self.db.connection.execute(
                    "INSERT INTO evidence(id, assignment_id, record, outcome_id, check_id, "
                    "success, state_digest) VALUES (?, ?, ?, ?, ?, ?, ?)",
                    (
                        evidence.id,
                        execution_id,
                        evidence.model_dump_json(),
                        outcome_id,
                        result.check_id,
                        1 if result.success else 0,
                        result.state_digest,
                    ),
                )
            append_event(
                self.db,
                "outcome.verified",
                {
                    "id": outcome_id,
                    "by": verifier_id,
                    "passed": sum(1 for r in results if r.success),
                    "total": len(results),
                },
            )
        return results

    def _latest_assignment_id(self, outcome_id: str) -> str:
        """The execution evidence is bound to. Empty when no work has run yet."""
        sow_ids = {sow.id for sow in self.sows_for(outcome_id)}
        rows = self.db.connection.execute(
            "SELECT id, sow_id FROM assignments ORDER BY rowid DESC"
        ).fetchall()
        for row in rows:
            if row["sow_id"] in sow_ids:
                return str(row["id"])
        return ""

    def performers_for(self, outcome_id: str) -> set[str]:
        """Who actually did the work, DERIVED FROM THE LEDGER.

        Never ask the caller who performed the work. A caller that supplies the
        performer supplies the evidence for its own separation check.
        """
        sow_ids = {sow.id for sow in self.sows_for(outcome_id)}
        rows = self.db.connection.execute("SELECT sow_id, actor_id FROM assignments").fetchall()
        return {str(row["actor_id"]) for row in rows if row["sow_id"] in sow_ids}

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
        receipt_row = self.db.connection.execute(
            "SELECT record, status FROM receipts WHERE assignment_id = ?", (execution_id,)
        ).fetchone()
        if receipt_row is None:
            raise Refusal(
                f"No receipt for execution {execution_id or '(none)'}.",
                "An execution with no receipt left no evidence that it ran.",
                "sovereign-agent status",
                "Run the assignment.",
            )
        if str(receipt_row["status"]) != "completed":
            raise Refusal(
                f"The execution receipt reports status {receipt_row['status']}.",
                "Work that did not succeed cannot support an accepted outcome.",
                "sovereign-agent status",
                "Fix the failure and re-run the assignment.",
            )

        # An independent review must exist, and must have accepted.
        review_rows = self.db.connection.execute(
            "SELECT record, decision, reviewer_actor_id FROM reviews WHERE outcome_id = ?",
            (outcome_id,),
        ).fetchall()
        if not review_rows:
            raise Refusal(
                "No review record for this outcome.",
                "Acceptance requires an independent actor to have reviewed the work.",
                "sovereign-agent status",
                "Have a reviewer review the SOW.",
            )
        for row in review_rows:
            if str(row["decision"]) != "accepted":
                raise Refusal(
                    f"Review {row['reviewer_actor_id']} decided {row['decision']}.",
                    "An outcome cannot be accepted over an unresolved review.",
                    "sovereign-agent status",
                    "Resolve the review first.",
                )
            if str(row["reviewer_actor_id"]) == accepter_id:
                raise Refusal(
                    f"{accepter_id} reviewed this work and cannot also accept it.",
                    "Review and acceptance are separate acts by separate actors.",
                    "sovereign-agent actor list",
                    "Have the Principal accept.",
                )

        rows = self.db.connection.execute(
            "SELECT id, check_id, success, state_digest, assignment_id FROM evidence "
            "WHERE outcome_id = ?",
            (outcome_id,),
        ).fetchall()
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
