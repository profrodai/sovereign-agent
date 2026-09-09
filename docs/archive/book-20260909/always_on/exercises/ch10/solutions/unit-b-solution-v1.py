"""Instructor reference; requires the Unit A handoff."""


# ruff: noqa: F821
def repair_fragment():
    return "or work.epoch != current_epoch"


assert connect_repair(repair_fragment())["status"] == "PASS"
