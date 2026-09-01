# Chapter 1 — The organization remembers

Lucy's shop lost an order once. Not a big one — a single case of cones — but the
supplier's system had recorded the sale, charged her, and then, somewhere between
a crashed browser tab and a reload, forgotten it existed. The money was gone and
the cones never came, and there was no record to point at. "We ordered them" was
a hope, not a fact.

A Zero-Employee Organization cannot afford that. If it is going to act on Lucy's
behalf — move money, commit to suppliers, promise a full freezer — then its
memory has to be the kind you can hold it to. So before we teach the organization
to *decide* anything, we have to answer a plainer question: **where does the
truth live, and what survives when the power goes out mid-sentence?**

This chapter is hands-on the whole way through. You will open the organization's
memory, try to corrupt it three different ways, watch a half-finished purchase
roll itself back, and learn to name — for any piece of data in the system — which
file or table is the authority for it.

## Learning objective

Understand where a Zero-Employee Organization keeps its memory, why some of that
memory is allowed to change and some is not, and what a transaction actually
buys you.

By the end you should be able to say, for any piece of data in this system,
**which file or table is the authority for it** — and defend the answer.

## Why memory is the first hard problem

An organization that forgets cannot be held to anything. If an order can vanish
because a process died halfway through — exactly what happened to Lucy's cones —
then "we ordered it" is a hope, not a fact.

So the first question is not "how does the AI decide" — it is "where does the
truth live, and what happens when the power goes out mid-sentence".

## Build it yourself: memory that cannot half-happen

Before you inspect the production database, build the core of it from scratch, so
that when you see the real thing you recognize every piece. Everything below runs
in a throwaway in-memory SQLite database — paste it into a Python shell.

Start with the smallest schema that can hold a shop's operational truth: what is
on the shelf, every movement of money, and a log of what happened.

```python
import sqlite3

db = sqlite3.connect(":memory:")
db.executescript("""
    CREATE TABLE inventory (
        sku TEXT PRIMARY KEY,
        on_hand INTEGER NOT NULL,
        reorder_point INTEGER NOT NULL
    );
    CREATE TABLE cash_entries (id INTEGER PRIMARY KEY, amount_cents INTEGER NOT NULL);
    CREATE TABLE events (seq INTEGER PRIMARY KEY, kind TEXT NOT NULL);
""")
db.execute("INSERT INTO inventory VALUES ('SKU-VANILLA', 4, 3)")
db.execute("INSERT INTO cash_entries(amount_cents) VALUES (10000)")  # opening balance
db.commit()
```

Notice the shape of `cash_entries`: it is a **ledger of signed movements**, not a
single balance field. The balance is `SUM(amount_cents)`. Nothing ever overwrites
a number, so no bug can silently lose money — the worst a mistake can do is add a
wrong row, which you can see and correct, never erase a right one.

Now the append-only guarantee for the event log, enforced by the *database*, not
by Python remembering to be careful:

```python
db.executescript("""
    CREATE TRIGGER events_no_update BEFORE UPDATE ON events
    BEGIN SELECT RAISE(ABORT, 'events are append-only: update refused'); END;
    CREATE TRIGGER events_no_delete BEFORE DELETE ON events
    BEGIN SELECT RAISE(ABORT, 'events are append-only: delete refused'); END;
""")
db.execute("INSERT INTO events(kind) VALUES ('sale.committed')")
db.commit()

try:
    db.execute("UPDATE events SET kind = 'NOTHING_HAPPENED'")
except sqlite3.IntegrityError as error:
    print("refused:", error)
```

```text
refused: events are append-only: update refused
```

A rule in application code protects you from your own bugs. A rule in the database
protects you from *everything that can reach the database* — including you, at 2am,
with a shell open. That is why the guard lives here.

### The three-write transaction, and what a rollback buys you

A restock has to change three things together: inventory goes up, cash goes down,
and an event records it. If only some of those land, the organization is lying to
itself — a full shelf with no money spent, or money spent with no stock. The tool
that makes "all or nothing" real is a transaction.

```python
def restock(db, sku, units, unit_cost):
    with db:  # commits at the end, or rolls the whole block back on any exception
        db.execute("UPDATE inventory SET on_hand = on_hand + ? WHERE sku = ?", (units, sku))
        db.execute("INSERT INTO cash_entries(amount_cents) VALUES (?)", (-units * unit_cost,))
        db.execute("INSERT INTO events(kind) VALUES ('replenishment.committed')")


def state(db):
    on_hand = db.execute("SELECT on_hand FROM inventory WHERE sku = 'SKU-VANILLA'").fetchone()[0]
    balance = db.execute("SELECT SUM(amount_cents) FROM cash_entries").fetchone()[0]
    return f"on_hand={on_hand} balance={balance}"


print("before:", state(db))
restock(db, "SKU-VANILLA", 6, 250)
print("after: ", state(db))
```

