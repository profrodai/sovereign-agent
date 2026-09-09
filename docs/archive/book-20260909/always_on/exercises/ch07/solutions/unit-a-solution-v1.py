"""Instructor reference; execute only in the submitted Unit A namespace."""

# ruff: noqa: F821
implementation_source = r"""
def tick(db: Database, *, now: float | None = None, maximum: int = 100) -> list[str]:
    now = time.time() if now is None else now
    if not math.isfinite(now) or type(maximum) is not int or not 1 <= maximum <= 1000:
        raise ValueError("invalid scheduler pass")
    created = []
    with db.immediate() as connection:
        if connection.execute("SELECT paused FROM assistant_control WHERE id=1").fetchone()[0]:
            return []
        rows = connection.execute(
            "SELECT * FROM assistant_jobs WHERE enabled=1 AND next_due<=? "
            "ORDER BY next_due,id LIMIT ?",
            (now, maximum),
        ).fetchall()
        for row in rows:
            try:
                identifier = _enqueue(
                    connection,
                    f"job:{row['id']}:{row['next_due']!r}",
                    row["session"],
                    row["prompt"],
                    now,
                    row["channel"],
                    row["recipient"],
                    require_admission=True,
                )
            except IntakeLimitError:
                if not row["deferred"]:
                    append_event(db, "assistant.job.deferred", {"job": row["id"]})
                    connection.execute(
                        "UPDATE assistant_jobs SET deferred=1 WHERE id=?", (row["id"],)
                    )
                continue
            created.append(identifier)
            skipped = math.floor((now - row["next_due"]) / row["interval_seconds"])
            next_due = row["next_due"] + (skipped + 1) * row["interval_seconds"]
            connection.execute(
                "UPDATE assistant_jobs SET next_due=?,deferred=0 WHERE id=?", (next_due, row["id"])
            )
            append_event(
                db,
                "assistant.job.enqueued",
                {"job": row["id"], "work": identifier, "coalesced": skipped},
            )
    return created
"""
assert connect_build(implementation_source)["status"] == "PASS"
