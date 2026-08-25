# Chapter 1 — The organization remembers

## Learning objective

Understand where a Zero-Employee Organization keeps its memory, why some of that
memory is allowed to change and some is not, and what a transaction actually
buys you.

By the end you should be able to say, for any piece of data in this system,
**which file or table is the authority for it** — and defend the answer.

## Why memory is the first hard problem

An organization that forgets cannot be held to anything. If the tea order can
vanish because a process died halfway through, then "we ordered the tea" is a
hope, not a fact.

So the first question is not "how does the AI decide" — it is "where does the
truth live, and what happens when the power goes out mid-sentence".

## Exercise 1: look at the operational state

```bash
sovereign-agent demo store --mode simulated --root /tmp/andrea-memory
sqlite3 /tmp/andrea-memory/.sovereign/organization.db ".tables"
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
sqlite3 -header -column /tmp/andrea-memory/.sovereign/organization.db \
  "SELECT * FROM inventory; SELECT id, amount_cents FROM cash_entries;"
```

Cash is a **ledger of movements**, not a single balance field. The balance is
`SUM(amount_cents)`: `10000` opening, `+800` from the sale, `-720` for the
purchase. Nothing overwrites a balance, so nothing can quietly lose money.

## Exercise 2: prove the events are append-only

The event log is the organization's memory of what it did. Try to rewrite it.

```bash
sqlite3 /tmp/andrea-memory/.sovereign/organization.db \
  "UPDATE events SET kind='NOTHING_HAPPENED' WHERE kind='sale.committed';"
```

Expected:

```text
Error: stepping, events are append-only: update refused (19)
```

Now try deleting:

```bash
sqlite3 /tmp/andrea-memory/.sovereign/organization.db \
  "DELETE FROM events WHERE kind='replenishment.committed';"
```

Also refused. Now try the sneaky third variant — overwriting a row instead of
editing it:

```bash
sqlite3 /tmp/andrea-memory/.sovereign/organization.db \
  "INSERT OR REPLACE INTO events(id,kind,payload,created_at)
   SELECT id,'NOTHING_HAPPENED',payload,created_at FROM events LIMIT 1;"
```

Also refused: `events are append-only: replace refused`.

All three are enforced by **database triggers**, not by Python being careful.
That distinction matters: a rule enforced in application code protects you from
bugs, but a rule enforced in the database protects you from *everything else
that can reach the database* — including you, at 2am, with a REPL open.

That third case is worth dwelling on, because getting it right took two
attempts. The first version of this guard relied on a SQLite setting called
`recursive_triggers`, which the application switched on when it opened the
database. It worked perfectly — from the application. From the `sqlite3` command
above, the one this chapter just told you to use, the overwrite **succeeded
silently** and the row count did not change. The lesson claimed the database
enforced the rule while the guarantee actually lived in Python.

The fix is the guard you just triggered: a `BEFORE INSERT` trigger that refuses
an id which already exists. It needs no setting, so it holds from any client.
Enforcement now matches the claim — which is the entire subject of Chapter 2.

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
from sovereign_agent.organization import Organization

org = Organization.init(pathlib.Path(tempfile.mkdtemp()))
seed(org.db)
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
        apply_restock(org.db, RestockProposal("SKU-TEA", 6), "asg_demo", signal.id)
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
sovereign-agent demo store --mode simulated --root /tmp/andrea-boundary
cat /tmp/andrea-boundary/sovereign.toml
ls /tmp/andrea-boundary/governance/outcomes/*/
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
shutil.rmtree('/tmp/andrea-boundary/governance')
from sovereign_agent.organization import Organization
o = Organization('/tmp/andrea-boundary')
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
