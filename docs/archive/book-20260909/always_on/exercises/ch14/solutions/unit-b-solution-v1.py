"""Instructor reference; requires the Unit A handoff."""


# ruff: noqa: F821
def repair_fragment():
    return "tubs = (inquiry.guests + 9) // 10"


assert connect_repair(repair_fragment())["status"] == "PASS"
