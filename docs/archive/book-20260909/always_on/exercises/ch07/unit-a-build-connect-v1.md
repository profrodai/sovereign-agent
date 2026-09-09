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

# Chapter 7, Unit A — Construct scheduling

**Student edition v1 · 2026-09-09 · 90–120 minutes · local Python 3.14**

**Design question:** Missed wakeups should coalesce?

Build the scheduler transaction: validate inputs, honor pause and enabled flags, order due jobs, admit bounded work, retain deferral, advance next_due past now and record skipped intervals.

You edit a complete function in a temporary copy of `src/sovereign_agent/assistant_work.py`. The real callers, database and tool boundaries remain connected. Run from the locked Sovereign Agent development environment. The notebook runs reviewed local subprocesses; it is not a security sandbox. No live account is required.

## Predict before running

Use schedule and tick against SQLite and inspect created work IDs, job time and events across repeated passes.

Write the expected result and a falsifying observation before running. Include one legal action, one refusal, and the exact-empty case where the interface permits it. Explain the consequence for Lucy if your prediction is wrong.

```python tags=["setup"]
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
CHAPTER = 7
HANDOFF = Path("ch07-unit-a-handoff-v1.json")
```

## Construct the complete mechanism

Implement `tick` in the string below. Keep the named signature and existing helper interfaces. The starter is intentionally incomplete; its failed connection is reported separately from whether the notebook itself executed. A constant answer cannot stand in for the real mechanism.

Read the chapter and the caller around the function in `src/sovereign_agent/assistant_work.py`. Draw the data path from the observed output through this function to its actual input or query. Then write your implementation from the contract.

```python tags=["exercise", "learner-owned"]
implementation_source = """
def tick(db: Database, *, now: float | None = None, maximum: int = 100) -> list[str]:
    raise NotImplementedError("Construct this chapter mechanism")
"""
```

<details><summary>Hint 1 — the design</summary>

Advancing by one interval replays every missed wakeup after downtime.

</details>

<details><summary>Hint 2 — the boundary</summary>

Inspect the parameters and the caller in `src/sovereign_agent/assistant_work.py`. Identify validation, durable state and the first externally observable effect. Preserve the existing surrounding helper contracts.

</details>

<details><summary>Hint 3 — the structure</summary>

Calculate elapsed whole intervals, enqueue one occurrence, then advance by skipped plus one intervals in the same transaction.

</details>

## Connect to the cumulative runtime

The following installs your complete function into the copied runtime and executes the chapter probe against it. It saves your implementation and the observed connection for Unit B only after that connection succeeds.

```python tags=["integration", "handoff"]
def connect_build(source):
    task = SourceTask(ROOT, CHAPTER)
    try:
        task.install(source)
        result = task.visible()
        if result["status"] == "PASS":
            task.save(HANDOFF, result)
        return result
    finally:
        task.close()


build_result = connect_build(implementation_source)
print("CONNECTION", build_result["status"])
print("OBSERVATION", build_result["observation"])
```

## Challenge and transfer

Use exact due time, fractional intervals, a very long absence and repeated same-time ticks. Separate coalescing from total queue capacity.

Use a fresh `SourceTask`, install your implementation and edit **only its copied probe** to run the changed input. Keep the expected result in your prediction notes, independent of your implementation. Call `task.run("MY_TRANSFER", expected=your_expected)` and close the task in `finally`. Retain both a valid and a refused case so rejecting everything cannot pass.

The instructor runs additional cases with different identities and boundaries against the real source. Passing the visible connection alone is not the transfer verdict. Do not put instructor solutions or holdouts into a student submission.

## Save and explain

After success, submit `ch07-unit-a-handoff-v1.json`, your source, prediction notes and changed-input observations. Unit B checks the chapter, runtime hash and exact implementation hash and re-executes your code.

Explain which input or state caused the output, which observation would refute the explanation and what remains outside the guarantee: This does not guarantee a running host or a wakeup at an exact wall-clock time.

```python tags=["exercise-report"]
exercise_report = {
    "unit": "ch07-a",
    "attempted": 1,
    "completed": int(build_result["status"] == "PASS"),
    "failed": int(build_result["status"] != "PASS"),
    "skipped": 0,
    "connection": build_result["status"],
    "handoff": "WRITTEN" if build_result["status"] == "PASS" else "NOT_READY",
}
print("EXERCISE_REPORT=" + json.dumps(exercise_report, sort_keys=True))
```
