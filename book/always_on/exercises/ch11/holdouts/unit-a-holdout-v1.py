"""Instructor holdout appended to a submitted Chapter 11 Unit A."""

# ruff: noqa: F821
import json

task = SourceTask(ROOT, CHAPTER)
try:
    task.install(implementation_source)
    outcome = task.transfer(ROOT / "book/always_on/exercises/ch11/holdouts/runtime-transfer-v1.py")
    assert outcome["status"] == "PASS", outcome
finally:
    task.close()
print("HOLDOUT_RESULT=" + json.dumps({"unit": "ch11-a", "status": "PASSED"}, sort_keys=True))
