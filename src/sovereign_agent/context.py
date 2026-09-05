"""Recoverable context compaction that never rewrites source transcript bytes."""

from __future__ import annotations

import sqlite3
from collections.abc import Callable
from dataclasses import dataclass

from sovereign_agent.database import Database
from sovereign_agent.ids import new_id, utc_now

Summarizer = Callable[[str, tuple["ContextItem", ...]], str]


@dataclass(frozen=True)
class ContextItem:
    seq: int
    role: str
    content: str
    derived: bool = False


def append_message(db: Database, session_id: str, role: str, content: str) -> int:
    if role not in {"system", "user", "assistant", "tool"} or not content:
        raise ValueError("role must be known and content non-empty")
    with db.immediate() as connection:
        seq = int(
            connection.execute(
                "SELECT COALESCE(MAX(seq), 0) + 1 FROM transcript_messages WHERE session_id = ?",
                (session_id,),
            ).fetchone()[0]
        )
        connection.execute(
            "INSERT INTO transcript_messages"
            "(session_id, seq, role, content, created_at) VALUES (?, ?, ?, ?, ?)",
            (session_id, seq, role, content, utc_now().isoformat()),
        )
    return seq


def compact_one(
    db: Database,
    session_id: str,
    summarizer: Summarizer,
    *,
    protect_head: int = 2,
    protect_tail: int = 2,
) -> bool:
    rows = db.connection.execute(
        "SELECT seq, role, content FROM transcript_messages WHERE session_id = ? ORDER BY seq",
        (session_id,),
    ).fetchall()
    prior = db.connection.execute(
        "SELECT through_seq, summary FROM context_compactions "
        "WHERE session_id = ? ORDER BY through_seq DESC LIMIT 1",
        (session_id,),
    ).fetchone()
    cursor, summary = (int(prior["through_seq"]), str(prior["summary"])) if prior else (0, "")
    eligible = rows[protect_head : max(protect_head, len(rows) - protect_tail)]
    start = next(
        (
            i
            for i, row in enumerate(eligible)
            if row["seq"] > cursor and row["role"] in {"assistant", "tool"}
        ),
        None,
    )
    if start is None:
        return False
    exchange_rows: list[sqlite3.Row] = []
    for row in eligible[start:]:
        if exchange_rows and row["role"] not in {"assistant", "tool"}:
            break
        if row["role"] in {"assistant", "tool"}:
            exchange_rows.append(row)
    exchange = tuple(
        ContextItem(int(row["seq"]), str(row["role"]), str(row["content"])) for row in exchange_rows
    )
    updated = summarizer(summary, exchange).strip()
    if not updated:
        return False
    through = exchange[-1].seq
    try:
        with db.transaction():
            db.connection.execute(
                "INSERT INTO context_compactions"
                "(id, session_id, through_seq, summary, created_at) VALUES (?, ?, ?, ?, ?)",
                (new_id("compact"), session_id, through, updated, utc_now().isoformat()),
            )
    except sqlite3.IntegrityError as error:
        if "context_compactions.session_id, context_compactions.through_seq" in str(error):
            return False
        raise
    return True


def render_context(
    db: Database, session_id: str, *, protect_head: int = 2, protect_tail: int = 2
) -> tuple[ContextItem, ...]:
    rows = db.connection.execute(
        "SELECT seq, role, content FROM transcript_messages WHERE session_id = ? ORDER BY seq",
        (session_id,),
    ).fetchall()
    prior = db.connection.execute(
        "SELECT through_seq, summary FROM context_compactions "
        "WHERE session_id = ? ORDER BY through_seq DESC LIMIT 1",
        (session_id,),
    ).fetchone()
    if prior is None:
        return tuple(
            ContextItem(int(row["seq"]), str(row["role"]), str(row["content"])) for row in rows
        )
    cursor = int(prior["through_seq"])
    head = {int(row["seq"]) for row in rows[:protect_head]}
    tail = {int(row["seq"]) for row in rows[-protect_tail:]}
    kept = [ContextItem(cursor, "assistant", str(prior["summary"]), True)]
    for row in rows:
        seq, role = int(row["seq"]), str(row["role"])
        if seq in head or seq in tail or role in {"system", "user"} or seq > cursor:
            kept.append(ContextItem(seq, role, str(row["content"])))
    return tuple(sorted(kept, key=lambda item: (item.seq, not item.derived)))
