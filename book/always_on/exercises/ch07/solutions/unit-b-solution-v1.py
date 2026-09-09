"""Instructor reference; requires the Unit A handoff."""


# ruff: noqa: F821
def repair_fragment():
    return 'next_due = row["next_due"] + (skipped + 1) * row["interval_seconds"]'


assert connect_repair(repair_fragment())["status"] == "PASS"
