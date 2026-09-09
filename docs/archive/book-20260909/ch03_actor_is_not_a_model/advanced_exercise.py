"""Chapter 3 extension: compact context and discover tools without granting authority."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from sovereign_agent.context import append_message, compact_one, render_context
from sovereign_agent.errors import Refusal
from sovereign_agent.isolation import IsolationPolicy
from sovereign_agent.organization import Organization
from sovereign_agent.tools import Tool, ToolCatalog


def explore_context_and_tools(root: Path) -> dict[str, object]:
    org = Organization(root)
    for role, content in (
        ("system", "Never spend without authority."),
        ("user", "Check vanilla stock."),
        ("assistant", "I will inspect the catalog."),
        ("tool", "Vanilla has two tubs."),
        ("user", "Keep that observation verbatim."),
        ("assistant", "The recent answer stays in full."),
        ("tool", "Recent receipt."),
    ):
        append_message(org.db, "lesson", role, content)

    compacted = compact_one(
        org.db,
        "lesson",
        lambda prior, exchange: (
            prior + "Earlier exchange: " + " | ".join(item.content for item in exchange)
        ),
    )
    rendered = render_context(org.db, "lesson")
    source_count = org.db.connection.execute(
        "SELECT COUNT(*) FROM transcript_messages WHERE session_id = 'lesson'"
    ).fetchone()[0]

    catalog = ToolCatalog(
        [
            Tool("read_inventory", "read stock levels", ("stock",)),
            Tool("delete_inventory", "delete stock rows", ("stock",)),
            Tool("email_supplier", "notify a supplier", ("mail",)),
        ]
    )
    discovery = catalog.discover("delete stock", limit=1)
    policy = IsolationPolicy(
        allowed_tools=frozenset({"read_inventory", "delete_inventory"}),
        denied_tools=frozenset({"delete_inventory"}),
    )
    try:
        catalog.authorize(discovery.tools[0], policy)
        authorization = "ALLOWED (this would be a bug)"
    except Refusal:
        authorization = "REFUSED"

    return {
        "context": {
            "compacted": compacted,
            "source_rows": source_count,
            "rendered_rows": len(rendered),
            "derived_rows": sum(item.derived for item in rendered),
            "user_messages": [item.content for item in rendered if item.role == "user"],
        },
        "tools": {
            "discovered": discovery.tools[0].name,
            "total_matches": discovery.total_matches,
            "truncated": discovery.truncated,
            "authorization": authorization,
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    print(json.dumps(explore_context_and_tools(parser.parse_args().root), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
