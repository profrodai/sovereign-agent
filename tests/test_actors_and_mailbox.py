"""An actor is not a model, and authority is not self-granted.

Unit 4 built these mechanisms; this file proves they behave as claimed. The
distinction matters most when it is inconvenient: an actor whose provider is
swapped is still the same governed identity, with the same authority, answerable
for the same work.
"""

from __future__ import annotations

from datetime import timedelta
from pathlib import Path

import pytest

from sovereign_agent.errors import Refusal
from sovereign_agent.ids import utc_now
from sovereign_agent.models import MessageState, Role
from sovereign_agent.organization import Organization
from sovereign_agent.policy import forbid_self_approval, require_authority
from sovereign_agent.relay import claim, complete, dead_letter, inbox, send


def test_actor_id_is_distinct_from_role_and_provider(tmp_path: Path) -> None:
    org = Organization.init(tmp_path)
    operator = org.actor("operator-course")
    assert operator.id == "operator-course"
    assert operator.role == Role.OPERATOR
    assert operator.provider == "scripted"
    # Two different actors can share a role and a provider and remain distinct.
    assert org.actor("master-course").provider == operator.provider
    assert org.actor("master-course").id != operator.id


def test_rebinding_the_provider_preserves_identity_and_authority(tmp_path: Path) -> None:
    """Swap the intelligence; the governed actor is unchanged.

    This is the whole point of the actor/provider split. The organization does
    not care which model does the thinking; it cares who is accountable.
    """
    org = Organization.init(tmp_path)
    before = org.actor("operator-course")
    identity, role, authority = before.id, before.role, list(before.authority)

    rebound = org.rebind_actor("operator-course", "claude", "principal-human")

    assert rebound.id == identity
    assert rebound.role == role
    assert rebound.authority == authority
    assert rebound.provider == "claude"
    reloaded = Organization(tmp_path).actor("operator-course")
    assert reloaded.provider == "claude"
    assert reloaded.id == identity


def test_rebinding_requires_ruling_authority(tmp_path: Path) -> None:
    org = Organization.init(tmp_path)
    with pytest.raises(Refusal):
        org.rebind_actor("operator-course", "claude", "operator-course")


def test_an_actor_cannot_expand_its_own_authority(tmp_path: Path) -> None:
    """Authority comes from the role table, not from the actor record.

    Editing the actor's own authority list must not grant the power to accept.
    """
    org = Organization.init(tmp_path)
    operator = org.actor("operator-course")
    operator.authority.append("accept")
    with pytest.raises(Refusal, match="Role operator attempted accept"):
        require_authority(operator.role, "accept")


def test_role_separation_covers_operator_reviewer_and_principal(tmp_path: Path) -> None:
    org = Organization.init(tmp_path)
    assert org.actor("operator-course").role == Role.OPERATOR
    assert org.actor("sparring-course").role == Role.SPARRING
    assert org.actor("principal-human").role == Role.PRINCIPAL
    with pytest.raises(Refusal):
        require_authority(Role.OPERATOR, "accept")
    with pytest.raises(Refusal):
        require_authority(Role.OPERATOR, "review")
    with pytest.raises(Refusal):
        require_authority(Role.SPARRING, "accept")
    require_authority(Role.SPARRING, "review")
    require_authority(Role.PRINCIPAL, "accept")


def test_no_self_approval_is_policy_not_convention() -> None:
    """The refusal is a pure function, callable without any UI in the way."""
    with pytest.raises(Refusal, match="No self-approval"):
        forbid_self_approval("operator-course", "operator-course")
    forbid_self_approval("operator-course", "sparring-course")


def test_reviewer_cannot_review_its_own_work(tmp_path: Path) -> None:
    org = Organization.init(tmp_path)
    outcome = org.create_outcome("t", "d", ["cash_reconciles"], "principal-human")
    org.activate(outcome.id, "master-course")
    sow = org.create_sow(outcome.id, "scope", Role.OPERATOR, "master-course")
    with pytest.raises(Refusal, match="No self-approval"):
        org.review(sow.id, "sparring-course", "sparring-course")


def test_claim_lease_is_exclusive(tmp_path: Path) -> None:
    org = Organization.init(tmp_path)
    message = send(org.db, "master-course", "sparring-course", "hello", "review please")
    claimed = claim(org.db, message.id, "sparring-course")
    assert claimed.claim_owner == "sparring-course"
    assert claimed.claim_expires_at is not None
    with pytest.raises(Refusal, match="cannot claim"):
        claim(org.db, message.id, "operator-course")


def test_expired_lease_is_reclaimable(tmp_path: Path) -> None:
    org = Organization.init(tmp_path)
    message = send(org.db, "master-course", "sparring-course", "hello", "body")
    claimed = claim(org.db, message.id, "sparring-course")
    claimed.claim_expires_at = utc_now() - timedelta(minutes=1)
    org.db.put("messages", claimed.id, claimed.model_dump(mode="json"))
    org.db.connection.commit()

    visible = inbox(org.db, "sparring-course")
    assert visible and visible[0].state == MessageState.NEW, "expired lease was not reclaimed"
    assert claim(org.db, message.id, "sparring-course").claim_owner == "sparring-course"


def test_only_the_claimant_can_complete(tmp_path: Path) -> None:
    org = Organization.init(tmp_path)
    message = send(org.db, "master-course", "sparring-course", "s", "b")
    claim(org.db, message.id, "sparring-course")
    with pytest.raises(Refusal, match="Only the claimant"):
        complete(org.db, message.id, "operator-course")
    assert complete(org.db, message.id, "sparring-course").state == MessageState.DONE


def test_retry_then_dead_letter(tmp_path: Path) -> None:
    org = Organization.init(tmp_path)
    message = send(org.db, "master-course", "sparring-course", "s", "b")
    for expected in (1, 2, 3):
        message = dead_letter(org.db, message)
        assert message.retry_count == expected
        assert message.state == MessageState.NEW
    message = dead_letter(org.db, message)
    assert message.state == MessageState.DEAD, "a message must stop retrying eventually"
    kinds = [row["kind"] for row in org.db.connection.execute("SELECT kind FROM events").fetchall()]
    assert "message.dead_lettered" in kinds


def test_an_invented_subagent_is_not_an_actor(tmp_path: Path) -> None:
    org = Organization.init(tmp_path)
    with pytest.raises(Refusal, match="Unknown actor"):
        org.actor("a-subagent-i-just-made-up")
