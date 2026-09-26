# Prof Rod | Build Your Always-On AI Agent From Scratch
# Full book and learning materials: https://profrod.ai/book
# Join the Prof Rod learner community: https://profrod.ai/community
# Original source and updates: https://github.com/profrodai/sovereign-agent

"""Chapter 16 learner file: what happens when you optimize against an evaluation.

Choosing the best of many candidates on a noisy score picks lucky candidates as well as good ones,
so the winner's score overstates it: the winner's curse. Preferences between pairs of answers are
the other half of improving a model, and the Bradley-Terry model turns them into a score per
answer. This file builds, with the standard library only: the expected maximum of k standard
normal draws, a simulation of the winner's curse, the Bradley-Terry win probability, its log
likelihood, and a maximum-likelihood fit by gradient ascent. Chapter 16 derives each and measures
the winner's curse on a real prompt search.
"""

from __future__ import annotations

import math
import random
from collections.abc import Sequence
from statistics import NormalDist

STANDARD = NormalDist()


def expected_max_normal(k: int, grid: int = 4000) -> float:
    """E[max of k independent standard normals] = integral of x k phi(x) Phi(x)^(k-1) dx."""
    if k < 1:
        raise ValueError("k must be at least 1")
    low, high = -8.0, 8.0
    step = (high - low) / grid
    total = 0.0
    for i in range(grid + 1):
        x = low + i * step
        weight = 0.5 if i in (0, grid) else 1.0
        total += weight * x * k * STANDARD.pdf(x) * STANDARD.cdf(x) ** (k - 1)
    return total * step


def winners_curse(true_rates: Sequence[float], cases: int, trials: int, seed: int) -> dict:
    """Score every candidate on `cases` pass/fail cases, pick the best, and record how its
    measured score compares with its true rate, over many repetitions."""
    rng = random.Random(seed)
    measured, truth = [], []
    for _ in range(trials):
        scores = [sum(rng.random() < p for _ in range(cases)) / cases for p in true_rates]
        best = max(range(len(scores)), key=lambda i: (scores[i], -i))
        measured.append(scores[best])
        truth.append(true_rates[best])
    return {
        "selected_measured": sum(measured) / trials,
        "selected_true": sum(truth) / trials,
        "optimism": (sum(measured) - sum(truth)) / trials,
    }


def bradley_terry(r_i: float, r_j: float) -> float:
    """P(i is preferred to j) = e^r_i / (e^r_i + e^r_j) = sigmoid(r_i - r_j)."""
    return 1 / (1 + math.exp(-(r_i - r_j)))


def log_likelihood(comparisons: Sequence[tuple[int, int]], ratings: Sequence[float]) -> float:
    """Sum of log P(winner preferred to loser) over (winner, loser) pairs."""
    return sum(math.log(bradley_terry(ratings[w], ratings[loser])) for w, loser in comparisons)


def fit_bradley_terry(
    comparisons: Sequence[tuple[int, int]], items: int, steps: int = 2000, rate: float = 0.5
) -> list[float]:
    """Maximum-likelihood ratings by gradient ascent, centered to mean zero.

    The gradient of the log likelihood for item i is its wins minus its expected wins:
    sum over comparisons involving i of (1[i won] - P(i wins)). Only rating differences are
    identified, so the ratings are re-centered after every step.
    """
    ratings = [0.0] * items
    n = len(comparisons)
    if n == 0:
        raise ValueError("no comparisons")
    for _ in range(steps):
        gradient = [0.0] * items
        for w, loser in comparisons:
            p = bradley_terry(ratings[w], ratings[loser])
            gradient[w] += 1 - p
            gradient[loser] -= 1 - p
        ratings = [r + rate * g / n * items for r, g in zip(ratings, gradient, strict=True)]
        mean = sum(ratings) / items
        ratings = [r - mean for r in ratings]
    return ratings
