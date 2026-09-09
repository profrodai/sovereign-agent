"""Instructor reference; requires the Unit A handoff."""


# ruff: noqa: F821
def repair_fragment():
    return 'if budget["spent_pence"] + budget["reserved_pence"] + addition > min('


assert connect_repair(repair_fragment())["status"] == "PASS"
