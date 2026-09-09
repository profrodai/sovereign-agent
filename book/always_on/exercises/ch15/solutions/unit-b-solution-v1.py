"""Instructor reference; requires the Unit A handoff."""


# ruff: noqa: F821
def repair_fragment():
    return '"UPDATE assistant_control SET epoch=?,paused=1 WHERE id=1"'


assert connect_repair(repair_fragment())["status"] == "PASS"
