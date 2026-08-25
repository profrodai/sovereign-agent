"""The stdlib-only command-line entry point."""

from __future__ import annotations

import argparse
import importlib.metadata
import platform
import sys
from collections.abc import Sequence
from pathlib import Path

from sovereign_agent import __version__
from sovereign_agent.errors import Refusal
from sovereign_agent.models import Role
from sovereign_agent.organization import Organization
from sovereign_agent.providers import PROVIDERS


def _installed_version(distribution: str) -> str:
    try:
        return importlib.metadata.version(distribution)
    except importlib.metadata.PackageNotFoundError:
        return "not installed"


def _root(namespace: argparse.Namespace) -> Path:
    return Path(namespace.root).resolve()


def _doctor(_: argparse.Namespace) -> int:
    python_ok = sys.version_info >= (3, 14)
    pydantic_version = _installed_version("pydantic")
    pydantic_ok = pydantic_version != "not installed"
    print("Sovereign Agent doctor")
    print(f"  Python:   {platform.python_version()} {'OK' if python_ok else 'NEEDS 3.14+'}")
    print(f"  Pydantic: {pydantic_version} {'OK' if pydantic_ok else 'MISSING'}")
    print("  Network:  not required")
    print("  Tokens:   not required")
    print("  Providers:")
    for name, provider in PROVIDERS.items():
        caps = provider.probe()
        if caps.available:
            state = f"available {caps.version}".rstrip()
            if caps.degraded_reason:
                state += f"; degraded: {caps.degraded_reason}"
        elif caps.degraded_reason:
            state = f"degraded: {caps.degraded_reason}"
        else:
            state = "missing executable"
        extra = []
        if caps.streaming:
            extra.append("streaming")
        if caps.resume:
            extra.append("resume")
        if caps.workspace_selection:
            extra.append("workspace-selection")
        if caps.workspace_write:
            extra.append("workspace-write")
        if caps.sandbox:
            extra.append("sandbox")
        suffix = f" ({', '.join(extra)})" if extra else ""
        print(f"    {name:8} {state}{suffix}")
    if python_ok and pydantic_ok:
        print("Ready for the offline curriculum. Live providers are optional.")
        return 0
    if not python_ok:
        print("Next: install Python 3.14, then rerun `sovereign-agent doctor`.")
    else:
        print("Next: reinstall sovereign-agent so its sole runtime dependency is present.")
    return 1


def _init(namespace: argparse.Namespace) -> int:
    org = Organization.init(_root(namespace))
    print(f"Initialized {org.root}")
    return 0


def _actor_list(namespace: argparse.Namespace) -> int:
    org = Organization(_root(namespace))
    for actor in org.actors.values():
        print(f"{actor.id}\t{actor.role}\t{actor.provider}")
    return 0


def _outcome_new(namespace: argparse.Namespace) -> int:
    org = Organization(_root(namespace))
    outcome = org.create_outcome(
        namespace.title, namespace.desired, namespace.checks, namespace.owner
    )
    print(outcome.id)
    return 0


def _plan(namespace: argparse.Namespace) -> int:
    org = Organization(_root(namespace))
    org.activate(namespace.outcome_id, namespace.actor)
    sow = org.create_sow(
        namespace.outcome_id, namespace.scope, Role(namespace.role), namespace.actor
    )
    org.ready_sow(sow.id)
    print(sow.id)
    return 0


def _run(namespace: argparse.Namespace) -> int:
    org = Organization(_root(namespace))
    assignment = org.assign(namespace.sow_id, namespace.actor, namespace.planner)
    assignment = org.run_assignment(assignment.id)
    print(f"{assignment.id} {assignment.state}")
    return 0


def _status(namespace: argparse.Namespace) -> int:
    print(Organization(_root(namespace)).status_text(namespace.outcome_id))
    return 0


def _inbox(namespace: argparse.Namespace) -> int:
    for message in Organization(_root(namespace)).inbox(namespace.actor_id):
        print(f"{message.id} {message.state} {message.subject}")
    return 0


def _ruling_decide(namespace: argparse.Namespace) -> int:
    ruling = Organization(_root(namespace)).rule(
        namespace.question, namespace.decision, namespace.actor, namespace.applies_to
    )
    print(ruling.id)
    return 0


def _verify(namespace: argparse.Namespace) -> int:
    org = Organization(_root(namespace))
    outcome = org.verify_outcome(namespace.outcome_id, namespace.actor)
    print(outcome.state)
    return 0


