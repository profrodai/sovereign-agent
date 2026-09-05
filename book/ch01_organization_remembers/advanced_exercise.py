"""Chapter 1 extension: inspect how retrieval policy selects durable memory."""

from __future__ import annotations

import argparse
import json
from datetime import UTC, datetime
from pathlib import Path

from sovereign_agent.memory import recall, remember
from sovereign_agent.organization import Organization

NOW = datetime(2026, 9, 5, tzinfo=UTC)


def explore_retrieval(root: Path) -> dict[str, object]:
    org = Organization(root)
    remember(org.db, "public", "Lucy needs vanilla inventory", embedding=(1.0, 0.0), created_at=NOW)
    remember(
        org.db,
        "alice-only",
        "Lucy's private vanilla supplier",
        visibility="actor:alice",
        importance=1.0,
        embedding=(1.0, 0.0),
        created_at=NOW,
    )
    remember(
        org.db,
        "bob-only",
        "Bob's private vanilla supplier",
        visibility="actor:bob",
        importance=1.0,
        embedding=(1.0, 0.0),
        created_at=NOW,
    )
    remember(org.db, "unrelated", "chocolate freezer manual", importance=1.0, created_at=NOW)

    hits = recall(
        org.db,
        "vanilla inventory",
        actor_id="alice",
        query_embedding=(1.0, 0.0),
        now=NOW,
    )
    return {
        "visible_ids": [hit.id for hit in hits],
        "bob_row_reached_ranker": any(hit.id == "bob-only" for hit in hits),
        "unrelated_row_returned": any(hit.id == "unrelated" for hit in hits),
        "score_evidence": [
            {
                "id": hit.id,
                "lexical": round(hit.lexical, 3),
                "semantic": round(hit.semantic, 3),
                "recency": round(hit.recency, 3),
                "importance": hit.importance,
                "semantic_status": hit.semantic_status,
            }
            for hit in hits
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    print(json.dumps(explore_retrieval(parser.parse_args().root), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
