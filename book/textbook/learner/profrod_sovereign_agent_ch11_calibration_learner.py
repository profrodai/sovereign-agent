# Prof Rod | Build Your Always-On AI Agent From Scratch
# Full book and learning materials: https://profrod.ai/book
# Join the Prof Rod learner community: https://profrod.ai/community
# Original source and updates: https://github.com/profrodai/sovereign-agent

"""Chapter 11 learner file: when may the agent spend without asking?

Automatic approval is a bet that the proposal is right. This file computes, with the standard
library only, the reorder quantity the shop's rule requires, the calibration error of a model's
confidence, what an auto-approval threshold covers and how often what it covers is wrong, a
confidence taken from agreement between samples, and the threshold at which approving
automatically costs less than asking Lucy. Chapter 11 derives each and measures them.
"""

from __future__ import annotations

import math
from collections import Counter
from collections.abc import Sequence


def reorder_quantity(on_hand: int, daily: int, days: int, case: int = 1) -> int:
    """Tubs to order: enough to sell `daily` a day for `days` days, less what is on hand, in whole
    cases, and never a negative amount."""
    needed = daily * days - on_hand
    return max(0, math.ceil(needed / case) * case)


def calibration_error(
    confidences: Sequence[float], correct: Sequence[bool], bins: int = 10
) -> float:
    """Expected calibration error: sort answers into confidence bins, and average the gap between
    each bin's accuracy and its mean confidence, weighted by the bin's share of answers."""
    groups: dict[int, list[int]] = {}
    for i, confidence in enumerate(confidences):
        groups.setdefault(min(int(confidence * bins), bins - 1), []).append(i)
    total = 0.0
    for members in groups.values():
        accuracy = sum(correct[i] for i in members) / len(members)
        mean = sum(confidences[i] for i in members) / len(members)
        total += len(members) / len(confidences) * abs(accuracy - mean)
    return total


def auto_approval(
    confidences: Sequence[float], correct: Sequence[bool], threshold: float
) -> tuple[float, float | None]:
    """Approve automatically when confidence is at least the threshold. Return the share approved
    automatically, and the share of those that were wrong (None when none were approved)."""
    approved = [
        ok for confidence, ok in zip(confidences, correct, strict=True) if confidence >= threshold
    ]
    coverage = len(approved) / len(confidences)
    return coverage, (sum(not ok for ok in approved) / len(approved) if approved else None)


def agreement(answers: Sequence[object]) -> tuple[object, float]:
    """The most common of several sampled answers, and the share of samples that gave it."""
    answer, count = Counter(answers).most_common(1)[0]
    return answer, count / len(answers)


def approval_threshold(loss_cents: float, review_cents: float) -> float:
    """Approving automatically costs P(wrong) * loss; asking costs the review. With a calibrated
    confidence c, P(wrong) = 1 - c, so approve automatically when c > 1 - review / loss."""
    if loss_cents <= 0 or review_cents < 0:
        raise ValueError("need a positive loss and a nonnegative review cost")
    return max(0.0, 1 - review_cents / loss_cents)