def _accept(namespace: argparse.Namespace) -> int:
    org = Organization(_root(namespace))
    acceptance = org.accept(
        namespace.outcome_id, namespace.actor, namespace.performer, namespace.evidence
    )
    print(f"ACCEPTED {acceptance.outcome_id}")
    return 0


def _demo(namespace: argparse.Namespace) -> int:
    from reference_organizations.store.demo import run_simulated

    if namespace.target != "store" or namespace.mode != "simulated":
        print("Only `demo store --mode simulated` is implemented in this unit.")
        return 1
    text = run_simulated(_root(namespace))
    print(text)
    if "ACCEPTED" in text:
        print("outcome ACCEPTED")
        return 0
    return 1


def build_parser() -> argparse.ArgumentParser:
    shared = argparse.ArgumentParser(add_help=False)
    shared.add_argument("--root", default=".", help="organization directory")
    parser = argparse.ArgumentParser(
        prog="sovereign-agent",
        description="Learn how outcomes become governed, evidence-backed work.",
        parents=[shared],
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    subparsers = parser.add_subparsers(dest="command", required=True)

    doctor = subparsers.add_parser(
        "doctor", parents=[shared], help="check the offline learning environment"
    )
    doctor.set_defaults(handler=_doctor)

    init = subparsers.add_parser(
        "init", parents=[shared], help="create sovereign.toml and the local ledger"
    )
    init.set_defaults(handler=_init)

    actor = subparsers.add_parser("actor", parents=[shared], help="inspect actors")
    actor_sub = actor.add_subparsers(dest="actor_command", required=True)
    listed = actor_sub.add_parser("list", parents=[shared])
    listed.set_defaults(handler=_actor_list)

    outcome = subparsers.add_parser("outcome", parents=[shared], help="define outcomes")
    outcome_sub = outcome.add_subparsers(dest="outcome_command", required=True)
    created = outcome_sub.add_parser("new", parents=[shared])
    created.add_argument("title")
    created.add_argument("--desired", default="The outcome's acceptance checks pass.")
    created.add_argument("--checks", nargs="*", default=["evidence_present"])
    created.add_argument("--owner", default="principal-human")
    created.set_defaults(handler=_outcome_new)

    plan = subparsers.add_parser("plan", parents=[shared], help="activate an outcome and add a SOW")
    plan.add_argument("outcome_id")
    plan.add_argument("--scope", default="Advance the outcome by one bounded assignment")
    plan.add_argument("--role", default="operator")
    plan.add_argument("--actor", default="master-course")
    plan.set_defaults(handler=_plan)

    run = subparsers.add_parser("run", parents=[shared], help="assign and invoke one actor")
    run.add_argument("sow_id")
    run.add_argument("--actor", default="operator-course")
    run.add_argument("--planner", default="master-course")
    run.set_defaults(handler=_run)

    status = subparsers.add_parser("status", parents=[shared], help="explain outcome and SOW state")
    status.add_argument("outcome_id")
    status.set_defaults(handler=_status)

    inbox = subparsers.add_parser("inbox", parents=[shared], help="list an actor's durable mailbox")
    inbox.add_argument("actor_id")
    inbox.set_defaults(handler=_inbox)

    ruling = subparsers.add_parser("ruling", parents=[shared], help="record a decision")
    ruling_sub = ruling.add_subparsers(dest="ruling_command", required=True)
    decide = ruling_sub.add_parser("decide", parents=[shared])
    decide.add_argument("question")
    decide.add_argument("--decision", required=True)
    decide.add_argument("--actor", default="principal-human")
    decide.add_argument("--applies-to", dest="applies_to", default="organization")
    decide.set_defaults(handler=_ruling_decide)

    verify = subparsers.add_parser(
        "verify", parents=[shared], help="run deterministic verification"
    )
    verify.add_argument("outcome_id")
    verify.add_argument("--actor", default="verifier-course")
    verify.set_defaults(handler=_verify)

    accept = subparsers.add_parser(
        "accept", parents=[shared], help="accept an outcome under authority"
    )
    accept.add_argument("outcome_id")
    accept.add_argument("--actor", default="principal-human")
    accept.add_argument("--performer", default="operator-course")
    accept.add_argument("--evidence", nargs="+", required=True)
    accept.set_defaults(handler=_accept)

    demo = subparsers.add_parser("demo", parents=[shared], help="run a scripted teaching scenario")
    demo.add_argument("target", choices=["store"])
    demo.add_argument("--mode", default="simulated", choices=["simulated"])
    demo.set_defaults(handler=_demo)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    namespace = build_parser().parse_args(argv)
    try:
        return int(namespace.handler(namespace))
    except Refusal as error:
        print(error)
        print(f"Next: {error.next_command}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
