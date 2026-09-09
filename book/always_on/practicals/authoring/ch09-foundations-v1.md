## An ambiguous response leaves two systems with different knowledge

Lucy approves an order. The supplier stores it, then the network reply is lost. Locally we see a
timeout; remotely an order exists. The central difficulty is not calculating the quantity again.
It is deciding what evidence is available without creating another purchase. **Distributed state**
means relevant records live in more than one independently changing system.

An **intent** is the durable local record of one exact operation before sending. An **operation
identity** distinguishes that intent from another business operation. A **receipt** binds a
supplier outcome to that identity and exact proposal. **Reconciliation** asks the external system
for evidence and brings local state into agreement where the evidence is conclusive.

### Separate the effect from the caller's observation

The function below deliberately stores a supplier record before raising. The exception describes
what the caller observed; it does not reverse the stored effect. Predict both the local exception
and the independent order count before running.

```python tags=["foundation", "worked-example"]
intro_supplier_orders = {}


def intro_accept_then_lose_reply(operation, proposal):
    if operation in intro_supplier_orders and intro_supplier_orders[operation] != proposal:
        raise ValueError("same identity used for different intent")
    intro_supplier_orders.setdefault(operation, dict(proposal))
    raise TimeoutError("reply lost after acceptance")


for intro_operation in ("opening-order", "opening-order"):
    try:
        intro_accept_then_lose_reply(intro_operation, {"sku": "MANGO", "quantity": 4})
    except TimeoutError:
        print("caller state UNKNOWN; supplier count", len(intro_supplier_orders))
assert len(intro_supplier_orders) == 1
```

This fixture's stable-identity contract prevents a second effect when the same operation is
repeated. A real supplier must explicitly support the relevant behavior; a local ID string alone
cannot force a remote service to deduplicate. The book's supplier fixture lets us inspect the
independent records so the experiment does not grade its own final prose.

### Why a new identity creates a new operation

Repeat the experiment with a new identity after the lost reply. Nothing tells the supplier that
the second identity is intended as a retry of the first. There are now two valid-looking intents
for the same products. Identical payloads are not enough to conclude that two operations are one.

```python tags=["foundation", "worked-example"]
try:
    intro_accept_then_lose_reply("opening-order-retry", {"sku": "MANGO", "quantity": 4})
except TimeoutError:
    pass
assert len(intro_supplier_orders) == 2
print("Stored operation identities:", sorted(intro_supplier_orders))
```

Unit B introduces this defect at the actual send boundary with a freshly generated UUID. A
**UUID** is a generated identifier; uniqueness is useful for a new intent but harmful when it
accidentally turns a retry into a new business operation. The repair reuses the recorded identity
and proposal. The evidence is the supplier's order count, not a message claiming “retry handled.”

### Read the local state machine

| State | What the local record says | What it does not establish |
|---|---|---|
| APPROVED | Exact intent has bounded authority | Supplier acceptance |
| SENDING | Send was admitted and intent recorded | A conclusive response |
| UNKNOWN | Available evidence cannot settle the outcome | Failure or permission for a new order |
| CONFIRMED | Matching accepted receipt was retained | Physical delivery |
| REJECTED | Matching conclusive rejection was retained | That every transport failure is rejection |

The reservation remains held while the outcome is uncertain. On a matching accepted receipt,
money moves from reserved to spent exactly once. On a conclusive rejection, the reservation is
released. A repeated identical receipt must not spend twice; a contradictory receipt must not
silently overwrite the first outcome. Both identity and exact proposal need comparison.

### Adapt vocabulary without weakening evidence

Another supplier may call its fields `order_ref`, `payload` and `decision`. An adapter maps these
names to the internal receipt. It must preserve operation and proposal and reject unknown
decisions. `None` from a lookup is not an accepted receipt. Nor is an unavailable lookup proof
that no remote order exists. Keep absence, unavailability and conclusive rejection distinct.

The core code uses SQLite for local intent and a local supplier fixture for independent effects.
A loopback server, where used, listens on this machine rather than contacting a real supplier.
Its subprocess and temporary database are supplied infrastructure. Your work constructs the
transition boundary, repairs identity handling and normalizes changed discovery data.

Before coding, draw two columns, local ledger and supplier ledger, at four instants: before send,
after acceptance, after lost reply and after lookup. Put unknown values explicitly in the table.
The transfer task will change the receipt vocabulary and failure schedule while requiring the
same accounting invariant.
