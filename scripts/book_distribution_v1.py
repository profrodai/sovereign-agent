"""Public teaching identities and source attribution for files shared on their own."""

from __future__ import annotations

import re
from pathlib import Path

PREFIX = "profrod-sovereign-agent"
BOOK_URL = "https://profrod.ai/book"
COMMUNITY_URL = "https://profrod.ai/community"
SOURCE_URL = "https://github.com/profrodai/sovereign-agent"
EDITION = "2026-09-10"
ASSETS = ("textbook", "exercises", "solutions", "educator")
TOPICS = {
    1: "first-model-call",
    2: "pydantic-shop-tools",
    3: "agent-loop",
    4: "sqlite-state",
    5: "durable-memory",
    6: "versioned-skills",
    7: "durable-inbox-outbox",
    8: "telegram-messaging",
    9: "schedules-stock-events",
    10: "spending-permissions",
    11: "ambiguous-supplier-order",
    12: "worker-recovery",
    13: "mcp-tools",
    14: "tool-isolation",
    15: "agent-evaluation",
    16: "controlled-improvement",
    17: "bounded-delegation",
    18: "deployment-restoration",
    19: "integrated-shop-day",
}
UNIT_TOPICS = {
    1: ("grounded-morning-brief", "prompt-harness-repair"),
    2: ("pydantic-shop-tools", "pydantic-validation-repair"),
    3: ("bounded-agent-loop", "failed-call-accounting"),
    5: ("durable-memory", "memory-repair-transfer"),
    6: ("versioned-skills", "skill-repair-transfer"),
    8: ("private-telegram-messaging", "messaging-repair-transfer"),
    9: ("schedules-stock-events", "scheduling-repair-transfer"),
    10: ("exact-spending-approval", "approval-repair-transfer"),
    11: ("durable-order-evidence", "ambiguous-order-recovery"),
    12: ("worker-crash-recovery", "recovery-repair-transfer"),
    14: ("tool-isolation", "isolation-repair-transfer"),
    15: ("agent-evaluation", "evaluation-repair-transfer"),
    16: ("controlled-improvement", "improvement-repair-transfer"),
    17: ("bounded-delegation", "delegation-repair-transfer"),
    18: ("deployment-restoration", "operations-repair-transfer"),
    19: ("integrated-day-acceptance", "acceptance-repair-transfer"),
}


def start_name(asset: str) -> str:
    return f"{PREFIX}-{asset}-start-here.md"


def chapter_name(chapter: int, asset: str) -> str:
    role = {
        "textbook": "chapter",
        "exercises": "exercise-guide",
        "solutions": "solutions-guide",
        "educator": "educator-guide",
    }[asset]
    return f"{PREFIX}-ch{chapter:02d}-{TOPICS[chapter]}-{role}.md"


def unit_name(chapter: int, letter: str, asset: str, *, educator: bool = False) -> str:
    role = "exercise" if asset == "exercises" else "solution"
    if educator:
        role = "educator-" + role
    topic = UNIT_TOPICS[chapter]["ab".index(letter)]
    return f"{PREFIX}-ch{chapter:02d}-{letter}-{topic}-{role}.ipynb"


def unit_path(book: Path, chapter: int, letter: str, asset: str) -> Path:
    return book / asset / f"ch{chapter:02d}" / unit_name(chapter, letter, asset)


def guide_name(chapter: int) -> str:
    return f"{PREFIX}-ch{chapter:02d}-{TOPICS[chapter]}-teaching-guide.md"


def checkpoint_name(chapter: int) -> str:
    return f"{PREFIX}-ch{chapter:02d}-{TOPICS[chapter]}-checkpoint.py".replace("-", "_")


def download_name(asset: str) -> str:
    return f"{PREFIX}-{asset}-2026-09-10.zip"


def origin_block() -> str:
    return (
        "> **Learn with Prof Rod** — *Build Your Always-On AI Agent From Scratch*.\n"
        "> **Read the full book and get the latest learning materials:** "
        f"[{BOOK_URL}]({BOOK_URL}).\n"
        f"> **Join the Prof Rod learner community:** [{COMMUNITY_URL}]({COMMUNITY_URL})\n"
        "> — bring your questions, compare experiments and share what you build.\n"
        f"> **Original source and updates:** [profrodai/sovereign-agent]({SOURCE_URL}).\n"
    )


def closing_block() -> str:
    return (
        "## Keep building with Prof Rod\n\n"
        "Found this material through a colleague, classroom or shared download? "
        f"[Get the complete book at profrod.ai/book]({BOOK_URL}) and "
        f"[join the Prof Rod learner community]({COMMUNITY_URL}). "
        "Bring one result, one question or one failure you learned from. "
        "Share this resource with another learner and keep its source links with it "
        "so they can find the full course and future updates.\n"
    )


def brand_markdown(source: str, *, closing: bool = True) -> str:
    assert "**Learn with Prof Rod**" not in source, "refuse duplicate attribution"
    heading = re.search(r"^# [^\n]+\n", source, re.M)
    assert heading is not None, "teaching document has no title"
    at = heading.end()
    source = source[:at] + "\n" + origin_block() + source[at:]
    return source.rstrip() + ("\n\n" + closing_block() if closing else "\n")


def verify_attribution(source: str) -> None:
    assert "**Learn with Prof Rod**" in source, "missing visible Prof Rod origin"
    assert "**Join the Prof Rod learner community:**" in source, "missing community invitation"
    for url in (BOOK_URL, COMMUNITY_URL, SOURCE_URL):
        assert f"]({url})" in source, f"missing clickable attribution link: {url}"


def verify_unique_names(book: Path) -> None:
    names: dict[str, Path] = {}
    for path in book.rglob("*"):
        if not path.is_file() or "__pycache__" in path.parts:
            continue
        if path.name == "README.md":
            assert path.parent == book or path.parent.parent == book, "generic chapter filename"
            continue
        if path.name == "BOOK.json":
            assert path == book / "textbook/BOOK.json"
            continue
        key = path.name.casefold()
        assert key not in names, f"shared filename collision: {path} and {names.get(key)}"
        names[key] = path
        assert path.name.startswith((PREFIX + "-", PREFIX.replace("-", "_") + "_")), (
            "teaching file lacks a discoverable book identity",
            path,
        )
