"""Instructor reference; requires the Unit A handoff."""


# ruff: noqa: F821
def repair_fragment():
    return '"WHERE session=? AND active=1",\n            (session,),'


assert connect_repair(repair_fragment())["status"] == "PASS"
