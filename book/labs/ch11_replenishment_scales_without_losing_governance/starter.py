"""Starter for Chapter 11's transactional restock lab."""

from pathlib import Path

STUDENT_TODO = True


class Restock:
    """Exact identity of one requested replenishment effect."""

    def __init__(
        self,
        effect_key: str,
        assignment_id: str,
        signal_id: str,
        sku: str,
        quantity: int,
        unit_cost_cents: int,
    ) -> None:
        self.effect_key = effect_key
        self.assignment_id = assignment_id
        self.signal_id = signal_id
        self.sku = sku
        self.quantity = quantity
        self.unit_cost_cents = unit_cost_cents


def initialize(db_path: Path) -> None:
    """Create inventory, cash, authority, and effect-key tables."""
    # TODO(1): Add constraints and seed one authorized tea assignment.
    raise NotImplementedError


def apply_restock(db_path: Path, request: Restock, *, fault: str | None = None) -> str:
    """Apply once or return replay for an exact durable identity."""
    # TODO(2): Put authority, replay, inventory, cash, and effect writes in one transaction.
    raise NotImplementedError


def exercise(root: Path) -> dict[str, object]:
    """Apply one authorized effect exactly once and prove rollback safety."""
    # TODO(3): Demonstrate exact replay, unauthorized refusal, and injected rollback.
    raise NotImplementedError(
        "Use a durable effect key, exact request identity, and one SQLite transaction."
    )
