"""Multi-host session fencing and restart-durable delivery attempts."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import NoReturn

from sovereign_agent.database import Database
from sovereign_agent.errors import Refusal
from sovereign_agent.ids import utc_now


@dataclass(frozen=True)
class SessionClaim:
    session_id: str
    host_id: str
    incarnation: int
    expires_at: datetime


def register_host(
    db: Database, host_id: str, *, now: datetime | None = None, ttl_seconds: int = 60
) -> None:
    expires = (now or utc_now()) + timedelta(seconds=ttl_seconds)
    with db.transaction():
        db.connection.execute(
            "INSERT INTO host_instances(id, lease_expires_at) VALUES (?, ?) "
            "ON CONFLICT(id) DO UPDATE SET lease_expires_at = excluded.lease_expires_at",
            (host_id, expires.isoformat()),
        )


def claim_session(
    db: Database,
    session_id: str,
    host_id: str,
    *,
    now: datetime | None = None,
    ttl_seconds: int = 60,
) -> SessionClaim:
    instant = now or utc_now()
    expires = instant + timedelta(seconds=ttl_seconds)
    with db.immediate() as connection:
        host = connection.execute(
            "SELECT lease_expires_at FROM host_instances WHERE id = ?", (host_id,)
        ).fetchone()
        if host is None or datetime.fromisoformat(host["lease_expires_at"]) <= instant:
            _refuse("host lease is absent or expired")
        current = connection.execute(
            "SELECT * FROM session_claims WHERE session_id = ?", (session_id,)
        ).fetchone()
        if (
            current
            and current["host_id"] != host_id
            and datetime.fromisoformat(current["lease_expires_at"]) > instant
        ):
            _refuse(f"live claim belongs to {current['host_id']}")
        incarnation = 1 if current is None else int(current["incarnation"])
        if current is not None and (
            current["host_id"] != host_id
            or datetime.fromisoformat(current["lease_expires_at"]) <= instant
        ):
            incarnation += 1
        connection.execute(
            "INSERT INTO session_claims"
            "(session_id, host_id, incarnation, lease_expires_at) VALUES (?, ?, ?, ?) "
            "ON CONFLICT(session_id) DO UPDATE SET host_id=excluded.host_id, "
            "incarnation=excluded.incarnation, lease_expires_at=excluded.lease_expires_at",
            (session_id, host_id, incarnation, expires.isoformat()),
        )
    return SessionClaim(session_id, host_id, incarnation, expires)


def finish_session(
    db: Database, claim: SessionClaim, result: str, *, now: datetime | None = None
) -> None:
    instant = now or utc_now()
    with db.immediate() as connection:
        current = connection.execute(
            "SELECT * FROM session_claims WHERE session_id = ?", (claim.session_id,)
        ).fetchone()
        host = connection.execute(
            "SELECT lease_expires_at FROM host_instances WHERE id = ?", (claim.host_id,)
        ).fetchone()
        if (
            current is None
            or host is None
            or current["host_id"] != claim.host_id
            or int(current["incarnation"]) != claim.incarnation
            or datetime.fromisoformat(current["lease_expires_at"]) <= instant
            or datetime.fromisoformat(host["lease_expires_at"]) <= instant
        ):
            _refuse("completion came from a stale or expired session incarnation")
        connection.execute(
            "INSERT INTO session_completions"
            "(session_id, host_id, incarnation, result, created_at) "
            "VALUES (?, ?, ?, ?, ?)",
            (claim.session_id, claim.host_id, claim.incarnation, result, utc_now().isoformat()),
        )


def record_delivery_failure(
    db: Database, delivery_id: str, error: str, process_after: datetime
) -> int:
    with db.transaction():
        db.connection.execute(
            "INSERT INTO delivery_attempts"
            "(delivery_id, attempt_count, status, process_after, last_error) "
            "VALUES (?, 1, 'RETRY', ?, ?) ON CONFLICT(delivery_id) DO UPDATE SET "
            "attempt_count=attempt_count+1, status='RETRY', "
            "process_after=excluded.process_after, last_error=excluded.last_error",
            (delivery_id, process_after.isoformat(), error),
        )
    row = db.connection.execute(
        "SELECT attempt_count FROM delivery_attempts WHERE delivery_id = ?", (delivery_id,)
    ).fetchone()
    return int(row["attempt_count"])


def _refuse(reason: str) -> NoReturn:
    raise Refusal(
        "Session claim refused.",
        reason,
        "Inspect host_instances and session_claims in organization.db.",
        "Renew the host lease or wait for the current claim to expire.",
        category="session_claim_refusal",
    )
