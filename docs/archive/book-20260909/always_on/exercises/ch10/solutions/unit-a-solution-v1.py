"""Instructor reference; execute only in the submitted Unit A namespace."""

# ruff: noqa: F821
implementation_source = r"""
def assert_current(connection: sqlite3.Connection, work: Claim, now: float | None = None) -> None:
    now = time.time() if now is None else now
    control = connection.execute("SELECT epoch,paused FROM assistant_control WHERE id=1").fetchone()
    location = connection.execute("PRAGMA database_list").fetchone()[2]
    try:
        current_epoch = Path(location).with_suffix(".authority").read_text()
    except OSError:
        raise PermissionError("authority marker is unavailable") from None
    if (
        not control
        or control["paused"]
        or current_epoch != control["epoch"]
        or work.epoch != current_epoch
    ):
        raise PermissionError("runtime paused or replaced by restore")
    row = connection.execute(
        "SELECT 1 FROM assistant_work WHERE id=? AND owner=? AND generation=? "
        "AND status='RUNNING' AND expires>? AND subject=? AND role=? AND session=? AND prompt=?",
        (
            work.id,
            work.owner,
            work.generation,
            now,
            work.subject,
            work.role,
            work.session,
            work.prompt,
        ),
    ).fetchone()
    if row is None:
        raise PermissionError("worker claim expired or superseded")
    if work.role == "research":
        contract = connection.execute(
            "SELECT d.deadline,p.cancelled FROM assistant_delegations d "
            "JOIN assistant_work p ON p.id=d.parent_id WHERE d.work_id=?",
            (work.id,),
        ).fetchone()
        if contract is None or contract["deadline"] <= now or contract["cancelled"]:
            raise PermissionError("delegation expired or parent cancelled")
"""
assert connect_build(implementation_source)["status"] == "PASS"
