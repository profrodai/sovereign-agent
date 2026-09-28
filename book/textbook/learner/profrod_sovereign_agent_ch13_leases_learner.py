# Prof Rod | Build Your Always-On AI Agent From Scratch
# Full book and learning materials: https://profrod.ai/book
# Join the Prof Rod learner community: https://profrod.ai/community
# Original source and updates: https://github.com/profrodai/sovereign-agent

"""Chapter 13 learner file: leases, the slow-or-dead question, and fencing.

A replacement worker cannot tell whether the previous holder died or is only slow. A lease turns
that question into a time limit: after it expires, another worker may take over. This file
computes, with the standard library only, how often a lease expires under a holder that is still
working, how long a crash goes undetected, the shortest lease that keeps false expiry below a
target, and the fencing rule that refuses writes from a superseded holder. Chapter 13 derives
each and measures them.
"""

from __future__ import annotations

import math
from collections.abc import Sequence


def percentile(values: Sequence[float], q: float) -> float:
    """Nearest-rank percentile: the smallest value with at least q percent of values at or below."""
    ordered = sorted(values)
    return ordered[max(1, math.ceil(q / 100 * len(ordered))) - 1]


def false_expiry_share(turn_seconds: Sequence[float], lease: float) -> float:
    """Share of turns that outlive a lease taken at their start: P(turn > lease). Each one is a
    holder that is still working when another worker may take its work."""
    return sum(seconds > lease for seconds in turn_seconds) / len(turn_seconds)


def shortest_lease(turn_seconds: Sequence[float], target: float) -> float:
    """The shortest observed turn length whose false-expiry share is at most `target`."""
    for lease in sorted(turn_seconds):
        if false_expiry_share(turn_seconds, lease) <= target:
            return lease
    raise ValueError("no observed lease meets the target")


def detection_delay(lease: float, turn: float, scan_interval: float) -> float:
    """Mean time from a crash to a replacement claim, when the lease starts with the turn, the
    crash falls uniformly within a turn of length `turn`, and replacements look for expired work
    every `scan_interval` seconds: lease - turn / 2 + scan_interval / 2."""
    if not 0 <= turn <= lease or scan_interval < 0:
        raise ValueError("need 0 <= turn <= lease and a nonnegative scan interval")
    return lease - turn / 2 + scan_interval / 2


def fenced(writer_generation: int, current_generation: int) -> bool:
    """A write is admitted only from the current holder: its generation equals the record's."""
    return writer_generation == current_generation
