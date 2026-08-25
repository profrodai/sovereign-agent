"""Typed refusals that name the invariant and the next command."""

from __future__ import annotations


class Refusal(Exception):  # noqa: N818
    """A fail-closed decision that must not be treated as success."""

    def __init__(
        self,
        happened: str,
        why: str,
        inspect: str,
        next_command: str,
        *,
        category: str = "refusal",
    ) -> None:
        self.happened = happened
        self.why = why
        self.inspect = inspect
        self.next_command = next_command
        self.category = category
        super().__init__(f"{happened} {why} Inspect: {inspect}. Next: {next_command}")
