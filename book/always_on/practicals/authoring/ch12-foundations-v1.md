## Evaluation asks a precise question of independently specified evidence

An agent can produce fluent text and still order the wrong amount. An **evaluation case** fixes
inputs, a task and expected business outcomes. An **oracle** defines those outcomes independently
of the candidate. A **baseline** is a simpler method used for comparison. A **metric** summarizes
observations; it does not replace the per-case evidence that produced it.

For Lucy, relevant facts include product identity, physical stock, reserved stock, target and
price. Sellable stock is physical stock minus reserved stock. If physical stock is six, four
are reserved and the target is five, the deficit is three. A baseline that ignores reservations
will report no deficit and can make a correct agent look wrong.

### Calculate a case before writing its oracle

Predict the needed quantities for the rows below, including the exact-threshold row. The
expected dictionary is written independently, before the baseline calculation. Do not replace
it with the candidate's own output when the comparison fails.

```python tags=["foundation", "worked-example"]
intro_case_rows = [
    {"sku": "MANGO", "physical": 6, "reserved": 4, "target": 5},
    {"sku": "COCOA", "physical": 7, "reserved": 2, "target": 5},
]
intro_expected = {"MANGO": 3}
intro_baseline = {}
for intro_row in intro_case_rows:
    intro_available = intro_row["physical"] - intro_row["reserved"]
    intro_need = max(0, intro_row["target"] - intro_available)
    if intro_need:
        intro_baseline[intro_row["sku"]] = intro_need
print(intro_baseline)
assert intro_baseline == intro_expected
```

The baseline omits products with no deficit. Including zero entries would change its declared
output contract. Empty input should produce an empty dictionary. Renaming the SKU must change
the identity in the output without changing arithmetic. These are useful checks against a
candidate that simply looks up the visible example.

### Keep the denominator visible

Suppose one system solves nine of ten easy cases and none of two difficult cases. “90%” describes
only the easy subset. A reported aggregate needs its population and missingness. Unrun cases
are not successes or observed failures; retain their status separately. The same discipline
applies to cost and latency: specify which attempts the total includes.

```python tags=["foundation", "worked-example"]
intro_case_results = [
    {"case": "ordinary", "status": "PASS", "pence": 2},
    {"case": "reserved", "status": "FAIL", "pence": 3},
    {"case": "provider-down", "status": "NOT_RUN", "pence": None},
]
intro_observed = [row for row in intro_case_results if row["status"] != "NOT_RUN"]
intro_passes = sum(row["status"] == "PASS" for row in intro_observed)
print("Observed pass fraction:", intro_passes, "/", len(intro_observed))
print("Unrun:", len(intro_case_results) - len(intro_observed))
print("Known recorded cost:", sum(row["pence"] for row in intro_observed))
assert intro_passes == 1 and len(intro_observed) == 2
```

The fraction is one of two observed cases, with one unrun case. A mean alone can hide an important
failed case, so the course retains each observation. **Holdouts** are additional cases withheld
from the visible feedback. They test transfer, but a finite holdout suite is still not proof
for every possible input or every natural-language claim.

### A saved report needs a subject and provenance

Record the evaluated configuration, scenario identities and exact evidence. A digest can detect
changed report bytes; it cannot establish that the report's oracle was correct. A supplied
`Case.expected` is the reference for grading, not an input the baseline may read to generate its
answer. A candidate returning that field would pass by copying the answer rather than calculating.

The actual `baseline` function is connected to `evaluate`, which also invokes the offline shop
model and actual tools. The construction task implements the deterministic calculation from
stock rows. The failure task removes reserved stock from the oracle's arithmetic. Inspect both
baseline and tool observations to determine which side is wrong; do not automatically trust the
component named “baseline.”

Before coding, write cases for no products, exact threshold, a renamed product and reservations
larger than physical stock. Add a fluent but wrong explanation while holding correct tool calls
fixed. Explain why substring checks cannot establish arbitrary prose faithfulness and why an
honest review-required outcome is preferable to a fabricated pass.
