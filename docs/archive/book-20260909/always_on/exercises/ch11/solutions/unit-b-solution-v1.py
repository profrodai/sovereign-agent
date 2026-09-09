"""Instructor reference; requires the Unit A handoff."""


# ruff: noqa: F821
def repair_fragment():
    return "if tool is None or call.name not in self.allowed:"


assert connect_repair(repair_fragment())["status"] == "PASS"