```text
before: on_hand=4 balance=10000
after:  on_hand=10 balance=8500
```

Now break it. Inject a failure *after* inventory and cash have already been
written but *before* the event — the exact "power cut mid-sentence" case — and
watch all three writes disappear together:

```python
def restock_but_crash(db, sku, units, unit_cost):
    with db:
        db.execute("UPDATE inventory SET on_hand = on_hand + ? WHERE sku = ?", (units, sku))
        db.execute("INSERT INTO cash_entries(amount_cents) VALUES (?)", (-units * unit_cost,))
        raise RuntimeError("power cut before the event was written")


print("before:", state(db))
try:
    restock_but_crash(db, "SKU-VANILLA", 6, 250)
except RuntimeError as error:
    print("failed:", error)
print("after: ", state(db))
```

```text
before: on_hand=10 balance=8500
failed: power cut before the event was written
after:  on_hand=10 balance=8500
```

`before` and `after` are identical. The inventory write had already happened, and
the rollback took it back. Either all three changes commit or none do — there is
no in-between state for the shop to be caught in.

### One honest limit: SQLite durability, not magic

The transaction guarantees *atomicity* — all-or-nothing — and, on commit,
*durability* to the extent SQLite provides it (WAL mode, an `fsync` at commit). Be
precise about what that does and does not promise: it protects the **database**.
It cannot make a write to the database and a write to a separate file happen in
one transaction — those are two systems, and a crash between them can leave them
disagreeing. The production organization keeps its canonical truth in SQLite for
exactly this reason, and treats files it writes outside the database as
projections that can always be regenerated. Chapter 2 makes that boundary sharp.

## Exercise 1: look at the operational state

```bash
sovereign-agent demo store --mode simulated --root /tmp/lucy-memory
sqlite3 /tmp/lucy-memory/.sovereign/organization.db ".tables"
```

Expected: sixteen tables listed. The ones to care about now:

| Table | Holds |
| --- | --- |
| `inventory` | how much stock exists, and the reorder point |
| `cash_entries` | every movement of money, as signed amounts |
| `events` | an append-only history of what happened |
| `signals` | durable "something needs attention" facts |
| `schema_migrations` | which schema versions have been applied |

```bash
sqlite3 -header -column /tmp/lucy-memory/.sovereign/organization.db \
  "SELECT * FROM inventory; SELECT id, amount_cents FROM cash_entries;"
```

Cash is a **ledger of movements**, not a single balance field. The balance is
`SUM(amount_cents)`: `10000` opening, `+800` from the sale, `-720` for the
purchase. Nothing overwrites a balance, so nothing can quietly lose money.

## Exercise 2: prove the events are append-only

The event log is the organization's memory of what it did. Try to rewrite it.

```bash
sqlite3 /tmp/lucy-memory/.sovereign/organization.db \
  "UPDATE events SET kind='NOTHING_HAPPENED' WHERE kind='sale.committed';"
```

Expected:

```text
Error: stepping, events are append-only: update refused (19)
```

Now try deleting:

```bash
sqlite3 /tmp/lucy-memory/.sovereign/organization.db \
  "DELETE FROM events WHERE kind='replenishment.committed';"
```

Also refused. Now try the sneaky third variant — overwriting a row instead of
editing it:

```bash
sqlite3 /tmp/lucy-memory/.sovereign/organization.db \
  "INSERT OR REPLACE INTO events(id,kind,payload,created_at)
   SELECT id,'NOTHING_HAPPENED',payload,created_at FROM events LIMIT 1;"
```

Also refused: `events are append-only: replace refused`.

All three are enforced by **database triggers**, not by Python being careful.
That distinction matters: a rule enforced in application code protects you from
bugs, but a rule enforced in the database protects you from *everything else
that can reach the database* — including you, at 2am, with a REPL open.

That third case is worth dwelling on, because it is where a subtle mistake
hides. A tempting way to block the overwrite is a SQLite setting like
`recursive_triggers`, switched on when the application opens the database. It
works — *from the application*. But from the `sqlite3` command line above, the
one this chapter just told you to use, the overwrite would succeed silently and
the row count would not change. A guarantee that lives in only one client is not
a guarantee; it is a coincidence waiting to be discovered at 2am.

