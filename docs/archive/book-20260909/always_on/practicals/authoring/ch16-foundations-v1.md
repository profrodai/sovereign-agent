## Acceptance assembles independent evidence for an operating day

Lucy needs to know what the assistant actually accomplished: work received, drafts prepared,
orders confirmed, money reserved, deliveries still uncertain and recovery actions still needed.
A final paragraph saying “everything went well” is an output, not independent acceptance evidence.
An **acceptance criterion** names an observable condition required before we accept the system
for a stated use. A **business-day scenario** exercises several mechanisms in sequence.

The book's final scenario combines tools, memory, scheduling, authority, supplier ambiguity,
worker recovery, evaluation and operation. The report must keep evidence sources distinct so
agreement is meaningful. Comparing one summary field with another field computed from the same
buggy total is not independent reconciliation.

### Reconcile orders with the spending ledger

An approved, sending or unknown order retains reserved exposure. A confirmed or delivered order
contributes to known spent exposure under this report's contract. A rejected order contributes
neither. Predict the reserved and spent totals below before computing them, then compare with a
separately supplied ledger. The list of uncertain operations belongs beside the totals.

```python tags=["foundation", "worked-example"]
intro_orders = [
    {"id": "one", "status": "CONFIRMED", "amount": 1500},
    {"id": "two", "status": "UNKNOWN", "amount": 1100},
    {"id": "three", "status": "REJECTED", "amount": 400},
]
intro_reserved = sum(
    row["amount"] for row in intro_orders if row["status"] in {"APPROVED", "SENDING", "UNKNOWN"}
)
intro_spent = sum(
    row["amount"] for row in intro_orders if row["status"] in {"CONFIRMED", "DELIVERED"}
)
intro_ledger = {"reserved": 1100, "spent": 1500}
intro_uncertain = [row["id"] for row in intro_orders if row["status"] == "UNKNOWN"]
print("Orders:", intro_reserved, intro_spent, "ledger:", intro_ledger, "unknown:", intro_uncertain)
assert (intro_reserved, intro_spent) == (1100, 1500)
assert intro_uncertain == ["two"]
```

If the ledger said 1000 reserved, the report should expose the 100-pence disagreement. It must
not choose whichever source makes the day look more successful. **Unknown** is a state with a
reason; it is not zero. The same applies to historical usage after a stale restore: missing
records cannot justify a confident zero-cost claim.

### A report needs one consistent read boundary

Suppose one query reads an order before confirmation and a later query reads its ledger after
confirmation. The combined report can appear inconsistent even though each database state was
internally consistent. A read transaction provides a snapshot for related local queries. The
actual `operating_report` opens its own read snapshot, queries the work/order/ledger tables,
obtains stock through the real tool path and retains scope information.

```python tags=["foundation", "worked-example"]
intro_before = {"order_state": "UNKNOWN", "reserved": 1100, "spent": 1500}
intro_after = {"order_state": "CONFIRMED", "reserved": 0, "spent": 2600}
intro_mixed = {"order_state": intro_before["order_state"], "reserved": intro_after["reserved"]}
print("Mixed-time report:", intro_mixed)
assert intro_mixed == {"order_state": "UNKNOWN", "reserved": 0}
```

The mixed dictionary illustrates the problem; it is not itself a concurrent database test.
The connected runtime task supplies the real read transaction and multiple sources. A snapshot
of local SQLite also does not freeze a remote supplier. Label which evidence is local and which
comes from an independently observed external fixture.

### Design a failure schedule, not just a happy-path demo

A **failure schedule** states where an interruption occurs: before durable intent, after supplier
acceptance but before reply, after a lease replacement, or after a backup but before another
external order. Each location changes what evidence is available. Predict the expected retained
state before running. If a failure occurs elsewhere, diagnose that difference rather than
declaring the planned experiment passed.

Unit A constructs the operating report from the real data sources. Unit B corrupts one total
and asks you to trace the discrepancy back to its query. The transfer includes empty work,
uncertain delivery, unknown historical usage, changed supplier totals and a reordered catalog.
The final practical asks you to use earlier concepts to defend an acceptance decision.

### Retain an operational explanation

Your submission should let another person answer: which source supports each claim, which
operation remains uncertain, which budget is still reserved, and what action is allowed next?
Include an explicit next check for each uncertainty. Do not invent a purchase, refund or resend
merely to make the report terminal. The notebook's offline acceptance is scoped to the authored
scenario and fixtures; live model quality, phone delivery, OS containment and host operation
retain their separate evidence requirements.

Before the main task, draw the day as events with two columns for local and supplier evidence.
Circle every point where a retry could create a second effect. Then name the identity, authority
and reconciliation mechanism that prevents or detects it. This is cumulative understanding:
the final chapter should make earlier boundaries easier to explain, not hide them inside a demo.
