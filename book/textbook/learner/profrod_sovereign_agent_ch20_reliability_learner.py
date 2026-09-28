# Prof Rod | Build Your Always-On AI Agent From Scratch
# Full book and learning materials: https://profrod.ai/book
# Join the Prof Rod learner community: https://profrod.ai/community
# Original source and updates: https://github.com/profrodai/sovereign-agent

"""Chapter 20 learner file: how reliable is a whole day, and how complete is its report?

A day of work succeeds only if every step does, and a report is complete only if it includes
every fact Lucy must act on. This file computes, with the standard library only, the success of a
series of independent steps, the per-step reliability a daily target demands, the Wilson interval
for a measured rate, and the facts a narrated report includes. Chapter 20 derives each and
measures them on local models.
"""

from __future__ import annotations

import math
import re
from collections.abc import Sequence


def series_success(step_success: Sequence[float]) -> float:
    """A day that needs every step to succeed, with independent steps, succeeds with the product."""
    return math.prod(step_success)


def per_step_needed(day_target: float, steps: int) -> float:
    """The success each of `steps` equal, independent steps needs for the day to reach the target:
    the steps-th root of the target."""
    return day_target ** (1 / steps)


def wilson_interval(successes: int, trials: int, z: float = 1.96) -> tuple[float, float]:
    """The Wilson score interval for a success rate (Chapter 16)."""
    if trials == 0:
        return 0.0, 1.0
    p = successes / trials
    center = (p + z * z / (2 * trials)) / (1 + z * z / trials)
    half = (
        z * math.sqrt(p * (1 - p) / trials + z * z / (4 * trials * trials)) / (1 + z * z / trials)
    )
    return max(0.0, center - half), min(1.0, center + half)


def dollars(cents: int) -> str:
    """How a report should state an amount: $26.00 for 2600 cents."""
    return f"${cents // 100:,}.{cents % 100:02d}"


def states_amount(report: str, cents: int) -> bool:
    """Whether the report states this exact amount, as $26.00, $26 or 26.00 dollars."""
    whole, part = divmod(cents, 100)
    forms = [rf"\$\s?{whole:,}\.{part:02d}\b", rf"\b{whole}\.{part:02d}\s*(?:dollars|USD)"]
    if part == 0:
        forms.append(rf"\$\s?{whole:,}(?![\d.,])")
    return any(re.search(form, report) for form in forms)


def names(report: str, word: str) -> bool:
    """Whether the report names this word, as a whole word, ignoring case."""
    return re.search(rf"\b{re.escape(word)}\b", report, re.IGNORECASE) is not None
