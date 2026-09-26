# Prof Rod | Build Your Always-On AI Agent From Scratch
# Full book and learning materials: https://profrod.ai/book
# Join the Prof Rod learner community: https://profrod.ai/community
# Original source and updates: https://github.com/profrodai/sovereign-agent

"""Chapter 4: the learner's StateStore against the chapter's acceptance examples.

Every expectation is read by an independent observer connection, never by the store's own
methods. The last example is a negative control: a store that swallows the injected failure
must be caught by the same observer.
"""

import runpy
import sqlite3
import tempfile
from pathlib import Path

LEARNER = runpy.run_path(
    str(
        Path(__file__).resolve().parents[1]
        / "learner/profrod_sovereign_agent_ch04_state_store_learner.py"
    )
)
StateStore, StockEvent, observe = LEARNER["StateStore"], LEARNER["StockEvent"], LEARNER["observe"]
EventConflictError = LEARNER["EventConflictError"]
UnsupportedSchemaError, NestedTransactionError = (
    LEARNER["UnsupportedSchemaError"],
    LEARNER["NestedTransactionError"],
)
SCHEMA_VERSION = LEARNER["SCHEMA_VERSION"]


class InjectedFailureError(Exception):
    """The failure injected between the event write and the stock write."""


def interrupt() -> None:
    raise InjectedFailureError("stopped between the two writes")


def check(label: str, condition: bool) -> None:
    print(f"{'ok  ' if condition else 'FAIL'} {label}")
    if not condition:
        raise SystemExit(1)


def main() -> None:
    with tempfile.TemporaryDirectory() as folder:
        path = Path(folder) / "shop.sqlite3"
        store = StateStore(path)
        check("fresh database migrates from version 0", store.initialize() == (0, SCHEMA_VERSION))
        check("fresh database: no stock", observe(path)["stock"] == {})

        store.apply(StockEvent("e1", "vanilla", 2, "opening count"))
        store.close()
        seen = observe(path)
        check(
            "reopen: vanilla=2 and exactly e1",
            seen["stock"] == {"vanilla": 2} and seen["events"] == ["e1"],
        )

        store = StateStore(path)
        try:
            store.apply(StockEvent("e2", "vanilla", 7, "delivery"), between=interrupt)
        except InjectedFailureError:
            pass
        seen = observe(path)
        check(
            "failure between writes leaves vanilla=2 and only e1",
            seen["stock"] == {"vanilla": 2} and seen["events"] == ["e1"],
        )

        check(
            "identical replay of e1 is a duplicate",
            store.apply(StockEvent("e1", "vanilla", 2, "opening count")) == "duplicate",
        )
        try:
            store.apply(StockEvent("e1", "vanilla", 5, "opening count"))
            conflict = False
        except EventConflictError:
            conflict = True
        check(
            "e1 with other content is a conflict; e1 unchanged",
            conflict and observe(path)["stock"] == {"vanilla": 2},
        )

        try:
            store.apply(StockEvent("e3", "vanilla", -3, "sale"))
            refused = False
        except sqlite3.IntegrityError:
            refused = True
        seen = observe(path)
        check(
            "stock cannot go negative; the event is not kept either",
            refused and seen["events"] == ["e1"],
        )

        try:
            with store.immediate():
                with store.immediate():
                    pass
            nested = False
        except NestedTransactionError:
            nested = True
        check("a nested transaction is refused", nested)

        check("invariant: stock equals the sum of events", seen["stock"] == seen["sums"])
        store.close()

        # A database from the future is refused before anything changes.
        writer = sqlite3.connect(path, autocommit=True)
        writer.execute(
            "UPDATE meta SET value = ? WHERE key = 'stock.version'", (SCHEMA_VERSION + 1,)
        )
        writer.close()
        store = StateStore(path)
        try:
            store.initialize()
            refused = False
        except UnsupportedSchemaError:
            refused = True
        check(
            "a future schema version is refused, rows untouched",
            refused and observe(path)["stock"] == {"vanilla": 2},
        )
        store.close()

    # Negative control: a store whose transaction swallows the failure must be caught.
    class Swallowing(StateStore):
        def apply(self, event, *, between=None):
            try:
                return super().apply(event, between=between)
            except InjectedFailureError:
                self.connection.execute(
                    "INSERT INTO events (event_id, sku, delta, payload, reason)"
                    " VALUES (?, ?, ?, ?, ?)",
                    (event.event_id, event.sku, event.delta, event.payload(), event.reason),
                )
                return "applied"

    with tempfile.TemporaryDirectory() as folder:
        path = Path(folder) / "shop.sqlite3"
        broken = Swallowing(path)
        broken.initialize()
        broken.apply(StockEvent("e1", "vanilla", 2, "opening count"))
        broken.apply(StockEvent("e2", "vanilla", 7, "delivery"), between=interrupt)
        seen = observe(path)
        broken.close()
        check(
            "negative control: the observer catches a half-applied change",
            seen["stock"] != seen["sums"],
        )

    print("Chapter 4 checkpoint: durable state holds across reopen, failure, replay and version.")


if __name__ == "__main__":
    main()