The guard you just triggered instead is a `BEFORE INSERT` trigger that refuses an
id which already exists. It needs no setting, so it holds from *any* client.
Enforcement matches the claim — which is the entire subject of Chapter 2.

## Exercise 3: watch a transaction roll back

A restock has to change three things: inventory goes up, cash goes down, and an
event records it. If only some of those happen, the organization is lying to
itself.

```bash
python - <<'PY'
import tempfile, pathlib
from unittest.mock import patch
import reference_organizations.store as store
from reference_organizations.store import RestockProposal, apply_restock, record_sale, seed
from sovereign_agent.models import Role
from sovereign_agent.organization import Organization

org = Organization.init(pathlib.Path(tempfile.mkdtemp()))
seed(org.db)

# An effect needs a real completed assignment behind it. Chapter 2 explains why.
outcome = org.create_outcome(
    "Keep the shelf stocked", "stocked",
    ["inventory_at_or_above_reorder_point"], "principal-human", "SKU-TEA")
org.activate(outcome.id, "master-course")
sow = org.create_sow(outcome.id, "replenish", Role.OPERATOR, "master-course")
org.ready_sow(sow.id)
assignment = org.run_assignment(org.assign(sow.id, "operator-course", "master-course").id)

signal = record_sale(org.db, "SKU-TEA", 2, 400)

def state():
    on_hand = org.db.connection.execute(
        "SELECT on_hand FROM inventory WHERE sku='SKU-TEA'").fetchone()["on_hand"]
    cash = org.db.connection.execute(
        "SELECT COUNT(*) c FROM cash_entries WHERE amount_cents<0").fetchone()["c"]
    return f"on_hand={on_hand} purchase_entries={cash}"

print("before: ", state())
with patch.object(store, "append_event", side_effect=RuntimeError("power cut")):
    try:
        apply_restock(org.db, RestockProposal("SKU-TEA", 6), assignment.id, signal.id)
    except RuntimeError as error:
        print("failed: ", error)
print("after:  ", state())
PY
```

Expected: `before` and `after` are identical. The failure was injected *after*
inventory had already been written — and the rollback took it back. Either all
three changes happen, or none do.

## Exercise 4: find the boundary between governance and operations

```bash
sovereign-agent demo store --mode simulated --root /tmp/lucy-boundary
cat /tmp/lucy-boundary/sovereign.toml
ls /tmp/lucy-boundary/governance/outcomes/*/
```

Two kinds of file, and they behave differently:

- **`sovereign.toml`** is read every time the organization opens. Edit an actor's
  `provider = ` line, reopen, and the change takes effect. It is *canonical*.
- **`governance/outcomes/*/outcome.json` and `README.md`** are written and never
  read back. Delete the whole `governance/` directory and the organization keeps
  working perfectly. They are *projections*.

Try it:

```bash
python -c "
import shutil, sys; sys.path.insert(0,'src')
shutil.rmtree('/tmp/lucy-boundary/governance')
from sovereign_agent.organization import Organization
o = Organization('/tmp/lucy-boundary')
print(o.status_text(o.db.connection.execute('select id from outcomes').fetchone()['id']))
"
```

It still prints the outcome. Nothing was lost, because SQLite held the truth.

Markdown is one step further out: it is generated for *humans* and is never
authoritative for anything. If it disagrees with the database, the database is
right and the Markdown is stale.

The full boundary — and the one thing this design cannot honestly promise — is
written up in [docs/persistence-boundary.md](../../docs/persistence-boundary.md).
Read the section titled "The limit you must not lie about".

## Learner verification command

```bash
python -m pytest tests/test_persistence.py -q
```

Expected: all tests pass. They prove rollback, append-only enforcement,
migrations applying in order, and a v1 database upgrading to v2 without losing
its history.

## Explain it back

1. Cash is stored as a list of signed movements instead of one balance number.
   Name one specific bug that choice makes impossible.
2. The event triggers refuse `UPDATE` and `DELETE`. Why enforce that in SQLite
   instead of just not writing such code?
3. You delete `governance/` and nothing breaks. You delete
   `.sovereign/organization.db` and everything is gone. Explain the difference
   in one sentence.
4. A restock fails after inventory is written but before the event. What does
   the shelf look like afterwards, and why?
5. The docs say SQLite and the filesystem cannot be updated in one transaction.
   Describe a state the organization can end up in because of that.

Next: [Chapter 2 — Work needs governance](../ch02_work_needs_governance/README.md)
