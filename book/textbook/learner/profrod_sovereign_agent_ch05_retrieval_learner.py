# Prof Rod | Build Your Always-On AI Agent From Scratch
# Full book and learning materials: https://profrod.ai/book
# Join the Prof Rod learner community: https://profrod.ai/community
# Original source and updates: https://github.com/profrodai/sovereign-agent

"""Chapter 5 learner file: choosing what the model sees, built from scratch.

A model sees only its context window, and every token in it costs time, memory and money. So an
agent with a long memory must choose which records to send. This file builds that choice with the
standard library only: tokenizing for search, the BM25 ranking function, cosine similarity for
vector retrieval, the ranking metrics precision@k, recall@k and reciprocal rank, and a context
packer that fills a token budget in order of score. Chapter 5 derives each one and measures
retrieval against sending everything to a real model.
"""

from __future__ import annotations

import math
import re
from collections import Counter
from collections.abc import Callable, Sequence

WORD = re.compile(r"[a-z0-9]+")


def terms(text: str) -> list[str]:
    """Lowercase words and numbers: the units a lexical search matches on."""
    return WORD.findall(text.lower())


def bm25_scores(
    query: str, documents: Sequence[str], k1: float = 1.5, b: float = 0.75
) -> list[float]:
    """Okapi BM25: for each query term, idf times a saturating, length-normalized term frequency.

    idf(t) = ln(1 + (N - n_t + 0.5) / (n_t + 0.5)) rewards rare terms. A term's frequency f
    contributes f (k1 + 1) / (f + k1 (1 - b + b |d| / avgdl)), which rises with f but levels
    off at k1 + 1, and which a longer-than-average document must earn with more occurrences.
    """
    tokenized = [terms(d) for d in documents]
    if not tokenized:
        return []
    average = sum(len(t) for t in tokenized) / len(tokenized) or 1.0
    containing = Counter(term for t in tokenized for term in set(t))
    count = len(tokenized)
    scores = []
    for tokens in tokenized:
        frequency = Counter(tokens)
        score = 0.0
        for term in set(terms(query)):
            f = frequency[term]
            if not f:
                continue
            idf = math.log(1 + (count - containing[term] + 0.5) / (containing[term] + 0.5))
            norm = k1 * (1 - b + b * len(tokens) / average)
            score += idf * f * (k1 + 1) / (f + norm)
        scores.append(score)
    return scores


def cosine(a: Sequence[float], b: Sequence[float]) -> float:
    """Cosine of the angle between two vectors: their dot product over the product of lengths."""
    dot = sum(x * y for x, y in zip(a, b, strict=True))
    norms = math.sqrt(sum(x * x for x in a)) * math.sqrt(sum(y * y for y in b))
    if norms == 0:
        raise ValueError("cosine is undefined for a zero vector")
    return dot / norms


def ranking(scores: Sequence[float]) -> list[int]:
    """Indices from highest to lowest score; ties keep their original order."""
    return sorted(range(len(scores)), key=lambda i: -scores[i])


def precision_at_k(ranked: Sequence[int], relevant: set[int], k: int) -> float:
    """Share of the top k results that are relevant."""
    return sum(i in relevant for i in ranked[:k]) / k


def recall_at_k(ranked: Sequence[int], relevant: set[int], k: int) -> float:
    """Share of the relevant records that appear in the top k."""
    if not relevant:
        raise ValueError("recall needs at least one relevant record")
    return sum(i in relevant for i in ranked[:k]) / len(relevant)


def reciprocal_rank(ranked: Sequence[int], relevant: set[int]) -> float:
    """1 / the rank of the first relevant result, or 0 when none is returned."""
    for position, index in enumerate(ranked, start=1):
        if index in relevant:
            return 1 / position
    return 0.0


def pack_context(
    records: Sequence[str],
    scores: Sequence[float],
    budget: int,
    count_tokens: Callable[[str], int],
) -> list[int]:
    """Choose records in order of score while they fit the token budget; skip any that do not."""
    chosen, used = [], 0
    for index in ranking(scores):
        cost = count_tokens(records[index])
        if used + cost <= budget:
            chosen.append(index)
            used += cost
    return chosen
