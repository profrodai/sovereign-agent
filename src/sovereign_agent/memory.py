"""Small, inspectable hybrid memory retrieval with provenance in every score."""

from __future__ import annotations

import json
import math
import re
from dataclasses import dataclass
from datetime import datetime

from sovereign_agent.database import Database
from sovereign_agent.ids import utc_now


def _words(text: str) -> set[str]:
    return set(re.findall(r"[a-z0-9]+", text.lower()))


def _cosine(left: tuple[float, ...], right: tuple[float, ...]) -> float:
    if len(left) != len(right):
        raise ValueError("query and memory embeddings must have equal dimensions")
    denominator = math.sqrt(sum(x * x for x in left)) * math.sqrt(sum(x * x for x in right))
    return (
        sum(x * y for x, y in zip(left, right, strict=True)) / denominator if denominator else 0.0
    )


@dataclass(frozen=True)
class MemoryHit:
    id: str
    content: str
    score: float
    lexical: float
    semantic: float
    recency: float
    importance: float
    visibility: str
    semantic_status: str


def remember(
    db: Database,
    memory_id: str,
    content: str,
    *,
    visibility: str = "public",
    importance: float = 0.5,
    embedding: tuple[float, ...] | None = None,
    created_at: datetime | None = None,
) -> None:
    if (
        not content
        or not 0 <= importance <= 1
        or (visibility != "public" and not visibility.startswith("actor:"))
    ):
        raise ValueError("memory content, visibility, or importance is invalid")
    with db.transaction():
        db.connection.execute(
            "INSERT INTO memories"
            "(id, content, embedding, visibility, importance, created_at) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (
                memory_id,
                content,
                json.dumps(embedding) if embedding is not None else None,
                visibility,
                importance,
                (created_at or utc_now()).isoformat(),
            ),
        )


def recall(
    db: Database,
    query: str,
    *,
    actor_id: str,
    query_embedding: tuple[float, ...] | None = None,
    limit: int = 5,
    now: datetime | None = None,
) -> tuple[MemoryHit, ...]:
    if not 1 <= limit <= 20:
        raise ValueError("recall limit must be between 1 and 20")
    query_words, instant = _words(query), now or utc_now()
    candidates: list[tuple[MemoryHit, tuple[float, ...], set[str]]] = []
    rows = db.connection.execute(
        "SELECT * FROM memories WHERE visibility = 'public' OR visibility = ?",
        (f"actor:{actor_id}",),
    ).fetchall()
    for row in rows:
        words = _words(str(row["content"]))
        lexical = len(query_words & words) / max(1, len(query_words | words))
        vector = tuple(json.loads(row["embedding"])) if row["embedding"] else ()
        semantic = (
            _cosine(query_embedding, vector) if query_embedding is not None and vector else 0.0
        )
        if lexical == 0 and semantic <= 0:
            continue
        age_days = max(
            0.0, (instant - datetime.fromisoformat(row["created_at"])).total_seconds() / 86400
        )
        recency = 1 / (1 + age_days / 30)
        importance = float(row["importance"])
        score = 0.35 * lexical + 0.35 * semantic + 0.15 * recency + 0.15 * importance
        hit = MemoryHit(
            str(row["id"]),
            str(row["content"]),
            score,
            lexical,
            semantic,
            recency,
            importance,
            str(row["visibility"]),
            "used" if query_embedding is not None and vector else "unavailable",
        )
        candidates.append((hit, vector, words))
    selected: list[tuple[MemoryHit, tuple[float, ...], set[str]]] = []
    while candidates and len(selected) < limit:

        def mmr(item: tuple[MemoryHit, tuple[float, ...], set[str]]) -> tuple[float, str]:
            diversity = 0.0
            for _, vector, words in selected:
                similarity = (
                    _cosine(item[1], vector)
                    if item[1] and vector
                    else len(item[2] & words) / max(1, len(item[2] | words))
                )
                diversity = max(diversity, similarity)
            return (0.75 * item[0].score - 0.25 * diversity, item[0].id)

        winner = max(candidates, key=mmr)
        selected.append(winner)
        candidates.remove(winner)
    return tuple(item[0] for item in selected)
