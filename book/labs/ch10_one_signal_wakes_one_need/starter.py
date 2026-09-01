"""Starter for Chapter 10's causal-binding lab."""

from pathlib import Path
from typing import Any

STUDENT_TODO = True
Graph = dict[str, Any]


def build_repaired_graph() -> Graph:
    """Return the intended outcome -> SOW -> execution -> effect graph."""
    # TODO(1): Model a historical low-stock signal and a healthy current observation.
    raise NotImplementedError


def validate_proof(graph: Graph) -> str:
    """Return ACCEPTED or one stable refusal category."""
    # TODO(2): Check every causal edge, not merely the final world condition.
    raise NotImplementedError


def exercise(root: Path) -> dict[str, object]:
    """Build attacks and a repaired proof graph, then report the verdicts."""
    # TODO(3): Mutate one edge per attack and persist the repaired graph below root.
    raise NotImplementedError(
        "Bind outcome, SOW, execution, effect, and subject; a true condition is not proof."
    )
