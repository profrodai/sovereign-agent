"""Bounded subprocess invocation. Never uses shell=True."""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path

from sovereign_agent.errors import Refusal
from sovereign_agent.ids import new_id, utc_now
from sovereign_agent.models import Actor, ActorReport, Receipt, StatementOfWork
from sovereign_agent.providers import get_provider
from sovereign_agent.providers.base import InvocationRequest, InvocationSpec


def run_spec(spec: InvocationSpec, timeout: float = 60.0) -> subprocess.CompletedProcess[str]:
    argv = list(spec.argv)
    if argv and argv[0] == "python":
        argv[0] = sys.executable
    env = {key: os.environ[key] for key in ("PATH", "HOME", "LANG", "LC_ALL") if key in os.environ}
    env.update(spec.env)
    try:
        return subprocess.run(
            argv,
            cwd=spec.cwd,
            env=env,
            check=False,
            capture_output=True,
            text=True,
            timeout=timeout,
            shell=False,
        )
    except subprocess.TimeoutExpired as error:
        raise Refusal(
            happened="Provider timed out.",
            why="A hung provider must not be treated as completion.",
            inspect=str(spec.cwd),
            next_command="Retry with a smaller assignment or inspect provider-raw logs.",
            category="timeout",
        ) from error
    except OSError as error:
        raise Refusal(
            happened="Provider process could not start.",
            why=str(error),
            inspect=str(spec.cwd),
            next_command="Run sovereign-agent doctor and inspect the executable.",
            category="invocation_error",
        ) from error


def build_assignment_envelope(
    actor: Actor,
    sow: StatementOfWork,
    workspace: Path,
    output: Path,
) -> str:
    """Build the provider-neutral governed assignment passed to every CLI."""
    envelope = {
        "kind": "sovereign-agent.assignment.v1",
        "actor": {
            "id": actor.id,
            "role": actor.role,
            "authority": actor.authority,
        },
        "statement_of_work": sow.model_dump(mode="json"),
        "workspace": {
            "root": str(workspace),
            "boundary": "Do not read or write outside this disposable workspace.",
        },
        "output": {
            "directory": str(output),
            "report": str(output / "report.json"),
            "artifacts": str(output / "artifacts.json"),
            "messages": str(output / "messages"),
        },
        "report_contract": {
            "schema": ActorReport.model_json_schema(),
            "required_action": (
                "Before exiting, write report.json as strict JSON matching this schema. "
                "Use status completed, blocked, or failed. Do not claim authority the actor lacks."
            ),
        },
    }
    return json.dumps(envelope, sort_keys=True)


def canonical_receipt_json(receipt: Receipt) -> str:
    return json.dumps(
        receipt.model_dump(mode="json"),
        sort_keys=True,
        separators=(",", ":"),
    ) + "\n"


def write_receipt(workspace: Path, receipt: Receipt) -> str:
    receipt_json = canonical_receipt_json(receipt)
    receipt_path = workspace / "receipt.json"
    receipt_path.write_text(receipt_json, encoding="utf-8")
    digest = hashlib.sha256(receipt_json.encode()).hexdigest()
    (workspace / "receipt.json.sha256").write_text(f"{digest}\n", encoding="utf-8")
    return receipt_json


def write_failed_receipt(
    actor: Actor,
    workspace: Path,
    category: str,
    message: str,
    started_at: datetime | None = None,
) -> Receipt:
    receipt = Receipt(
        id=new_id("rct"),
        actor_id=actor.id,
        provider=actor.provider,
        provider_session_ref=None,
        provider_usage={},
        started_at=started_at or utc_now(),
        ended_at=utc_now(),
        status="failed",
        failure_category=category,
        failure_message=message,
        evidence_refs=[],
    )
    write_receipt(workspace, receipt)
    return receipt


