"""Reference solution for Chapter 5: authority is a current fenced lease."""

from __future__ import annotations

import shutil
import sqlite3
from pathlib import Path

STUDENT_TODO = False


def _fresh(path: Path) -> None:
    if path.exists():
        shutil.rmtree(path)
    path.mkdir(parents=True)


def _mint(connection: sqlite3.Connection) -> int:
    cursor = connection.execute("INSERT INTO tokens DEFAULT VALUES")
    assert cursor.lastrowid is not None
    return int(cursor.lastrowid)


def _claim(connection: sqlite3.Connection, actor: str, now: int) -> tuple[bool, int]:
    row = connection.execute(
        "SELECT state, owner, expires_at, token FROM messages WHERE id = 'msg-1'"
    ).fetchone()
    assert row is not None
    state, owner, expires_at, current_token = row
    if state == "CLAIMED" and owner == actor and expires_at > now:
        return True, int(current_token)
    token = _mint(connection)
    cursor = connection.execute(
        "UPDATE messages SET state='CLAIMED', owner=?, expires_at=?, token=? "
        "WHERE id='msg-1' AND (state='NEW' OR (state='CLAIMED' AND expires_at<=?))",
        (actor, now + 10, token, now),
    )
    if cursor.rowcount != 1:
        connection.rollback()
        return False, token
    connection.commit()
    return True, token


def _complete(connection: sqlite3.Connection, actor: str, token: int) -> bool:
    cursor = connection.execute(
        "UPDATE messages SET state='DONE' "
        "WHERE id='msg-1' AND state='CLAIMED' AND owner=? AND token=?",
        (actor, token),
    )
    connection.commit()
    return cursor.rowcount == 1


def exercise(root: Path) -> dict[str, object]:
    lab = root / "ch05"
    _fresh(lab)
    connection = sqlite3.connect(lab / "mailbox.db")
    connection.executescript(
        "CREATE TABLE tokens(id INTEGER PRIMARY KEY AUTOINCREMENT);"
        "CREATE TABLE messages(id TEXT PRIMARY KEY, state TEXT NOT NULL, owner TEXT, "
        "expires_at INTEGER, token INTEGER);"
        "INSERT INTO messages VALUES('msg-1', 'NEW', NULL, NULL, NULL);"
    )

    # Naive interleaving: both decisions are made from the same pre-write fact.
    first_read = connection.execute("SELECT state FROM messages WHERE id='msg-1'").fetchone()[0]
    second_read = connection.execute("SELECT state FROM messages WHERE id='msg-1'").fetchone()[0]
    naive_winners = int(first_read == "NEW") + int(second_read == "NEW")

    won_a, token_a = _claim(connection, "actor-a", now=0)
    won_b, _unused = _claim(connection, "actor-b", now=0)
    retry_won, retry_token = _claim(connection, "actor-a", now=1)
    takeover_won, token_b = _claim(connection, "actor-b", now=11)
    stale_completed = _complete(connection, "actor-a", token_a)
    current_completed = _complete(connection, "actor-b", token_b)
    final_state = connection.execute("SELECT state FROM messages WHERE id='msg-1'").fetchone()[0]
    connection.close()

    return {
        "naive_winners": naive_winners,
        "cas_winners_before_expiry": int(won_a) + int(won_b),
        "unexpired_retry_same_token": retry_won and retry_token == token_a,
        "expired_takeover_won": takeover_won,
        "token_increased": token_b > token_a,
        "stale_completion_accepted": stale_completed,
        "current_completion_accepted": current_completed,
        "final_state": final_state,
    }
