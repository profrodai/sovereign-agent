## Improvement changes a version under an evidence contract

Lucy notices that an opening procedure omits reserved stock. Editing the active procedure in
place seems convenient, but destroys the relationship between an earlier evaluation and the
version now running. This chapter separates **candidate**, **evaluation** and **activation**.
A candidate is a proposed immutable version. Evaluation produces evidence for specified cases
under a specified configuration. Activation changes which version future work will use.

A **regression** is behavior that used to satisfy a requirement and no longer does after a
change. A regression suite retains earlier cases while adding the newly discovered failure.
Passing only the new case can hide damage to an old one. **Rollback** restores a prior active
version; it does not erase effects produced while the intervening version was active.

### Record what was actually evaluated

A result named “PASS” without its candidate and baseline is ambiguous. Suppose evaluation starts
with active version 2, but someone activates version 3 before evaluation finishes. The result
may be valid for the old configuration and stale for the new one. **Optimistic concurrency**
means doing expensive work without holding a long write transaction, then checking that the
assumed baseline is still current before committing the change.

```python tags=["foundation", "worked-example"]
intro_active = {"opening": 2, "delivery": 1}
intro_evaluated_baseline = dict(intro_active)
intro_results = {"ordinary-stock": True, "reserved-stock": True}
intro_active["delivery"] = 2
intro_stale = intro_active != intro_evaluated_baseline
print("Cases passed:", all(value is True for value in intro_results.values()))
print("Configuration changed:", intro_stale)
assert intro_stale
```

The two observations can both be true: all named cases passed and activation must refuse because
its baseline changed. Re-running against the current configuration is a different act from
ignoring the stale flag. The comparison belongs inside the transaction that changes active rows,
so another writer cannot slip between the final check and activation.

### Exact truth values and complete case coverage

Python treats many values as truthy, including integer one and a nonempty string. A callback
contract that requires exact boolean `True` should not accept those values as test evidence.
Missing a required case is also different from an observed failure. Require named positive
evidence for every required case before activation.

```python tags=["foundation", "worked-example"]
intro_required_cases = {"ordinary-stock", "reserved-stock"}
intro_reports = [
    {"ordinary-stock": True, "reserved-stock": True},
    {"ordinary-stock": True},
    {"ordinary-stock": True, "reserved-stock": 1},
    {"ordinary-stock": True, "reserved-stock": False},
]
for intro_report in intro_reports:
    intro_complete = intro_required_cases <= intro_report.keys()
    intro_positive = intro_complete and all(
        intro_report[name] is True for name in intro_required_cases
    )
    print(intro_report, "admissible evidence:", intro_positive)
```

Only the first report satisfies this evidence contract. This does not prove that the evaluator
itself is a trustworthy oracle. It establishes that activation honors the declared evidence
shape. The evaluation chapter supplies the separate reasoning about independent expected results.

### Freeze both the candidate and the comparison baseline

A callback could mutate the candidate object while evaluating it. Serializing the candidate
before evaluation and checking afterward detects this change. A shallow reference to the same
mutable dictionary would not preserve the earlier bytes. Similarly, a version name without its
content identity is too weak if content can change under that name.

The actual `activate_skill` path stages an immutable version, captures the active snapshot,
evaluates outside the write transaction, then checks candidate and baseline inside the activation
transaction. The context builder later reads active rows, making activation observable in the
next model input. That final use is the connection: storing a candidate row alone does not change
the running procedure.

Unit A constructs this complete boundary. Unit B removes the stale-configuration protection and
uses an evaluation callback that deliberately changes another active skill. Inspect which version
is active after the attempted activation and after reopening SQLite. The transfer introduces
missing cases, `False`, integer one, candidate mutation and an uncontended valid activation.

Before coding, draw the sequence baseline capture → evaluation → transaction → baseline compare
→ active swap. Place a second writer at each gap and predict the outcome. Then explain what
evidence should remain after a refusal and after a rollback. “Self-improvement” is not permission
for the agent to bypass this version and evaluation boundary.
