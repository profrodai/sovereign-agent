"""Append-only business and control-plane events."""

from __future__ import annotations

import json
from datetime import datetime
from typing import Any

from sovereign_agent.database import Database
from sovereign_agent.ids import new_id, utc_now
from sovereign_agent.models import EventRecord


def append_event(db: Database, kind: str, payload: dict[str, Any]) -> EventRecord:
    """Insert one event. Callers must already be inside a transaction for business mutations."""
    record = EventRecord(id=new_id("evt"), kind=kind, payload=payload, created_at=utc_now())
    db.connection.execute(
        "INSERT INTO events(id, kind, payload, created_at) VALUES (?, ?, ?, ?)",
        (record.id, record.kind, json.dumps(payload, default=str), record.created_at.isoformat()),
    )
    seq = db.connection.execute("SELECT seq FROM events WHERE id = ?", (record.id,)).fetchone()[
        "seq"
    ]
    return record.model_copy(update={"seq": int(seq)})


def replay(db: Database) -> list[EventRecord]:
    rows = db.connection.execute(
        "SELECT seq, id, kind, payload, created_at FROM events ORDER BY seq"
    ).fetchall()
    return [
        EventRecord(
            seq=int(row["seq"]),
            id=row["id"],
            kind=row["kind"],
            payload=json.loads(row["payload"]),
            created_at=datetime.fromisoformat(row["created_at"]),
        )
        for row in rows
    ]
