"""Small command surface for the cumulative always-on teaching implementation."""

from __future__ import annotations

import argparse
import json
import os
import signal
import sys
import threading
import time
import uuid
from pathlib import Path
from typing import Any

from sovereign_agent import assistant_context, assistant_orders, assistant_service, assistant_work
from sovereign_agent.agent_loop import Limits
from sovereign_agent.database import Database
from sovereign_agent.model_turn import HTTPModel, Model
from sovereign_agent.telegram_channel import Telegram, deliver_one, poll


def handle(args: argparse.Namespace) -> int:
    from sovereign_agent import research as investigations

    root = Path(args.root).resolve()
    investigations.check_root(root, args.profile)
    if args.profile == "research":
        return handle_research(args, root)
    if args.action in {
        "pause",
        "resume",
        "redirect",
        "allow",
        "release-inference",
        "recover",
        "attach-paper",
        "paper-card",
    }:
        raise ValueError("action requires the research profile")
    from reference_organizations.store.account_recovery import configured_supplier
    from reference_organizations.store.agent import OfflineShopModel, seed_lucy
    from reference_organizations.store.assistant import reconcile_once, run_once
    from reference_organizations.store.extra_tools import Sandbox, optional_tools
    from reference_organizations.store.stock_conditions import disable, scan, watch

    root = Path(args.root).resolve()
    root.mkdir(parents=True, exist_ok=True, mode=0o700)
    db = Database(root / "agent.sqlite")
    seed_lucy(db)
    operators = frozenset(
        item for item in os.environ.get("SOVEREIGN_AGENT_OPERATORS", "lucy").split(",") if item
    )
    policy = assistant_orders.SpendingPolicy(
        operators, total_cents=args.total_cents, automatic_order_cents=args.automatic_cents
    )
    model: Model = OfflineShopModel()
    if args.live or os.environ.get("SOVEREIGN_AGENT_MODEL_MODE") == "live":
        model = HTTPModel(
            os.environ.get("SOVEREIGN_AGENT_LLM_BASE_URL", "http://localhost:11434/v1"),
            os.environ.get("SOVEREIGN_AGENT_LLM_MODEL", "qwen3"),
            os.environ.get("SOVEREIGN_AGENT_LLM_API_KEY", ""),
            reasoning_effort=None
            if args.reasoning_effort == "provider-default"
            else args.reasoning_effort,
        )
    endpoint = args.supplier or os.environ.get("SOVEREIGN_AGENT_SUPPLIER", "")
    supplier = (
        configured_supplier(db, endpoint)
        if endpoint
        and not args.research_worker
        and args.action
        in {
            "ask",
            "work",
            "serve",
            "approve",
            "bind-supplier",
            "inspect-account",
            "recover-account",
        }
        else None
    )
    limits = Limits(
        estimated_call_cents=args.estimated_call_cents, model_budget_cents=args.model_budget_cents
    )
    sandbox = None
    if args.sandbox_report:
        sandbox = Sandbox(
            os.environ.get("SOVEREIGN_AGENT_SANDBOX_IMAGE", ""),
            Path(os.environ.get("SOVEREIGN_AGENT_SANDBOX_SCRATCH", str(root / "sandbox"))),
            os.environ.get("SOVEREIGN_AGENT_DOCKER_HOST"),
        )
    edges = tuple(optional_tools(db, mcp_catalog=args.mcp_catalog, sandbox=sandbox))
    result: Any = {"status": "INITIALIZED", "root": str(root)}
    action = args.action
    if action == "bind-supplier":
        if supplier is None:
            raise ValueError("a simulated supplier endpoint is required")
        result = {"status": "BOUND", "target": supplier.identity, "account": supplier.account}
    elif action in {"inspect-account", "recover-account"}:
        from reference_organizations.store.account_recovery import inspect_account, recover

        if supplier is None:
            raise ValueError("the bound simulated supplier endpoint is required")
        if action == "inspect-account":
            result = inspect_account(db, supplier, actor=args.actor or "lucy", policy=policy)
        else:
            with Path(args.value).open("rb") as stream:
                raw = stream.read(262_145)
            result = recover(
                db, supplier, raw, args.digest, actor=args.actor or "lucy", policy=policy
            )
    elif action == "delegate":
        from reference_organizations.store.delegation import Inquiry, delegate

        result = {
            "status": "QUEUED",
            "work": delegate(
                db,
                args.value,
                Inquiry(sku=args.sku, guests=args.guests),
                deadline=args.deadline if args.deadline is not None else time.time() + 300,
                estimated_call_cents=args.estimated_call_cents,
                budget_cents=args.model_budget_cents,
            ),
        }
    elif action == "research-work":
        from reference_organizations.store.delegation import (
            OfflineCateringModel,
        )
        from reference_organizations.store.delegation import (
            run_once as research,
        )

        result = research(
            db,
            model if isinstance(model, HTTPModel) else OfflineCateringModel(),
            identifier=args.value,
        )
    elif action == "ask":
        identifier = assistant_work.enqueue(
            db, args.id or "local:" + uuid.uuid4().hex, args.session, args.value
        )
        result = {"work": identifier, "status": "QUEUED"}
        if not args.enqueue_only:
            result = run_once(
                db, model, policy=policy, supplier=supplier, limits=limits, extra_tools=edges
            )
    elif action == "work":
        assistant_work.tick(db)
        scan(db)
        result = run_once(
            db, model, policy=policy, supplier=supplier, limits=limits, extra_tools=edges
        )
    elif action == "watch-stock":
        identifier = args.id or "stock:" + args.value
        watch(
            db, identifier, args.session, args.value, channel=args.channel, recipient=args.recipient
        )
        result = {"status": "WATCHING", "condition": identifier, "subject": args.value}
    elif action == "unwatch-stock":
        disable(db, args.value)
        result = {"status": "DISABLED", "condition": args.value, "existing_work": "retained"}
    elif action == "receive":
        result = assistant_orders.receive(
            db, args.value, args.delivery_ref, actor=args.actor or "lucy", policy=policy
        )
    elif action == "schedule":
        assistant_work.schedule(
            db,
            args.id or "morning",
            args.session,
            args.value or "Prepare the morning replenishment brief.",
            first_due=args.first_due if args.first_due is not None else time.time(),
            interval_seconds=args.interval,
            channel=args.channel,
            recipient=args.recipient,
        )
        result = {
            "status": "SCHEDULED",
            "id": args.id or "morning",
            "timezone": "UTC",
            "missed_runs": "coalesce",
        }
    elif action == "unschedule":
        assistant_work.unschedule(db, args.value)
        result = {"status": "DISABLED", "job": args.value, "existing_work": "retained"}
    elif action == "report":
        from reference_organizations.store.operating_report import operating_report

        print(operating_report(db)["text"])
        return 0
    elif action == "status":
        result = assistant_service.health(db)
        result["items"] = [
            dict(row)
            for row in db.connection.execute(
                "SELECT id,status,result FROM assistant_work ORDER BY created DESC LIMIT 20"
            )
        ]
        result["orders"] = [
            dict(row)
            for row in db.connection.execute(
                "SELECT id,digest,amount,status,approved_until,revoked FROM assistant_orders "
                "ORDER BY created DESC LIMIT 20"
            )
        ]
    elif action in {"approve", "revoke"}:
        actor = args.actor or "lucy"
        if action == "approve":
            assistant_orders.approve(
                db,
                args.value,
                args.digest,
                actor=actor,
                policy=policy,
                expires=time.time() + args.approval_seconds,
                supplier=supplier,
            )
            with db.immediate() as connection:
                connection.execute(
                    "UPDATE assistant_work SET status='READY',available_after=0 "
                    "WHERE status='BLOCKED' "
                    "AND id=(SELECT work_id FROM assistant_orders WHERE id=?)",
                    (args.value,),
                )
        else:
            assistant_orders.revoke(db, args.value, actor=actor, policy=policy)
        result = {"status": action.upper(), "order": args.value}
    elif action == "resolve-order":
        with Path(args.receipt).open("rb") as stream:
            raw = stream.read(65_537)
        if len(raw) > 65_536:
            raise ValueError("receipt exceeds 64 KiB")
        result = assistant_orders.resolve(
            db,
            args.value,
            args.digest,
            json.loads(raw),
            target=args.supplier,
            evidence=args.evidence,
            actor=args.actor or "lucy",
            policy=policy,
        )
    elif action == "retry":
        with db.immediate() as connection:
            changed = connection.execute(
                "UPDATE assistant_work SET status='READY',available_after=0 "
                "WHERE id=? AND status='BLOCKED'",
                (args.value,),
            ).rowcount
        result = {"status": "READY" if changed else "UNCHANGED"}
    elif action == "cancel":
        assistant_work.cancel(db, args.value)
        result = {"status": "CANCELED"}
    elif action == "remember":
        result = {
            "revision": assistant_context.remember(
                db, args.session, args.key, args.value, "local-operator:" + (args.actor or "lucy")
            )
        }
    elif action == "forget":
        assistant_context.forget(db, args.session, args.key)
        result = {"status": "FORGOTTEN"}
    elif action == "backup":
        result = {"backup": str(assistant_service.backup(db, Path(args.value)))}
    elif action == "restore":
        assistant_service.restore(db, Path(args.value))
        result = {
            "status": "PAUSED",
            "reason": "Restored state requires external reconciliation and renewed authority.",
        }
    elif action == "evaluate":
        from reference_organizations.store.evaluation import evaluate
        from reference_organizations.store.improvement import save_report

        baseline, active = assistant_context.skill_snapshot(db)
        report = evaluate(lambda: model, skills=active, repeats=args.repeats, limits=limits)
        report["active_skill_state"] = baseline
        path, digest = save_report(root / "evaluations", report)
        result = {
            "passed": report["passed"],
            "acceptance": report["acceptance"]["status"],
            "report": str(path),
            "sha256": digest,
        }
    elif action == "skill-stage":
        skill = assistant_context.stage_skill(db, Path(args.value))
        result = {"status": "STAGED", "name": skill.name, "version": skill.version}
    elif action in {"skill-activate", "skill-rollback"}:
        from reference_organizations.store.improvement import change_skill

        result = change_skill(
            db,
            args.value,
            args.version,
            lambda: model,
            root / "evaluations",
            repeats=args.repeats,
            rollback=action == "skill-rollback",
            model_label="live HTTP model" if isinstance(model, HTTPModel) else "offline fixture",
        )
    elif action == "service":
        result = assistant_service.service(
            args.value,
            root,
            Path(sys.executable).with_name("sovereign-agent"),
            research=args.research_worker,
        )
    elif action == "serve":
        stop = threading.Event()
        for sig in (signal.SIGINT, signal.SIGTERM):
            signal.signal(sig, lambda *_: stop.set())
        token = os.environ.get("SOVEREIGN_AGENT_TELEGRAM_TOKEN", "")
        bot = Telegram(token) if token and not args.research_worker else None
        numeric = frozenset(int(actor) for actor in operators if actor.isdigit())
        if bot and (not numeric or len(numeric) != len(operators)):
            raise ValueError("Telegram requires numeric SOVEREIGN_AGENT_OPERATORS")
        failures = 0
        while not stop.is_set():
            try:
                if args.research_worker:
                    from reference_organizations.store.delegation import (
                        OfflineCateringModel,
                    )
                    from reference_organizations.store.delegation import (
                        run_once as research,
                    )

                    item = research(
                        db,
                        model if isinstance(model, HTTPModel) else OfflineCateringModel(),
                        should_stop=stop.is_set,
                    )
                    print(
                        json.dumps({"status": item["status"], "work": item.get("work")}), flush=True
                    )
                    failures = 0
                    stop.wait(1)
                    continue
                uncertain = db.connection.execute(
                    "SELECT count(*) FROM assistant_orders WHERE status IN ('UNKNOWN','SENDING')"
                ).fetchone()[0]
                if uncertain:
                    item = (
                        reconcile_once(db, supplier, policy, should_stop=stop.is_set)
                        if supplier
                        else {"status": "RECOVERY_NEEDS_SUPPLIER"}
                    )
                    # An unresolved supplier must not make the operator's revoke
                    # and cancel commands unreachable. Ordinary turns stay held.
                    if bot and not stop.is_set():
                        poll(db, bot, numeric)
                        if not stop.is_set():
                            run_once(
                                db,
                                model,
                                policy=policy,
                                supplier=supplier,
                                limits=limits,
                                should_stop=stop.is_set,
                                extra_tools=edges,
                                control_only=True,
                            )
                else:
                    if bot:
                        poll(db, bot, numeric)
                    if stop.is_set():
                        break
                    assistant_work.tick(db)
                    scan(db)
                    item = run_once(
                        db,
                        model,
                        policy=policy,
                        supplier=supplier,
                        limits=limits,
                        should_stop=stop.is_set,
                        extra_tools=edges,
                    )
                if bot and not stop.is_set():
                    deliver_one(db, bot, numeric)
                # Logs describe work state, never prompts or channel credentials.
                print(json.dumps({"status": item["status"], "work": item.get("work")}), flush=True)
                failures = 0
            except (OSError, ValueError):
                failures = min(failures + 1, 5)
                print(json.dumps({"status": "RETRY_WAIT", "attempt": failures}), flush=True)
            stop.wait(min(60, 2**failures) if failures else 1)
        result = {"status": "STOPPED"}
    print(json.dumps(result, indent=2, default=str))
    return 1 if isinstance(result, dict) and result.get("passed") is False else 0


