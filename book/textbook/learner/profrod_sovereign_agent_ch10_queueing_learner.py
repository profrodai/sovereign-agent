# Prof Rod | Build Your Always-On AI Agent From Scratch
# Full book and learning materials: https://profrod.ai/book
# Join the Prof Rod learner community: https://profrod.ai/community
# Original source and updates: https://github.com/profrodai/sovereign-agent

"""Chapter 10 learner file: how long work waits when events arrive at random.

Stock events and schedules put work on a queue that one worker empties. This file computes, with
the standard library only, the worker's utilization, the mean wait before a job starts
(Pollaczek-Khinchine, and the exponential special case), the highest arrival rate that keeps the
mean wait under a target, random arrival times, and the extra delay a periodic rescan adds.
Chapter 10 derives each and measures them on a local model.
"""

from __future__ import annotations

import random
from collections.abc import Sequence


def moments(service_seconds: Sequence[float]) -> tuple[float, float]:
    """The mean service time E[S] and its second moment E[S^2]."""
    n = len(service_seconds)
    return sum(service_seconds) / n, sum(s * s for s in service_seconds) / n


def utilization(arrival_rate: float, mean_service: float) -> float:
    """The share of time the worker is busy: rho = lambda * E[S]."""
    return arrival_rate * mean_service


def pk_wait(arrival_rate: float, mean_service: float, second_moment: float) -> float:
    """Pollaczek-Khinchine: the mean wait in the queue before service, for random (Poisson)
    arrivals and any service-time distribution, W = lambda * E[S^2] / (2 * (1 - rho))."""
    rho = utilization(arrival_rate, mean_service)
    if not 0 <= rho < 1:
        raise ValueError("the queue grows without bound unless rho < 1")
    return arrival_rate * second_moment / (2 * (1 - rho))


def exponential_wait(arrival_rate: float, mean_service: float) -> float:
    """The same wait when service times are exponential (E[S^2] = 2 E[S]^2):
    rho * E[S] / (1 - rho)."""
    return pk_wait(arrival_rate, mean_service, 2 * mean_service**2)


def highest_rate(target_wait: float, mean_service: float, second_moment: float) -> float:
    """The largest arrival rate whose Pollaczek-Khinchine wait is at most `target_wait`:
    solve W = lambda * m2 / (2 * (1 - lambda * m1)) for lambda."""
    return 2 * target_wait / (second_moment + 2 * target_wait * mean_service)


def arrivals(rate: float, count: int, seed: int) -> list[float]:
    """Arrival times of a Poisson process: independent exponential gaps with mean 1 / rate."""
    chooser, now, times = random.Random(seed), 0.0, []
    for _ in range(count):
        now += chooser.expovariate(rate)
        times.append(now)
    return times


def rescan_delay(period: float) -> float:
    """Mean extra delay before a periodic scan notices an event that arrives at a random moment."""
    return period / 2
