from __future__ import annotations

from pathlib import Path

import pytest
from pydantic import ValidationError

from reference_organizations.store import cash_balance_cents, record_sale, seed
from reference_organizations.store.demo import run_simulated
from sovereign_agent.errors import Refusal
from sovereign_agent.events import replay
from sovereign_agent.models import Outcome, Role
from sovereign_agent.organization import Organization
from sovereign_agent.policy import require_authority
from sovereign_agent.relay import claim, send


def test_extra_fields_are_forbidden() -> None:
    with pytest.raises(ValidationError):
        Outcome(
            id="out_x",
            title="t",
            desired_state="d",
            acceptance_checks=[],
            state="PROPOSED",  # type: ignore[arg-type]
            owner_actor_id="principal-human",
            created_at="2026-01-01T00:00:00Z",  # type: ignore[arg-type]
            surprise=True,  # type: ignore[call-arg]
        )


def test_operator_cannot_accept(tmp_path: Path) -> None:
    org = Organization.init(tmp_path)
    with pytest.raises(Refusal, match="Role operator"):
        require_authority(Role.OPERATOR, "accept")
    outcome = org.create_outcome("t", "d", ["c"], "principal-human")
    org.activate(outcome.id, "master-course")
    with pytest.raises(Refusal):
        org.accept(outcome.id, "operator-course", "operator-course", ["evd"])


def test_sale_is_atomic_with_event(tmp_path: Path) -> None:
    org = Organization.init(tmp_path)
    seed(org.db)
    before = len(replay(org.db))
    signal = record_sale(org.db, "SKU-TEA", 2, 400)
    assert signal.kind == "inventory.changed"
    events = replay(org.db)
    assert events[-1].kind == "sale.committed"
    assert cash_balance_cents(org.db) == 10_800
    assert len(events) == before + 1


def test_mailbox_rejects_wrong_actor(tmp_path: Path) -> None:
    org = Organization.init(tmp_path)
    message = send(org.db, "master-course", "sparring-course", "hello", "review please")
    with pytest.raises(Refusal, match="subagent"):
        claim(org.db, message.id, "invented-sparring")
    claimed = claim(org.db, message.id, "sparring-course")
    assert claimed.claim_owner == "sparring-course"


def test_simulated_store_reaches_accepted(tmp_path: Path) -> None:
    text = run_simulated(tmp_path)
    assert "ACCEPTED" in text
    org = Organization(tmp_path)
    outcome_id = text.split()[0]
    assert org._outcome(outcome_id).state.value == "ACCEPTED"  # noqa: SLF001
    assert (tmp_path / "governance" / "outcomes" / outcome_id / "README.md").exists()
