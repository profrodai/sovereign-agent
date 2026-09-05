"""Chapter 7 extension: observe a durable watcher without confusing it with Pulse."""

from __future__ import annotations

import argparse
import json
from datetime import UTC, datetime, timedelta
from pathlib import Path

from sovereign_agent.automation import WatchDecision, create_automation, run_due
from sovereign_agent.organization import Organization

NOW = datetime(2026, 9, 5, tzinfo=UTC)


def explore_automation(root: Path) -> dict[str, object]:
    org = Organization(root)
    create_automation(
        org.db,
        "freezer-temperature",
        interval_seconds=60,
        payload="inspect freezer",
        first_run_at=NOW,
    )
    calls: list[dict[str, str]] = []
    quiet = run_due(
        org.db,
        "freezer-temperature",
        lambda state: WatchDecision(
            False, "temperature healthy", {"checks": state.get("checks", 0) + 1}
        ),
        lambda run_id, message: calls.append({"run_id": run_id, "message": message}),
        now=NOW,
    )
    fired = run_due(
        org.db,
        "freezer-temperature",
        lambda state: WatchDecision(True, "temperature high", {**state, "alarm": True}),
        lambda run_id, message: calls.append({"run_id": run_id, "message": message}),
        now=NOW + timedelta(seconds=60),
    )
    row = org.db.connection.execute(
        "SELECT condition_state, failure_count FROM automations WHERE id = 'freezer-temperature'"
    ).fetchone()
    run_count = org.db.connection.execute("SELECT COUNT(*) FROM automation_runs").fetchone()[0]
    return {
        "statuses": [quiet.status, fired.status],
        "run_rows": run_count,
        "payload_calls": len(calls),
        "payload_received_durable_run_id": calls[0]["run_id"] == fired.run_id,
        "condition_state": json.loads(row["condition_state"]),
        "failure_count": row["failure_count"],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    print(json.dumps(explore_automation(parser.parse_args().root), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
