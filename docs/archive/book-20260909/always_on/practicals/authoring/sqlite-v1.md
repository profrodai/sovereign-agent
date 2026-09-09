### SQLite from the first row to an atomic change

A dictionary disappears when its process ends. A database can retain records so a later process
can resume from evidence. **SQLite** is an embedded database: Python's `sqlite3` library opens
a local database file without starting a separate database server. **SQL** is the language used
to define, select and change its records. A **table** has named columns and rows. A **primary
key** identifies a row; a **query** asks for rows satisfying a condition.

Start with a deliberately small preference table. Read the SQL as instructions: create the
table, insert one named value, then select the value for one session. `?` is a parameter
placeholder; the values are passed separately so they are data, not SQL instructions.
`fetchone()` returns one row or `None`; it does not guarantee that a matching row exists.

```python tags=["foundation", "worked-example"]
import sqlite3
from pathlib import Path
from tempfile import TemporaryDirectory

with TemporaryDirectory() as intro_sql_folder:
    intro_db_path = Path(intro_sql_folder) / "example.sqlite"
    intro_db = sqlite3.connect(intro_db_path, autocommit=True)
    intro_db.execute("CREATE TABLE preference (id INTEGER PRIMARY KEY, session TEXT, value TEXT)")
    intro_db.execute("INSERT INTO preference (session,value) VALUES (?,?)", ("lucy", "09:00"))
    intro_row = intro_db.execute(
        "SELECT value FROM preference WHERE session=?", ("lucy",)
    ).fetchone()
    print("Matching row:", intro_row)
    assert intro_row == ("09:00",)
    assert (
        intro_db.execute(
            "SELECT value FROM preference WHERE session=?", ("another-session",)
        ).fetchone()
        is None
    )
    intro_db.close()
    intro_reopen = sqlite3.connect(intro_db_path, autocommit=True)
    assert intro_reopen.execute("SELECT count(*) FROM preference").fetchone()[0] == 1
    intro_reopen.close()
print("The row survived closing and reopening its connection.")
```

Index `[0]` selects the first column of a returned tuple. `sqlite3.Row` is an alternative row
factory that also permits named-column access. `dict(row)` then produces an ordinary dictionary.
The book's `Database` wrapper supplies that configuration and its schema; the wrapper is course
code, while `sqlite3` is the standard library. You will use the public connection and transaction
methods explained at the exercise boundary, rather than needing to reconstruct the wrapper.

Now consider a budget. Moving five pence from reserved to spent requires two values to change
together. A **transaction** makes a group of local changes commit together or roll back together.
The example explicitly controls SQL transactions with `autocommit=True` and SQL statements.
`BEGIN IMMEDIATE` starts a write transaction; `COMMIT` keeps its changes; `ROLLBACK` discards them.
Predict the row after the deliberately raised exception. Catching an error alone would not undo
the first update; the rollback is the operation that restores the prior state.

```python tags=["foundation", "worked-example"]
intro_ledger = sqlite3.connect(":memory:", autocommit=True)
intro_ledger.execute(
    "CREATE TABLE budget (id INTEGER PRIMARY KEY, reserved INTEGER, spent INTEGER)"
)
intro_ledger.execute("INSERT INTO budget VALUES (1,5,0)")
intro_ledger.execute("BEGIN IMMEDIATE")
try:
    intro_ledger.execute("UPDATE budget SET reserved=0 WHERE id=1")
    raise ValueError("injected failure before the matching spend update")
except ValueError:
    intro_ledger.execute("ROLLBACK")
assert intro_ledger.execute("SELECT reserved,spent FROM budget").fetchone() == (5, 0)
intro_ledger.execute("BEGIN IMMEDIATE")
intro_ledger.execute("UPDATE budget SET reserved=0,spent=5 WHERE id=1")
intro_ledger.execute("COMMIT")
print(
    "After a complete change:", intro_ledger.execute("SELECT reserved,spent FROM budget").fetchone()
)
intro_ledger.close()
```

The literal `:memory:` creates a temporary database inside this connection; it is useful for the
small experiment, but the earlier file example establishes persistence. Neither example proves
that a remote supplier rolls back when the local transaction rolls back. An external operation
has its own state and evidence.

**SQL you will meet later.** `UPDATE ... SET ... WHERE ...` changes selected rows. `AND` combines
conditions. `ORDER BY` makes an ordering explicit; absent that clause, do not rely on row order.
`count(*)` counts rows; `sum(amount)` totals a column and can be `NULL` on an empty input;
`coalesce(sum(amount),0)` uses zero for that empty aggregate. A `UNIQUE` constraint rejects
duplicate identities. `GROUP BY status` computes one aggregate per status.

An **invariant** is a condition that must remain true across operations, such as nonnegative
reserved money. A **snapshot** is a consistent view at one point; two separate reads can describe
different moments unless their transaction contract binds them. In the book, `with db.immediate()`
groups related writes. It is a course-defined context manager with the commit/rollback purpose
you just observed. Do not assume that an arbitrary `with connection` has identical behavior under
every SQLite autocommit setting.

**Your prediction:** two workers both read ten remaining pence outside a transaction and each
approve seven. Why can both believe the next order fits? Explain what must be checked together
with the write. Then change the example's initial reserved amount and repeat the failure.
Reference: Python's [SQLite tutorial and transaction control](https://docs.python.org/3.14/library/sqlite3.html).
