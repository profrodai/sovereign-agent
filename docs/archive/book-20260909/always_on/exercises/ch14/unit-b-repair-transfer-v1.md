---
jupyter:
  jupytext:
    text_representation:
      extension: .md
      format_name: markdown
      format_version: '1.3'
  kernelspec:
    display_name: Python 3
    language: python
    name: python3
---

# Chapter 14, Unit B — Break, repair and transfer bounded delegation

**Student edition v1 · 2026-09-09 · 75–90 minutes · local Python 3.14**

Floor division underquotes any partial tub. This time you begin with your Unit A implementation and its saved evidence. Lucy’s catering quote leaves one guest without a portion.

## Verify the handoff

Place the Unit A handoff beside this notebook. A missing handoff is an explicit prerequisite failure; the notebook will not silently substitute reference code. Run the setup and keep the runtime and implementation hashes in your submission.

```python tags=["setup", "handoff-consumer"]
import json
import os
import runpy
from pathlib import Path

start = Path(os.environ.get("SOVEREIGN_AGENT_REPO", Path.cwd())).resolve()
ROOT = next(
    (
        p
        for p in (start, *start.parents)
        if (p / "book/always_on/exercises/source_tasks_v1.py").is_file()
    ),
    None,
)
if ROOT is None:
    raise RuntimeError("Set SOVEREIGN_AGENT_REPO to the Sovereign Agent checkout.")
SourceTask = runpy.run_path(str(ROOT / "book/always_on/exercises/source_tasks_v1.py"))["SourceTask"]
CHAPTER = 14
HANDOFF = Path("ch14-unit-a-handoff-v1.json")
handoff_status = "MISSING"
if HANDOFF.is_file():
    task = SourceTask(ROOT, CHAPTER)
    try:
        handoff = task.load(HANDOFF)
        handoff_status = "VERIFIED"
        print("IMPLEMENTATION", handoff["implementation_sha256"])
    finally:
        task.close()
print("UNIT_A_HANDOFF", handoff_status)
```

## Reproduce and diagnose

Predict the consequence of this injected boundary before executing it:

```text
tubs = inquiry.guests // 10
```

The controlled mutation changes the same implementation you submitted. It refuses if the declared mutation boundary no longer occurs exactly once; inspect an alternative implementation with the instructor before adapting the experiment.

```python tags=["failure-experiment"]
baseline = broken = None
if handoff_status == "VERIFIED":
    task = SourceTask(ROOT, CHAPTER)
    try:
        task.load(HANDOFF)
        baseline = task.visible("YOUR_BASELINE")
        if baseline["status"] != "PASS":
            raise ValueError("Saved Unit A code no longer satisfies the visible contract")
        task.inject_failure()
        broken = task.run("INJECTED_FAILURE", expected=task.spec["expected_broken"])
        print("BEFORE", baseline["observation"])
        print("AFTER", broken["observation"])
    finally:
        task.close()
else:
    print("HANDOFF_REQUIRED: complete Unit A before performing Unit B")
```

State a diagnosis using those two observations. Name a test that would prove your diagnosis wrong. Invoke the actual quote tool used by the delegated research path and inspect product identity, total and unchanged stock.

## Repair the boundary

Return the complete replacement for the injected fragment. Do not edit the oracle or print a desired observation. Repair the actual source. The starter keeps the defect so the learner outcome remains incomplete.

```python tags=["exercise", "learner-owned"]
def repair_fragment():
    return "tubs = inquiry.guests // 10"
```

<details><summary>Hint 1 — the consequence</summary>

Lucy’s catering quote leaves one guest without a portion.

</details>

<details><summary>Hint 2 — the evidence</summary>

Compare the two observations, then trace the changed field to `quote` in `src/reference_organizations/store/delegation.py`. Distinguish a schema refusal from a business-rule or authority refusal.

</details>

<details><summary>Hint 3 — the design</summary>

Read the requested product record, validate positive integer price and use integer ceiling arithmetic for ten portions per tub.

</details>

```python tags=["integration", "learner-path"]
def connect_repair(fragment):
    task = SourceTask(ROOT, CHAPTER)
    try:
        task.load(HANDOFF)
        task.inject_failure()
        task.repair(fragment)
        return task.visible("YOUR_REPAIR")
    finally:
        task.close()


repair_result = None
if handoff_status == "VERIFIED":
    repair_result = connect_repair(repair_fragment())
    print("REPAIR", repair_result["status"], repair_result["observation"])
else:
    print("REPAIR_NOT_ATTEMPTED: missing Unit A evidence")
```

## Transfer under a changed constraint

Try 1, 10, 17 and 200 guests, a changed product price and invalid Inquiry shapes. Explain why fixed arithmetic earns zero model calls.

Create a fresh task, load your handoff, inject the defect and apply your repair. Then change only the copied probe to exercise the new condition. Keep the actual observation and a prediction written beforehand. Explain why a visible-case lookup or a blanket refusal could pass the original example but fail this transfer.

The instructor's holdout applies your repair to a new copied runtime and checks both the positive case and the missing protection. An exact exception or changed state must cause a failure; no broad error is accepted as successful refusal.

## Exit ticket

Submit the original handoff, baseline and broken observations, repair, transfer probe and results. State what Lucy would experience before and after the fix. Identify the guarantee that still requires separate evidence: A delegated draft neither reserves stock nor authorizes a purchase.

```python tags=["exercise-report"]
passed = repair_result is not None and repair_result["status"] == "PASS"
exercise_report = {
    "unit": "ch14-b",
    "attempted": int(repair_result is not None),
    "completed": int(passed),
    "failed": int(repair_result is not None and not passed),
    "skipped": int(repair_result is None),
    "connection": "PASS" if passed else "NOT_READY",
    "handoff": handoff_status,
}
print("EXERCISE_REPORT=" + json.dumps(exercise_report, sort_keys=True))
```
