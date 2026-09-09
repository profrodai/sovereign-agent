"""Instructor reference; requires the Unit A handoff."""


# ruff: noqa: F821
def repair_fragment():
    return "if skill_snapshot(db)[0] != baseline:"


assert connect_repair(repair_fragment())["status"] == "PASS"
