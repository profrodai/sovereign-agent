"""Organization root: config, SQLite ledger, and governance projections."""

from __future__ import annotations

from pathlib import Path

from sovereign_agent.actors import load_actors, write_config
from sovereign_agent.database import Database
from sovereign_agent.errors import Refusal
from sovereign_agent.events import append_event
from sovereign_agent.execution import invoke_actor, write_failed_receipt
from sovereign_agent.governance import project_outcome, project_ruling
from sovereign_agent.ids import new_id, utc_now
from sovereign_agent.models import (
    Acceptance,
    Actor,
    Assignment,
    AssignmentState,
    Message,
    Outcome,
    OutcomeState,
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
        self, title: str, desired_state: str, checks: list[str], owner: str
    ) -> Outcome:
        actor = self.actor(owner)
        require_authority(actor.role, "define_outcome")
        outcome = Outcome(
            id=new_id("out"),
            title=title,
            desired_state=desired_state,
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
            receipt, report = invoke_actor(worker, sow, workspace, output)
        except Refusal as error:
            receipt = write_failed_receipt(
                worker,
                workspace,
                error.category,
                str(error),
                started_at,
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

    def review(self, sow_id: str, reviewer_id: str, performer_id: str) -> StatementOfWork:
        reviewer = self.actor(reviewer_id)
        require_authority(reviewer.role, "review")
        forbid_self_approval(performer_id, reviewer_id)
        sow = self._sow(sow_id)
        sow.state = advance_sow(sow.state, SowState.ACCEPTED)
        relay_send(self.db, reviewer_id, performer_id, "review", f"SOW {sow_id} accepted")
        self._save_sow(sow, "sow.reviewed")
        return sow

    def verify_outcome(self, outcome_id: str, verifier_id: str) -> Outcome:
        verifier = self.actor(verifier_id)
        require_authority(verifier.role, "run_checks")
        outcome = self._outcome(outcome_id)
        outcome.state = advance_outcome(outcome.state, OutcomeState.VERIFYING)
        self._save_outcome(outcome, "outcome.verifying")
        return outcome

    def accept(
        self, outcome_id: str, accepter_id: str, performer_id: str, evidence_ids: list[str]
    ) -> Acceptance:
        accepter = self.actor(accepter_id)
        require_authority(accepter.role, "accept")
        forbid_self_approval(performer_id, accepter_id)
        outcome = self._outcome(outcome_id)
        sows = self.sows_for(outcome_id)
        if any(sow.state != SowState.ACCEPTED for sow in sows):
            raise Refusal(
                "SOWs remain open.",
                "Acceptance requires every SOW to be accepted.",
                "status",
                "Finish review first.",
            )
        if not evidence_ids:
            raise Refusal(
                "No evidence.",
                "Prose cannot set work to accepted.",
                "verify",
                "Run verifier checks.",
            )
        outcome.state = advance_outcome(outcome.state, OutcomeState.ACCEPTED)
        acceptance = Acceptance(
            outcome_id=outcome_id,
            accepted_by=accepter_id,
            evidence_refs=evidence_ids,
            accepted_at=utc_now(),
        )
        with self.db.transaction():
            self.db.put("outcomes", outcome.id, outcome.model_dump(mode="json"))
            self.db.connection.execute(
                "INSERT OR REPLACE INTO acceptance(outcome_id, record) VALUES (?, ?)",
                (outcome_id, acceptance.model_dump_json()),
            )
            append_event(self.db, "outcome.accepted", {"id": outcome_id, "by": accepter_id})
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