def handle_research(args: argparse.Namespace, root: Path) -> int:
    from sovereign_agent import research

    db = research.open_agent(root)
    result: Any = {"status": "INITIALIZED", "database": str(db.path)}
    if args.action in {"ask", "redirect"}:
        if args.action == "redirect" and not args.id:
            raise ValueError("redirect requires --id")
        result = {"investigation": research.revise(db, args.value, args.id)}
    elif args.action == "attach-paper":
        result = {
            "investigation": research.attach_paper(
                db, root, args.id, args.value, args.digest, args.evidence
            )
        }
    elif args.action == "paper-card":
        from sovereign_agent import paper_assessment

        result = paper_assessment.private_report(
            db, args.id, research.head(db, args.id)["revision"]
        )
    elif args.action == "allow":
        from sovereign_agent import paper_assessment
        from sovereign_agent import research_allowance as allowance

        with db.immediate():
            attached = paper_assessment.binding(db, args.id)
            exists = db.connection.execute(
                "SELECT 1 FROM research_campaigns WHERE id=?", (args.key,)
            ).fetchone()
            if attached and not exists:
                paper_assessment.check_allocations(
                    db,
                    args.id,
                    paper_assessment.baseline(db, args.id)["first_campaign"],
                    {
                        "seconds": args.campaign_seconds,
                        "calls": args.campaign_calls,
                        "tokens": args.campaign_tokens,
                        "actions": args.campaign_actions,
                        "evaluations": args.campaign_evaluations,
                    },
                )
            result = {
                "campaign": allowance.grant(
                    db,
                    args.id,
                    args.key,
                    args.campaign_seconds,
                    args.evidence,
                    {
                        "calls": args.campaign_calls,
                        "tokens": args.campaign_tokens,
                        "actions": args.campaign_actions,
                        "evaluations": args.campaign_evaluations,
                    },
                )
            }
    elif args.action == "release-inference":
        from sovereign_agent import research_allowance as allowance

        if not args.evidence or args.value != "no-inference":
            raise ValueError("explicit no-inference assertion and evidence required")
        with db.immediate() as connection:
            lease = connection.execute("SELECT * FROM research_profile WHERE id=1").fetchone()
            if lease["inference_owner"] and lease["inference_until"] > time.time():
                raise PermissionError("cannot release while inference ownership is live")
            allowance.settle(db, args.key, 0, "operator no-inference evidence: " + args.evidence)
        result = {"status": "RELEASED", "reservation": args.key}
    elif args.action == "recover":
        research.recover(db, root, args.key, args.evidence)
        result = {"status": "RECORDED", "operation": args.key}
    elif args.action == "cancel" and args.key:
        research.cancel_operation(db, root, args.key)
        result = {"status": "CANCELLATION_REQUESTED", "operation": args.key}
    elif args.action in {"pause", "resume", "cancel"}:
        research.control(db, args.id, args.action)
        result = research.context(db, args.id)
    elif args.action in {"status", "report"}:
        result = (
            research.context(db, args.id)
            if args.id
            else [dict(row) for row in db.connection.execute("SELECT * FROM investigations")]
        )
        if args.action == "report":
            result = research.history(db, args.id, redact_paper=True)
    elif args.action in {"work", "serve"}:
        model: Model | None = None
        if args.live:
            if args.research_provider == "claude-subscription":
                from sovereign_agent.research_model import SubscriptionModel

                model = SubscriptionModel(root)
            else:
                model = research_http_model(args)
        stop = threading.Event()
        if args.action == "serve":
            for signum in (signal.SIGTERM, signal.SIGINT):
                signal.signal(signum, lambda *_: stop.set())
        owner = uuid.uuid4().hex
        while True:
            result = {"status": research.wake(db, root, model, owner=owner)}
            if args.action == "serve":
                print(json.dumps(result), flush=True)
            if args.action == "work" or stop.wait(1):
                break
    elif args.action != "init":
        raise ValueError("action is not supported by the research profile")
    print(json.dumps(result, indent=2, default=str))
    return 0


