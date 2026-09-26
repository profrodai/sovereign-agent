# Prof Rod | Build Your Always-On AI Agent From Scratch
# Full book and learning materials: https://profrod.ai/book
# Join the Prof Rod learner community: https://profrod.ai/community
# Original source and updates: https://github.com/profrodai/sovereign-agent

"""Chapter 15 learner file: the statistics of an evaluation, built from scratch.

An evaluation score is an estimate from a sample of cases, so it needs an error bar, and two
candidates run on the same cases need a paired comparison. This file builds, with the standard
library only: binomial intervals (Wald and Wilson) and their exact coverage; a standard error that
respects repeated attempts at the same case; McNemar's exact paired test; the number of cases a
comparison needs; the unbiased pass@k estimator; and Cohen's kappa for agreement between graders.
Chapter 15 derives each formula and applies it to the chapter's own retained evaluation runs.
"""

from __future__ import annotations

import math
from collections import Counter
from collections.abc import Sequence
from statistics import NormalDist

Z95 = NormalDist().inv_cdf(0.975)  # 1.959963...: the two-sided 95% normal quantile.


def binomial_pmf(k: int, n: int, p: float) -> float:
    """P(exactly k successes in n independent trials, each succeeding with probability p)."""
    return math.comb(n, k) * p**k * (1 - p) ** (n - k)


def wald_interval(successes: int, trials: int, z: float = Z95) -> tuple[float, float]:
    """p-hat plus or minus z standard errors, with the standard error estimated at p-hat."""
    phat = successes / trials
    half = z * math.sqrt(phat * (1 - phat) / trials)
    return (max(0.0, phat - half), min(1.0, phat + half))


def wilson_interval(successes: int, trials: int, z: float = Z95) -> tuple[float, float]:
    """Every p for which p-hat lies within z standard errors of p, the error computed at p.

    Squaring |p-hat - p| <= z sqrt(p (1 - p) / n) gives a quadratic in p; its two roots are the
    interval. Unlike Wald, it never collapses to a point at 0 or n successes.
    """
    phat = successes / trials
    denominator = 1 + z * z / trials
    center = (phat + z * z / (2 * trials)) / denominator
    half = z * math.sqrt(phat * (1 - phat) / trials + z * z / (4 * trials * trials)) / denominator
    return (max(0.0, center - half), min(1.0, center + half))


def coverage(interval, p: float, trials: int, z: float = Z95) -> float:
    """Exact probability that `interval` contains the true p: sum over every possible outcome."""
    total = 0.0
    for successes in range(trials + 1):
        low, high = interval(successes, trials, z)
        if low <= p <= high:
            total += binomial_pmf(successes, trials, p)
    return total


def clustered_standard_error(groups: Sequence[Sequence[bool]]) -> float:
    """Standard error of the mean score when each case was attempted the same number of times.

    Attempts at one case are not independent; the case is the unit that was sampled. With equal
    attempts per case, the overall score is the mean of the case means, so its standard error is
    the standard deviation of the case means divided by the square root of the number of cases.
    """
    sizes = {len(group) for group in groups}
    if len(groups) < 2 or len(sizes) != 1 or 0 in sizes:
        raise ValueError("need at least two cases with the same, nonzero number of attempts")
    means = [sum(group) / len(group) for group in groups]
    grand = sum(means) / len(means)
    variance = sum((m - grand) ** 2 for m in means) / (len(means) - 1)
    return math.sqrt(variance / len(means))


def paired_counts(first: Sequence[bool], second: Sequence[bool]) -> dict[str, int]:
    """Cross-tabulate two candidates' results on the same attempts, in the same order."""
    if len(first) != len(second):
        raise ValueError("paired results need the same attempts in the same order")
    pairs = Counter(zip(first, second, strict=True))
    return {
        "both": pairs[(True, True)],
        "only_first": pairs[(True, False)],
        "only_second": pairs[(False, True)],
        "neither": pairs[(False, False)],
    }


def mcnemar_exact(only_first: int, only_second: int) -> float:
    """Two-sided exact p-value for 'both candidates are equally good' from the discordant pairs.

    Pairs where both pass or both fail say nothing about which is better. Under the null
    hypothesis, each of the b + c discordant pairs favors either candidate with probability 1/2,
    so the smaller count is Binomial(b + c, 1/2).
    """
    discordant = only_first + only_second
    if discordant == 0:
        return 1.0
    tail = sum(math.comb(discordant, i) for i in range(min(only_first, only_second) + 1))
    return min(1.0, 2 * tail / 2**discordant)


def cases_needed(p_first: float, p_second: float, alpha=0.05, power=0.8) -> int:
    """Cases per candidate to detect p_first vs p_second with independent samples."""
    z_alpha, z_beta = NormalDist().inv_cdf(1 - alpha / 2), NormalDist().inv_cdf(power)
    mean = (p_first + p_second) / 2
    spread = z_alpha * math.sqrt(2 * mean * (1 - mean)) + z_beta * math.sqrt(
        p_first * (1 - p_first) + p_second * (1 - p_second)
    )
    return math.ceil((spread / (p_first - p_second)) ** 2)


def paired_cases_needed(discordant: float, difference: float, alpha=0.05, power=0.8) -> int:
    """Cases to detect a difference in pass rate when both candidates run on the same cases.

    `discordant` is the expected share of cases on which the candidates disagree; `difference`
    is the difference in pass rates. Only discordant cases carry information, so a pair of similar
    candidates (few disagreements) needs far fewer cases than two independent samples.
    """
    if not 0 < abs(difference) <= discordant <= 1:
        raise ValueError("need 0 < |difference| <= discordant share <= 1")
    z_alpha, z_beta = NormalDist().inv_cdf(1 - alpha / 2), NormalDist().inv_cdf(power)
    spread = z_alpha * math.sqrt(discordant) + z_beta * math.sqrt(discordant - difference**2)
    return math.ceil((spread / difference) ** 2)


def pass_at_k(samples: int, correct: int, k: int) -> float:
    """Unbiased estimate of P(at least one of k fresh samples is correct), from n samples.

    Of the C(n, k) ways to choose k of the n samples, C(n - c, k) contain no correct one.
    """
    if not 0 <= correct <= samples or not 1 <= k <= samples:
        raise ValueError("need 0 <= correct <= samples and 1 <= k <= samples")
    return 1 - math.comb(samples - correct, k) / math.comb(samples, k)


def naive_pass_at_k(samples: int, correct: int, k: int) -> float:
    """The plug-in estimate 1 - (1 - c/n) ** k. Because (1 - x) ** k is convex, it is biased
    downward: on average it underestimates pass@k (Jensen's inequality)."""
    return 1 - (1 - correct / samples) ** k


def cohen_kappa(first: Sequence, second: Sequence) -> float:
    """Agreement between two graders beyond what their label frequencies give by chance."""
    if len(first) != len(second) or not first:
        raise ValueError("need two nonempty label lists of the same length")
    n = len(first)
    observed = sum(a == b for a, b in zip(first, second, strict=True)) / n
    first_counts, second_counts = Counter(first), Counter(second)
    chance = sum(first_counts[label] * second_counts[label] for label in first_counts) / n**2
    if chance == 1:
        raise ValueError("both graders used one identical label; kappa is undefined")
    return (observed - chance) / (1 - chance)
