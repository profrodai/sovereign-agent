"""Instructor reference; execute only in the submitted Unit A namespace."""

# ruff: noqa: F821
implementation_source = r'''
def restore(db: Database, source: Path) -> None:
    """Pause the active database, invalidate old holders, then copy a checked snapshot.

    Keep the same database inode: replacing the path would strand old connections
    on an independently writable database. SQLite backup replaces its contents
    under SQLite's locks. A process already admitted to the supplier may still
    complete remotely; restoring never claims to recall it.
    """
    if source.resolve() == db.path.resolve() or not source.is_file():
        raise ValueError("a separate existing backup is required")
    with sqlite3.connect(f"{source.resolve().as_uri()}?mode=ro", uri=True) as snapshot:
        if snapshot.execute("PRAGMA integrity_check").fetchone()[0] != "ok":
            raise ValueError("restore source is corrupt")
        versions = {row[0] for row in snapshot.execute("SELECT version FROM schema_migrations")}
        if versions != db.applied_versions():
            raise ValueError("restore requires the same schema version; migrate a copy first")
        # Prepare the restored image before disturbing active state.
        with tempfile.TemporaryDirectory(prefix="sovereign-restore-") as temporary:
            image = Path(temporary) / "restored.sqlite"
            epoch = uuid.uuid4().hex
            with sqlite3.connect(image) as prepared:
                snapshot.backup(prepared)
                prepared.execute(
                    "UPDATE assistant_control SET epoch=?,paused=1 WHERE id=1", (epoch,)
                )
                prepared.execute(
                    "UPDATE assistant_work SET generation=generation+1,owner=NULL,expires=NULL,"
                    "status=CASE WHEN status='RUNNING' THEN 'READY' ELSE status END"
                )
                # Old approvals can be reconciled, but cannot authorize a new send.
                prepared.execute("UPDATE assistant_orders SET revoked=1,approved_until=0")
                prepared.commit()
                with db.immediate() as connection:
                    connection.execute("UPDATE assistant_control SET paused=1 WHERE id=1")
                marker = db.path.with_suffix(".authority")
                replacement = marker.with_name(marker.name + "." + epoch)
                with replacement.open("x") as stream:
                    stream.write(epoch)
                    stream.flush()
                    os.fsync(stream.fileno())
                os.replace(replacement, marker)
                prepared.backup(db.connection)
'''
assert connect_build(implementation_source)["status"] == "PASS"
