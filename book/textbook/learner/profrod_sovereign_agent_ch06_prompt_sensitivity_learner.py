# Prof Rod | Build Your Always-On AI Agent From Scratch
# Full book and learning materials: https://profrod.ai/book
# Join the Prof Rod learner community: https://profrod.ai/community
# Original source and updates: https://github.com/profrodai/sovereign-agent

"""Chapter 6 learner file: a prompt is one draw from a distribution of prompts.

A skill is instructions and examples placed in the model's context. Rewording the instructions
or reordering the examples can change the answers, so a single prompt's score is one sample from
a distribution over equally reasonable prompts. This file measures that distribution with the
standard library only: accuracy per prompt, the spread across prompts, the spread that case
sampling alone would produce, and how often every prompt agrees on a case. Chapter 6 applies
them to paraphrased and reordered prompts on a real model.
"""

from __future__ import annotations

import math
import re
from collections.abc import Sequence

LABELS = ("stock", "draft", "clarify", "refuse")
WORD = re.compile(r"[a-z]+")


def label_of(answer: str) -> str | None:
    """The first of the four labels to appear as a word in the answer, or None."""
    for word in WORD.findall(answer.lower()):
        if word in LABELS:
            return word
    return None


def accuracy(correct: Sequence[bool]) -> float:
    if not correct:
        raise ValueError("no cases")
    return sum(correct) / len(correct)


def spread(values: Sequence[float]) -> dict[str, float]:
    """Mean, sample standard deviation, minimum and maximum of per-prompt scores."""
    if len(values) < 2:
        raise ValueError("need at least two prompts")
    mean = sum(values) / len(values)
    sd = math.sqrt(sum((v - mean) ** 2 for v in values) / (len(values) - 1))
    return {"mean": mean, "sd": sd, "min": min(values), "max": max(values)}


def case_sampling_sd(p: float, cases: int) -> float:
    """How much one prompt's accuracy varies across fresh sets of `cases` cases: sqrt(p(1-p)/n)."""
    return math.sqrt(p * (1 - p) / cases)


def all_agree_share(matrix: Sequence[Sequence[bool]]) -> float:
    """Share of cases on which every prompt is right, or every prompt is wrong."""
    if not matrix or len({len(row) for row in matrix}) != 1:
        raise ValueError("need prompts scored on the same cases")
    columns = list(zip(*matrix, strict=True))
    return sum(len(set(column)) == 1 for column in columns) / len(columns)
