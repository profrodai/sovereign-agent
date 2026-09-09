"""Instructor holdout appended to a submitted Chapter 15 Unit B."""

# ruff: noqa: F821
import json

task = SourceTask(ROOT, CHAPTER)
try:
    task.load(HANDOFF)
    task.inject_failure()
    task.repair(repair_fragment())
    outcome = task.transfer(ROOT / "book/always_on/exercises/ch15/holdouts/runtime-transfer-v1.py")
    assert outcome["status"] == "PASS", outcome
finally:
    task.close()
print("HOLDOUT_RESULT=" + json.dumps({"unit": "ch15-b", "status": "PASSED"}, sort_keys=True))
