# Prof Rod | Build Your Always-On AI Agent From Scratch
# Full book and learning materials: https://profrod.ai/book
# Join the Prof Rod learner community: https://profrod.ai/community
# Original source and updates: https://github.com/profrodai/sovereign-agent

"""Chapter 6 learner file: embeddings and vector search, from scratch.

A word's index says nothing about its meaning; a learned vector can. This file builds, with the
standard library only, one-hot vectors and the embedding lookup, word vectors trained with
skip-gram and negative sampling, one normalized vector per text, exact nearest-neighbor search,
reciprocal rank fusion of two rankings, the ranking metrics, and a navigable small-world graph that
finds near neighbors while counting how many vectors it compared. Chapter 6 derives each and
measures them on a real embedding model.
"""

from __future__ import annotations

import heapq
import math
import random
from collections.abc import Sequence

STOP = {"a", "an", "the", "is", "and", "in", "on", "for", "of", "from", "to", "at", "by", "with"}


def tokenize(text: str) -> list[str]:
    """Lowercase words; a hyphen stays inside a word (dairy-free); stop words are dropped."""
    words = "".join(c if c.isalpha() or c == "-" else " " for c in text.lower()).split()
    return [w for w in words if w not in STOP]


def one_hot(word: str, vocab: Sequence[str]) -> list[int]:
    """A vector with a 1 in the word's position and 0 everywhere else."""
    if word not in vocab:
        raise ValueError(f"unknown word: {word!r}")
    return [1 if w == word else 0 for w in vocab]


def matvec(matrix: Sequence[Sequence[float]], vector: Sequence[float]) -> list[float]:
    """A matrix (a list of rows) times a column vector."""
    if any(len(row) != len(vector) for row in matrix):
        raise ValueError("shape mismatch")
    return [sum(m * v for m, v in zip(row, vector, strict=True)) for row in matrix]


def dot(a: Sequence[float], b: Sequence[float]) -> float:
    if len(a) != len(b):
        raise ValueError("dimension mismatch")
    return sum(x * y for x, y in zip(a, b, strict=True))


def norm(v: Sequence[float]) -> float:
    return math.sqrt(dot(v, v))


def normalize(v: Sequence[float]) -> list[float]:
    n = norm(v)
    if n == 0:
        raise ValueError("cannot normalize a zero vector")
    return [x / n for x in v]


def cosine(a: Sequence[float], b: Sequence[float]) -> float:
    """The cosine of the angle between two vectors: their dot product over both lengths."""
    return dot(a, b) / (norm(a) * norm(b))


def squared_distance(a: Sequence[float], b: Sequence[float]) -> float:
    """Squared Euclidean distance. For unit vectors it equals 2 - 2 * cosine."""
    return sum((x - y) ** 2 for x, y in zip(a, b, strict=True))


def training_pairs(texts: Sequence[str], window: int = 2) -> list[tuple[str, str]]:
    """(center, context) pairs: words that appear within `window` of each other in one text."""
    pairs = []
    for text in texts:
        words = tokenize(text)
        for i, center in enumerate(words):
            for j in range(max(0, i - window), min(len(words), i + window + 1)):
                if j != i:
                    pairs.append((center, words[j]))
    return pairs


def train_word_vectors(
    texts: Sequence[str],
    dim: int = 8,
    window: int = 2,
    negatives: int = 3,
    epochs: int = 60,
    rate: float = 0.05,
    seed: int = 7,
) -> tuple[dict[str, list[float]], list[float]]:
    """Skip-gram with negative sampling. Each word owns an embedding and a context vector. For a
    real (center, neighbor) pair, the sigmoid of the center's embedding dotted with the neighbor's
    context vector is pushed toward 1; for randomly drawn words, toward 0. Returns the embeddings
    and the mean loss per pair after each epoch."""
    chooser = random.Random(seed)
    vocab = sorted({w for text in texts for w in tokenize(text)})
    embedding = {w: [chooser.uniform(-0.5, 0.5) for _ in range(dim)] for w in vocab}
    contexts = {w: [0.0] * dim for w in vocab}
    pairs = training_pairs(texts, window)
    losses = []
    for _ in range(epochs):
        chooser.shuffle(pairs)
        total = 0.0
        for center, neighbor in pairs:
            samples = [(neighbor, 1)] + [(chooser.choice(vocab), 0) for _ in range(negatives)]
            grad = [0.0] * dim
            for word, label in samples:
                if label == 0 and word == neighbor:
                    continue
                p = 1 / (1 + math.exp(-dot(embedding[center], contexts[word])))
                total += -math.log(p if label else 1 - p)
                g = p - label  # the loss's derivative with respect to the score
                for k in range(dim):
                    grad[k] += g * contexts[word][k]
                    contexts[word][k] -= rate * g * embedding[center][k]
            for k in range(dim):
                embedding[center][k] -= rate * grad[k]
        losses.append(total / len(pairs))
    return embedding, losses


