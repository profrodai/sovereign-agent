"""Instructor reference; requires the Unit A handoff."""


# ruff: noqa: F821
def repair_fragment():
    return "(sku, threshold - stock + reserved)"


assert connect_repair(repair_fragment())["status"] == "PASS"
