"""Instructor reference; requires the Unit A handoff."""


# ruff: noqa: F821
def repair_fragment():
    return "        if args.quantity != needed:"


assert connect_repair(repair_fragment())["status"] == "PASS"