def text_vector(text: str, table: dict[str, Sequence[float]]) -> list[float]:
    """One vector per text: the mean of its known word vectors, normalized to length one."""
    words = [w for w in tokenize(text) if w in table]
    if not words:
        raise ValueError(f"no known words in {text!r}")
    dim = len(next(iter(table.values())))
    mean = [sum(table[w][k] for w in words) / len(words) for k in range(dim)]
    return normalize(mean)


def exact_search(vectors: Sequence[Sequence[float]], query: Sequence[float], k: int) -> list[int]:
    """Indexes of the k vectors most similar to the query by dot product (cosine, if normalized):
    one comparison per stored vector."""
    scores = [dot(v, query) for v in vectors]
    return sorted(range(len(vectors)), key=lambda i: (-scores[i], i))[:k]


def reciprocal_rank_fusion(rankings: Sequence[Sequence[int]], k: int = 60) -> list[int]:
    """Combine rankings: each item scores the sum of 1 / (k + rank) over the rankings that list it,
    with ranks starting at 1. Items are returned best first."""
    score: dict[int, float] = {}
    for ranking in rankings:
        for rank, item in enumerate(ranking, start=1):
            score[item] = score.get(item, 0.0) + 1 / (k + rank)
    return sorted(score, key=lambda item: (-score[item], item))


def recall_at_k(ranking: Sequence[int], relevant: set[int], k: int) -> float:
    """Share of the relevant items that appear in the first k."""
    return len(set(ranking[:k]) & relevant) / len(relevant)


def reciprocal_rank(ranking: Sequence[int], relevant: set[int]) -> float:
    """1 / rank of the first relevant item, or 0 when none is ranked."""
    for rank, item in enumerate(ranking, start=1):
        if item in relevant:
            return 1 / rank
    return 0.0


def small_world_graph(vectors: Sequence[Sequence[float]], links: int = 8) -> list[list[int]]:
    """A navigable small-world graph: insert vectors one at a time and link each new one to its
    `links` nearest already-inserted neighbors, in both directions. Built exactly, for teaching.
    """
    graph: list[list[int]] = [[] for _ in vectors]
    for i in range(1, len(vectors)):
        nearest = sorted(range(i), key=lambda j: -dot(vectors[i], vectors[j]))[:links]
        for j in nearest:
            graph[i].append(j)
            graph[j].append(i)
    return graph


def graph_search(
    vectors: Sequence[Sequence[float]],
    graph: Sequence[Sequence[int]],
    query: Sequence[float],
    k: int,
    ef: int,
    entry: int = 0,
) -> tuple[list[int], int]:
    """Best-first search from `entry`: keep the `ef` best vectors seen, expand the closest
    unexpanded one, stop when none of them can improve. Returns the top k and how many vectors
    were compared with the query."""
    seen = {entry}
    compared = 1
    start = dot(vectors[entry], query)
    frontier = [(-start, entry)]  # most similar first
    best = [(start, entry)]  # a min-heap of the ef most similar
    while frontier:
        negative, node = heapq.heappop(frontier)
        if len(best) >= ef and -negative < best[0][0]:
            break
        for neighbor in graph[node]:
            if neighbor in seen:
                continue
            seen.add(neighbor)
            compared += 1
            score = dot(vectors[neighbor], query)
            if len(best) < ef or score > best[0][0]:
                heapq.heappush(frontier, (-score, neighbor))
                heapq.heappush(best, (score, neighbor))
                if len(best) > ef:
                    heapq.heappop(best)
    ranked = sorted(best, key=lambda pair: (-pair[0], pair[1]))
    return [node for _, node in ranked[:k]], compared


def index_bytes(count: int, dimensions: int, bytes_per_number: int = 4) -> int:
    """Memory for the raw vectors of an index: count * dimensions * bytes per number."""
    return count * dimensions * bytes_per_number
