"""Resolve seat types to exactly one runtime instance address."""

from __future__ import annotations

from sovereign_agent.contracts.ids import SeatId, SeatInstanceId
from sovereign_agent.registry import SeatInstance, SeatRegistry
from sovereign_agent.relay.errors import RelayValidationError


class AmbiguousRecipient(RelayValidationError):
    """A seat type maps to zero or many instances."""


def resolve_recipient(
    registry: SeatRegistry,
    *,
    seat_instance: SeatInstanceId | str | None = None,
    seat_type: SeatId | str | None = None,
    authorize_create: bool = False,
) -> SeatInstance:
    del authorize_create  # v0.4 never spawns an instance implicitly
    if seat_instance is not None:
        return registry.get(seat_instance)
    if seat_type is None:
        raise AmbiguousRecipient("recipient requires a seat instance or a unique seat type")
    wanted = seat_type if isinstance(seat_type, SeatId) else SeatId(seat_type)
    matches = [item for item in registry.list() if item.seat_id == wanted]
    if len(matches) != 1:
        raise AmbiguousRecipient(
            f"seat type {wanted.value!r} resolves to {len(matches)} instances; "
            "delivery requires an explicit instance address"
        )
    return matches[0]
