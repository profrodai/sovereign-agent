"""One compact, offline scenario exercising all six advanced mechanisms."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from pathlib import Path

from sovereign_agent.automation import WatchDecision, create_automation, run_due
from sovereign_agent.context import append_message, compact_one, render_context
from sovereign_agent.coordination import claim_session, register_host
from sovereign_agent.ids import new_id
from sovereign_agent.isolation import IsolationPolicy
from sovereign_agent.memory import recall, remember
from sovereign_agent.organization import Organization
from sovereign_agent.tools import Tool, ToolCatalog


def run_advanced(root: Path) -> str:
    """Return stable observations; random record ids deliberately stay hidden."""
    org = Organization.init(root)
    now = datetime(2026, 9, 5, tzinfo=UTC)
    workspace = root / "workspace"
    workspace.mkdir(exist_ok=True)
    policy = IsolationPolicy(
        filesystem_roots=(workspace,),
        network_hosts=frozenset({"inventory.example"}),
        credential_names=frozenset({"INVENTORY_TOKEN"}),
        allowed_tools=frozenset({"read_inventory"}),
    )
    isolation = ", ".join(f"{item.plane}={item.verdict}" for item in policy.explain())

    catalog = ToolCatalog(
        [
            Tool("read_inventory", "read stock levels", ("stock",)),
            Tool("delete_inventory", "delete stock rows", ("stock",)),
        ]
    )
    discovery = catalog.discover("read stock", limit=1)
    discovered = discovery.tools[0]
    authorized = catalog.authorize(discovered, policy).name

    automation_id = new_id("auto")
    create_automation(
        org.db, automation_id, interval_seconds=60, payload="inspect stock", first_run_at=now
    )
    no_fire = run_due(
        org.db,
        automation_id,
        lambda _state: WatchDecision(False, "stock healthy", {"on_hand": 8}),
        lambda _run_id, _message: None,
        now=now,
    )

    session_id = new_id("session")
    for role, content in (
        ("system", "Keep the shop governed."),
        ("user", "Check vanilla stock."),
        ("assistant", "I inspected the catalog."),
        ("tool", "Vanilla has eight tubs."),
        ("user", "Keep my correction verbatim."),
        ("assistant", "The recent answer stays visible."),
        ("tool", "Recent tool result."),
    ):
        append_message(org.db, session_id, role, content)
    compact_one(
        org.db,
        session_id,
        lambda _prior, exchange: (
            "Catalog inspected; vanilla has eight tubs." if len(exchange) == 2 else ""
        ),
    )
    context = render_context(org.db, session_id)

    host_a, host_b = new_id("host"), new_id("host")
    register_host(org.db, host_a, now=now, ttl_seconds=10)
    register_host(org.db, host_b, now=now + timedelta(seconds=20))
    first = claim_session(org.db, session_id, host_a, now=now, ttl_seconds=10)
    second = claim_session(org.db, session_id, host_b, now=now + timedelta(seconds=20))

    remember(org.db, new_id("memory"), "Vanilla reorder point is six", embedding=(1.0, 0.0))
    remember(
        org.db,
        new_id("memory"),
        "Chocolate supplier note",
        visibility="actor:other",
        embedding=(0.0, 1.0),
    )
    memories = recall(
        org.db, "vanilla reorder", actor_id="lucy", query_embedding=(1.0, 0.0), now=now
    )
    tools_line = (
        f"tools: discovered={discovered.name} authorized={authorized} "
        f"truncated={discovery.truncated}"
    )
    context_line = (
        f"context: source=7 rendered={len(context)} "
        f"summaries={sum(item.derived for item in context)}"
    )
    report = "\n".join(
        (
            f"isolation: {isolation}",
            tools_line,
            f"automation: {no_fire.status}, runs=0, state persisted",
            context_line,
            f"coordination: incarnation {first.incarnation}->{second.incarnation}",
            f"memory: visible={len(memories)} semantic={memories[0].semantic_status}",
        )
    )
    org.db.connection.close()
    return report
