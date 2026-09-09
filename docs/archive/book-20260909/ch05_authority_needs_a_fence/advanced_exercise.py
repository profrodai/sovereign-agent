"""Chapter 5 extension: prove that a session incarnation fences an old host."""

from __future__ import annotations

import argparse
import json
from datetime import UTC, datetime, timedelta
from pathlib import Path

from sovereign_agent.coordination import claim_session, finish_session, register_host
from sovereign_agent.errors import Refusal
from sovereign_agent.organization import Organization

NOW = datetime(2026, 9, 5, tzinfo=UTC)


def explore_incarnations(root: Path) -> dict[str, object]:
    org = Organization(root)
    register_host(org.db, "kiosk-a", now=NOW, ttl_seconds=10)
    first = claim_session(org.db, "supplier-chat", "kiosk-a", now=NOW, ttl_seconds=10)
    register_host(org.db, "kiosk-b", now=NOW + timedelta(seconds=20), ttl_seconds=60)
    second = claim_session(
        org.db,
        "supplier-chat",
        "kiosk-b",
        now=NOW + timedelta(seconds=20),
        ttl_seconds=60,
    )
    try:
        finish_session(org.db, first, "stale order")
        stale_finish = "ALLOWED (this would be a bug)"
    except Refusal:
        stale_finish = "REFUSED"
    finish_session(org.db, second, "current order", now=NOW + timedelta(seconds=20))
    committed = org.db.connection.execute(
        "SELECT host_id, incarnation, result FROM session_completions"
    ).fetchone()
    return {
        "incarnations": [first.incarnation, second.incarnation],
        "stale_finish": stale_finish,
        "committed": dict(committed),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    print(json.dumps(explore_incarnations(parser.parse_args().root), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