def research_http_model(args: argparse.Namespace) -> Model:
    name = os.environ.get("SOVEREIGN_AGENT_LLM_MODEL", "")
    if not name:
        raise ValueError("research requires an explicit authorized model configuration")
    return HTTPModel(
        os.environ.get("SOVEREIGN_AGENT_LLM_BASE_URL", "http://localhost:11434/v1"),
        name,
        os.environ.get("SOVEREIGN_AGENT_LLM_API_KEY", ""),
        reasoning_effort=None
        if args.reasoning_effort == "provider-default"
        else args.reasoning_effort,
    )


def register(subparsers: Any, shared: argparse.ArgumentParser) -> None:
    parser = subparsers.add_parser(
        "agent", parents=[shared], help="build and operate Lucy's always-on teaching agent"
    )
    parser.add_argument(
        "action",
        choices=[
            "init",
            "pause",
            "resume",
            "redirect",
            "allow",
            "release-inference",
            "recover",
            "ask",
            "work",
            "delegate",
            "research-work",
            "attach-paper",
            "paper-card",
            "watch-stock",
            "unwatch-stock",
            "receive",
            "schedule",
            "unschedule",
            "status",
            "report",
            "approve",
            "revoke",
            "resolve-order",
            "retry",
            "cancel",
            "remember",
            "forget",
            "backup",
            "restore",
            "bind-supplier",
            "inspect-account",
            "recover-account",
            "service",
            "serve",
            "evaluate",
            "skill-stage",
            "skill-activate",
            "skill-rollback",
        ],
    )
    parser.add_argument("value", nargs="?", default="")
    parser.add_argument("--profile", choices=["shop", "research"], default="shop")
    parser.add_argument(
        "--research-provider", choices=["http", "claude-subscription"], default="http"
    )
    parser.add_argument("--campaign-seconds", type=int, default=600)
    parser.add_argument("--campaign-calls", type=int, default=12)
    parser.add_argument("--campaign-tokens", type=int, default=12000)
    parser.add_argument("--campaign-actions", type=int, default=24)
    parser.add_argument("--campaign-evaluations", type=int, default=12)
    parser.add_argument("--session", default="lucy")
    parser.add_argument(
        "--research-worker",
        action="store_true",
        help="serve or install the separate read-only catering worker",
    )
    parser.add_argument("--sku", default="SKU-VANILLA")
    parser.add_argument("--guests", type=int, default=40)
    parser.add_argument("--deadline", type=float, help="absolute epoch UTC delegation deadline")
    parser.add_argument(
        "--channel", default="local", help="output route for schedules and stock watches"
    )
    parser.add_argument(
        "--recipient", default="", help="operator chat ID for a Telegram output route"
    )
    parser.add_argument("--id", default="")
    parser.add_argument("--key", default="")
    parser.add_argument("--version", default="")
    parser.add_argument("--repeats", type=int, default=1)
    parser.add_argument("--actor", default="")
    parser.add_argument("--digest", default="")
    parser.add_argument("--delivery-ref", default="")
    parser.add_argument("--receipt", default="")
    parser.add_argument("--evidence", default="")
    parser.add_argument("--approval-seconds", type=int, default=3600)
    parser.add_argument("--total-cents", type=int, default=20_000)
    parser.add_argument("--automatic-cents", type=int, default=0)
    parser.add_argument("--interval", type=int, default=86400)
    parser.add_argument("--first-due", type=float)
    parser.add_argument("--supplier", default="")
    parser.add_argument("--enqueue-only", action="store_true")
    parser.add_argument("--live", action="store_true")
    parser.add_argument("--mcp-catalog", action="store_true")
    parser.add_argument("--sandbox-report", action="store_true")
    parser.add_argument("--estimated-call-cents", type=int, default=0)
    parser.add_argument("--model-budget-cents", type=int, default=100)
    parser.add_argument(
        "--reasoning-effort",
        default="none",
        choices=["none", "low", "medium", "high", "max", "provider-default"],
        help="explicit Ollama teaching setting; provider-default omits the field",
    )
    parser.set_defaults(handler=handle)
