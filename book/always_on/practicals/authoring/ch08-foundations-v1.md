## Approval binds an actor to one exact proposal and bounded money

“You may order stock” leaves too many questions unanswered. Which product, quantity, supplier,
price and expiration did Lucy approve? This chapter treats approval as a decision over an exact
proposal and a cumulative budget. A **proposal** is structured intended work. A **digest** names
its serialized bytes. An **approval** records authority to proceed under stated conditions.
A **receipt** is later evidence from the supplier; approval is not that receipt.

### Make a change visible before any execution

Two dictionaries can express the same keys in different insertion orders. Canonical serialization
uses a stable key order and separators before hashing. SHA-256 maps bytes to a fingerprint useful
for detecting change. It is not encryption and does not identify the approving person by itself.
Predict whether changing quantity changes the digest, and whether reordering keys does.

```python tags=["foundation", "worked-example"]
import hashlib
import json


def intro_digest(proposal):
    encoded = json.dumps(proposal, sort_keys=True, separators=(",", ":"), allow_nan=False)
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


intro_proposal = {"sku": "MANGO", "quantity": 4, "unit_pence": 325}
intro_reordered = {"unit_pence": 325, "quantity": 4, "sku": "MANGO"}
intro_changed = {**intro_proposal, "quantity": 5}
assert intro_digest(intro_proposal) == intro_digest(intro_reordered)
assert intro_digest(intro_proposal) != intro_digest(intro_changed)
print("Reordered keys match; a changed quantity requires a new decision.")
```

The `**` syntax copies dictionary entries into a new dictionary before the explicit replacement.
`allow_nan=False` refuses nonstandard non-finite numbers in this representation. The actual order
proposal uses a validated schema and integer pence; hashing arbitrary malformed input would not
make it a meaningful proposal.

### Reserved and spent money answer different questions

**Reserved** money is committed to admitted work whose final outcome may still be pending.
**Spent** money is supported by confirmed accepted outcomes in the local ledger. Available
authority is the ceiling minus both. If 700 pence is spent and 900 reserved under a 2000-pence
ceiling, a 500-pence order is too large even though 500 is smaller than 2000.

```python tags=["foundation", "worked-example"]
intro_spent, intro_reserved, intro_ceiling = 700, 900, 2000
for intro_addition in (0, 400, 401, 500):
    intro_exposure = intro_spent + intro_reserved + intro_addition
    print(
        intro_addition, "total exposure", intro_exposure, "allowed", intro_exposure <= intro_ceiling
    )
assert intro_spent + intro_reserved + 400 == intro_ceiling
```

Four hundred exactly fits; 401 does not. A repeated approval of the same already-reserved
proposal must add zero, not reserve twice. This is **idempotency** at the local approval boundary:
repeating the same admitted decision preserves its accounting effect. It does not mean that
two distinct orders with the same price are the same order.

### Check and reserve in one transaction

If two workers separately read the same available budget and then both reserve it, the combined
result can exceed the ceiling. Validation must be tied to the write within the transaction that
owns the current totals. The actual exercise uses `db.immediate()` for that local critical section.
The installed account ceiling and the supplied policy ceiling both constrain authority; the
effective ceiling is the smaller one. A caller cannot enlarge installed authority by sending a
more generous policy object.

Authority also depends on the actor, expiration, current work and proposal state. A revoked or
expired decision must not become valid because its amount is small. An uncertain supplier outcome
must retain its reservation rather than being reset to a fresh draft. **Revocation** withdraws
future authority; it cannot recall an external request already admitted and sent.

### Translate the contract into cases

Write a table for a fresh draft, repeated approval, changed digest, one-pence overflow, unknown
actor, expiration and uncertain outcome. For each, predict both the returned decision and the
reserved/spent row after the attempt. Refusal with changed money is still a defect.

Unit A implements the complete approval path. Unit B removes part of the cumulative calculation;
the observable over-admission exposes the bug. In the changed-policy exercise, reduce the supplied
ceiling below the installed ceiling and keep the exact-fit case. A blanket refusal cannot satisfy
both the positive and negative cases. The final explanation must name which evidence grants
authority and which future evidence would settle the supplier outcome.
