## Delegation is a bounded assignment, not a reason to use another model

Lucy asks for a catering quote. One part is fixed arithmetic: divide guests by portions per tub,
round up, multiply by a validated price. Another part might require research or judgment. A
**delegated assignment** gives a worker a specific objective, inputs, authority, budget and a
result contract. A **handoff** returns evidence the parent can inspect. More workers do not
automatically improve either answer quality or operating cost.

Start with the deterministic part so you can defend whether delegation adds value. A function
that calculates a quote can be easier to verify than a second model describing the calculation.
The chapter's architecture comparison retains the function when that is the better-supported
choice. The exercise is not scored by how many agents it creates.

### Derive ceiling division without floating point

Ten guests fit one ten-portion tub. Eleven guests require two. Integer floor division `//`
would return one for eleven divided by ten and underquote the order. For positive integers,
`(guests + portions - 1) // portions` rounds upward. Work the boundaries 1, 10, 11 and 20 by hand.

```python tags=["foundation", "worked-example"]
intro_portions = 10
for intro_guests in (1, 10, 11, 17, 20):
    intro_tubs = (intro_guests + intro_portions - 1) // intro_portions
    intro_total = intro_tubs * 325
    print(intro_guests, "guests:", intro_tubs, "tubs:", intro_total, "pence")
assert (11 + 10 - 1) // 10 == 2
```

The formula's precondition matters. Zero portions would divide by zero; negative or boolean
guest counts are not valid inquiries under the strict contract. A Pydantic `Inquiry` represents
validated input. The quote function looks up the requested catalog product and validates its
selling price. It returns an explicit draft and does not reserve stock or authorize a purchase.

### A replacement must inherit used allowance

Suppose an assignment has a three-attempt budget. Its first worker uses two attempts and fails.
A replacement inherits one remaining attempt, not a fresh budget of three. Otherwise repeatedly
replacing a worker makes a bounded assignment unbounded. Keep assignment identity separate from
worker identity and keep usage attached to the assignment.

```python tags=["foundation", "worked-example"]
intro_assignment = {"id": "quote-research", "limit": 3, "used": 2}
intro_workers = ["first-worker", "replacement-worker"]
for intro_worker in intro_workers:
    intro_remaining = max(0, intro_assignment["limit"] - intro_assignment["used"])
    print(intro_worker, "remaining assignment allowance", intro_remaining)
assert intro_remaining == 1
```

This table illustrates retained accounting, not a full worker implementation. The surrounding
runtime supplies claims, leases, parent cancellation and result identity. A child may produce
a result after its parent cancels; accepting it must still depend on current authority and the
assignment's state. Duplicate results should not duplicate downstream effects.

### Compare alternatives using the same task

Hold inputs and required output fixed. Record the ordinary function's result, observed model
attempts and cost, then compare a delegated path under the same contract. A zero-model-call
function is a legitimate baseline. If the delegated result is different, inspect which difference
is useful and what evidence supports it. Avoid comparing a simple arithmetic task with a larger
research task and attributing the entire difference to delegation.

Unit A builds the real quote function used by the delegated research path. Unit B injects floor
division, then checks partial-tub cases against the actual quote tool. The changed-constraint
exercise varies portions per tub and price so a memorized ten-portion expression is insufficient.
You must validate the new contract, calculate the draft, and retain physical stock unchanged.

Before coding, distinguish inquiry, quote, reservation, approval and purchase. Draw their order
and mark which transitions this notebook implements. At the end, write a short decision record:
keep the function or delegate, observed evidence, cost/latency limits, and one future condition
that would justify reconsidering. A defensible decision is a learning outcome, not an optional
essay after “the real coding.”
