# Prof Rod | Build Your Always-On AI Agent From Scratch
# Full book and learning materials: https://profrod.ai/book
# Join the Prof Rod learner community: https://profrod.ai/community
# Original source and updates: https://github.com/profrodai/sovereign-agent

"""Chapter 18 learner file: when a second agent pays, in arithmetic.

Delegating to other agents promises speed from parallel work and accuracy from independent
answers. Both promises have conditions. This file computes them with the standard library only:
Amdahl's law for the speedup of partly parallel work, the success of a task that needs every
subagent to be right, the accuracy of a majority vote over independent answers, and how many
tokens a delegation sends compared with one agent doing the work. Chapter 18 derives each and
measures them on a local model.
"""

from __future__ import annotations

import math
from collections.abc import Sequence


def amdahl_speedup(parallel_fraction: float, workers: int) -> float:
    """Speedup when a fraction f of the work splits across n workers: 1 / ((1 - f) + f / n)."""
    if not 0 <= parallel_fraction <= 1 or workers < 1:
        raise ValueError("need 0 <= f <= 1 and at least one worker")
    return 1 / ((1 - parallel_fraction) + parallel_fraction / workers)


def all_correct(accuracies: Sequence[float]) -> float:
    """Chance that every one of several independent subtasks is right: the product."""
    return math.prod(accuracies)


def majority_accuracy(p: float, voters: int) -> float:
    """Chance that more than half of `voters` independent answers, each right with p, are right."""
    if voters < 1 or voters % 2 == 0:
        raise ValueError("use an odd number of voters, so there are no ties")
    return sum(
        math.comb(voters, k) * p**k * (1 - p) ** (voters - k)
        for k in range(voters // 2 + 1, voters + 1)
    )


def delegation_tokens(shared: int, own: Sequence[int], coordinator: int) -> dict[str, int]:
    """Input tokens when each of several subagents is sent the shared context plus its own part,
    and a coordinator reads their results, against one agent reading everything once."""
    delegated = sum(shared + part for part in own) + coordinator
    single = shared + sum(own)
    return {"delegated": delegated, "single": single}