def invoke_actor(
    actor: Actor,
    sow: StatementOfWork,
    workspace: Path,
    output: Path,
    provider_session_id: str | None = None,
) -> tuple[Receipt, ActorReport | None]:
    workspace_write = "write_workspace" in actor.authority
    if "report" not in actor.authority or not workspace_write:
        raise Refusal(
            "Actor cannot write the mandatory report.",
            "Every provider assignment must be authorized to write inside its run workspace.",
            actor.id,
            "Assign an actor with report and write_workspace authority.",
            category="authority_refusal",
        )
    provider = get_provider(actor.provider)
    capabilities = provider.probe()
    if not capabilities.available:
        raise Refusal(
            "Provider unavailable.",
            "Fail closed on missing executables.",
            "sovereign-agent doctor",
            "Install the CLI or use scripted.",
            category="provider_unavailable",
        )
    envelope = build_assignment_envelope(actor, sow, workspace, output)
    spec = provider.build_invocation(
        InvocationRequest(
            workspace=workspace,
            output=output,
            prompt=envelope,
            require_resume=provider_session_id is not None,
            require_sandbox=actor.provider == "codex" and workspace_write,
            require_workspace_write=workspace_write,
            provider_session_id=provider_session_id,
        )
    )
    started = utc_now()
    result = run_spec(spec)
    ended = utc_now()
    raw = workspace / "provider-raw"
    raw.mkdir(parents=True, exist_ok=True)
    (raw / "stdout.txt").write_text(result.stdout)
    (raw / "stderr.txt").write_text(result.stderr)
    events = []
    malformed = False
    terminal: bool | None = None
    session_ref = provider_session_id
    usage: dict[str, int] = {}
    for line in result.stdout.splitlines():
        event = provider.parse_event(line)
        if event is not None:
            events.append(
                json.dumps(
                    {
                        "kind": event.kind,
                        "payload": event.payload,
                        "malformed": event.malformed,
                        "terminal": event.terminal,
                    },
                    sort_keys=True,
                )
            )
            malformed = malformed or event.malformed
            if event.terminal:
                terminal = event.succeeded
            if event.session_id:
                if session_ref is not None and session_ref != event.session_id:
                    malformed = True
                session_ref = event.session_id
            usage.update(event.usage)
    (raw / "events.jsonl").write_text("\n".join(events) + ("\n" if events else ""))
    report_path = output / "report.json"
    report: ActorReport | None = None
    status = "failed"
    failure_category: str | None = None
    failure_message: str | None = None
    protocol_ok = not malformed and (
        not provider.requires_terminal_event
        or (terminal is True and session_ref is not None)
    )
    if result.returncode == 0 and protocol_ok and report_path.is_file():
        try:
            report = ActorReport.model_validate_json(report_path.read_text(encoding="utf-8"))
            status = report.status
            if status == "failed":
                failure_category = "actor_reported_failure"
                failure_message = report.notes
        except Exception as error:
            failure_category = "invalid_report"
            failure_message = str(error)
    elif result.returncode != 0:
        failure_category = "nonzero_exit"
        failure_message = f"Provider exited with status {result.returncode}."
    elif malformed:
        failure_category = "malformed_stream"
        failure_message = "Provider emitted malformed structured output."
    elif provider.requires_terminal_event and terminal is not True:
        failure_category = "provider_error" if terminal is False else "missing_terminal"
        failure_message = "Provider did not emit a successful terminal event."
    elif provider.requires_terminal_event and session_ref is None:
        failure_category = "missing_session"
        failure_message = "Provider did not emit a session reference."
    elif not report_path.is_file():
        failure_category = "missing_report"
        failure_message = "Provider did not write the mandatory report."
    receipt = Receipt(
        id=new_id("rct"),
        actor_id=actor.id,
        provider=actor.provider,
        provider_session_ref=session_ref,
        provider_usage=usage,
        started_at=started,
        ended_at=ended,
        status=status,
        failure_category=failure_category,
        failure_message=failure_message,
        evidence_refs=[],
    )
    write_receipt(workspace, receipt)
    return receipt, report
