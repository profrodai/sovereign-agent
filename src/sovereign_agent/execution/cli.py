"""Offline JSON CLI wiring for governed execution."""

from __future__ import annotations

import asyncio
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import typer

from sovereign_agent.contracts import (
    EvidenceLevel,
    FrozenDict,
    GovernedExecutionRequest,
    RelayMessageId,
    RepositoryId,
    SeatId,
    SeatInstanceId,
)
from sovereign_agent.orchestrator import (
    BareWorker,
    DockerWorker,
    OSIsolatedWorker,
    SubprocessWorker,
    WorkerOutcome,
)
from sovereign_agent.providers import (
    AgentProvider,
    ClaudeCodeProvider,
    CodexCliProvider,
    ProviderCapabilities,
)
from sovereign_agent.registry import RuntimeAddress, SeatRegistry
from sovereign_agent.relay import DurableRelay, RelayMessage
from sovereign_agent.repository import RepositoryConfig, RepositoryManager
from sovereign_agent.runtime import RuntimeRoot

from .engine import AdmissionRejected, ExecutionNotFound, GovernedExecutionEngine

governed_app = typer.Typer(
    name="governed",
    help="Run and inspect governed v0.3 executions using JSON.",
    no_args_is_help=True,
)
seat_app = typer.Typer(
    name="seat", help="Register persistent seat instances.", no_args_is_help=True
)
execution_app = typer.Typer(
    name="execution", help="Inspect execution status.", no_args_is_help=True
)
receipt_app = typer.Typer(
    name="receipt", help="Show finalized execution receipts.", no_args_is_help=True
)
relay_app = typer.Typer(
    name="relay", help="Send and receive durable relay messages.", no_args_is_help=True
)

EXIT_OK = 0
EXIT_INPUT = 2
EXIT_FAILED = 3
EXIT_NOT_FOUND = 4


@governed_app.command("run")
def run_command(
    request_file: Path = typer.Argument(..., exists=True, dir_okay=False),
    config_file: Path = typer.Option(..., "--config", exists=True, dir_okay=False),
) -> None:
    """Admit and run a request, printing exactly one JSON result."""
    _execute_request(request_file, config_file)


@governed_app.command("submit")
def submit_command(
    request_file: Path = typer.Argument(..., exists=True, dir_okay=False),
    config_file: Path = typer.Option(..., "--config", exists=True, dir_okay=False),
) -> None:
    """Offline submit-and-run alias; execution IDs make retries idempotent."""
    run_command(request_file, config_file)


@governed_app.command("status")
def governed_status_command(
    execution_id: str,
    config_file: Path = typer.Option(..., "--config", exists=True, dir_okay=False),
) -> None:
    """Print durable execution status as JSON."""
    _status(execution_id, config_file)


@governed_app.command("cancel")
def cancel_command(
    execution_id: str,
    config_file: Path = typer.Option(..., "--config", exists=True, dir_okay=False),
) -> None:
    """Persist cancellation and signal an execution-local Unit 3 token."""
    cancelled = _engine(config_file).cancel(execution_id)
    _json({"execution_id": execution_id, "cancellation_requested": cancelled})
    if not cancelled:
        raise typer.Exit(EXIT_NOT_FOUND)


@governed_app.command("receipt")
def governed_receipt_command(
    execution_id: str,
    config_file: Path = typer.Option(..., "--config", exists=True, dir_okay=False),
) -> None:
    """Print a finalized immutable receipt as JSON."""
    _show_receipt(execution_id, config_file)


def execute_command(
    request: Path = typer.Option(..., "--request", exists=True, dir_okay=False),
    config_file: Path = typer.Option(..., "--config", exists=True, dir_okay=False),
) -> None:
    """Admit and run a governed request file (JSON or YAML)."""
    _execute_request(request, config_file)


@execution_app.command("status")
def execution_status_command(
    execution_id: str,
    config_file: Path = typer.Option(..., "--config", exists=True, dir_okay=False),
) -> None:
    _status(execution_id, config_file)


@receipt_app.command("show")
def receipt_show_command(
    execution_id: str,
    config_file: Path = typer.Option(..., "--config", exists=True, dir_okay=False),
) -> None:
    _show_receipt(execution_id, config_file)


@seat_app.command("register")
def seat_register_command(
    instance: str = typer.Option(..., "--instance"),
    seat_type: str = typer.Option(..., "--seat-type"),
    provider: str = typer.Option(..., "--provider"),
    backend: str = typer.Option(..., "--backend"),
    config_file: Path = typer.Option(..., "--config", exists=True, dir_okay=False),
    sovereign_session: str | None = typer.Option(None, "--sovereign-session"),
    provider_session: str | None = typer.Option(None, "--provider-session"),
    capability_manifest_ref: str | None = typer.Option(None, "--capability-manifest-ref"),
) -> None:
    runtime = _runtime(config_file)
    registry = SeatRegistry(runtime)
    record = registry.register(
        instance_id=SeatInstanceId(instance),
        seat_id=SeatId(seat_type),
        provider=provider,
        backend=backend,
        sovereign_session_id=sovereign_session,
        provider_session_id=provider_session,
        capability_manifest_ref=capability_manifest_ref,
    )
    _json(record.to_dict())


@relay_app.command("send")
def relay_send_command(
    sender: str = typer.Option(..., "--from"),
    recipient: str = typer.Option(..., "--to"),
    kind: str = typer.Option(..., "--kind"),
    config_file: Path = typer.Option(..., "--config", exists=True, dir_okay=False),
    body: str = typer.Option("", "--body"),
    message_id: str | None = typer.Option(None, "--message-id"),
    conversation_id: str | None = typer.Option(None, "--conversation-id"),
    artifact_ref: list[str] = typer.Option((), "--artifact-ref"),
) -> None:
    runtime = _runtime(config_file)
    registry = SeatRegistry(runtime)
    relay = DurableRelay(runtime, registry)
    envelope = RelayMessage(
        message_id=RelayMessageId(message_id or f"msg-{int(datetime.now(UTC).timestamp())}"),
        sender=RuntimeAddress(sender if sender.startswith("local://") else f"local://{sender}"),
        recipient=RuntimeAddress(
            recipient if recipient.startswith("local://") else f"local://{recipient}"
        ),
        kind=kind,
        payload=FrozenDict((("body", body),)),
        created_at=datetime.now(UTC),
        conversation_id=conversation_id,
        artifact_refs=tuple(artifact_ref),
    )
    _json(relay.enqueue(envelope).to_dict())


@relay_app.command("receive")
def relay_receive_command(
    recipient: str = typer.Option(..., "--to"),
    owner: str = typer.Option(..., "--owner"),
    config_file: Path = typer.Option(..., "--config", exists=True, dir_okay=False),
    ack: bool = typer.Option(False, "--ack"),
) -> None:
    runtime = _runtime(config_file)
    registry = SeatRegistry(runtime)
    relay = DurableRelay(runtime, registry)
    address = RuntimeAddress(
        recipient if recipient.startswith("local://") else f"local://{recipient}"
    )
    claimed = relay.claim(address, owner=owner)
    if claimed is None:
        _json({"claimed": False})
        raise typer.Exit(EXIT_NOT_FOUND)
    if ack:
        acknowledgement = relay.ack(
            claimed.message.message_id, owner=owner, lease_token=claimed.lease_token
        )
        _json(
            {
                "claimed": True,
                "message": claimed.message.to_dict(),
                "ack": acknowledgement.to_dict(),
            }
        )
        return
    _json(
        {
            "claimed": True,
            "message": claimed.message.to_dict(),
            "lease_token": claimed.lease_token,
            "attempt_count": claimed.attempt_count,
        }
    )


def register_execution_commands(app: typer.Typer) -> None:
    """Attach Unit 7 command names and keep the governed aliases."""
    app.add_typer(governed_app, name="governed")
    app.add_typer(seat_app, name="seat")
    app.add_typer(execution_app, name="execution")
    app.add_typer(receipt_app, name="receipt")
    app.add_typer(relay_app, name="relay")
    app.command("execute")(execute_command)


def _execute_request(request_file: Path, config_file: Path) -> None:
    try:
        request = GovernedExecutionRequest.from_dict(_read_object(request_file))
        engine = _engine(config_file)
        receipt = asyncio.run(engine.run(request))
    except AdmissionRejected as exc:
        _json({"admitted": False, "reason": exc.reason, "detail": exc.detail})
        raise typer.Exit(EXIT_INPUT) from exc
    except Exception as exc:  # noqa: BLE001
        _json({"error": type(exc).__name__, "detail": str(exc)})
        raise typer.Exit(EXIT_INPUT) from exc
    _json(receipt.to_dict())
    if not receipt.is_successful:
        raise typer.Exit(EXIT_FAILED)


def _status(execution_id: str, config_file: Path) -> None:
    try:
        _json(_engine(config_file).status(execution_id).to_dict())
    except ExecutionNotFound as exc:
        _json({"error": "not_found", "execution_id": execution_id})
        raise typer.Exit(EXIT_NOT_FOUND) from exc


def _show_receipt(execution_id: str, config_file: Path) -> None:
    receipt = _engine(config_file).receipt(execution_id)
    if receipt is None:
        _json({"error": "not_found", "execution_id": execution_id})
        raise typer.Exit(EXIT_NOT_FOUND)
    _json(receipt.to_dict())


def _engine(config_file: Path) -> GovernedExecutionEngine:
    config = _read_object(config_file)
    runtime = RuntimeRoot(Path(str(config["runtime_root"]))).initialize()
    repositories_raw = config.get("repositories", ())
    if not isinstance(repositories_raw, list):
        raise ValueError("config.repositories must be an array")
    repositories = tuple(
        RepositoryConfig(
            repository_id=RepositoryId(str(item["repository_id"])),
            checkout=Path(str(item["checkout"])),
            default_remote=str(item.get("default_remote", "origin")),
            protected_branches=tuple(item.get("protected_branches", ("main", "master"))),
        )
        for item in repositories_raw
    )
    providers: dict[str, AgentProvider] = {}
    providers_raw = config.get("providers", ())
    if not isinstance(providers_raw, list):
        raise ValueError("config.providers must be an array")
    for item in providers_raw:
        kind = str(item["kind"])
        kwargs = {
            "name": str(item.get("name", kind)),
            "executable": str(item.get("executable", kind)),
        }
        if kind == "claude":
            provider: AgentProvider = ClaudeCodeProvider(**kwargs)
        elif kind == "codex":
            provider = CodexCliProvider(**kwargs)
        elif kind == "native":
            raise ValueError(
                "native provider must be wired in-process with NativeProvider; "
                "JSON config cannot supply an LLM client"
            )
        else:
            raise ValueError(f"unsupported configured provider kind: {kind}")
        declared = item.get("capabilities")
        if isinstance(declared, dict):
            capability_values = dict(declared)
            level = capability_values.get("evidence_level")
            if isinstance(level, str):
                capability_values["evidence_level"] = EvidenceLevel.from_wire(level)
            provider.capabilities = ProviderCapabilities(**capability_values)
        providers[provider.name] = provider

    async def unused_advance(session_id: str, session_dir: Path) -> WorkerOutcome:
        del session_dir
        return WorkerOutcome(session_id, False, False, "provider-owned execution")

    backends: dict[str, Any] = {}
    for name in config.get("backends", ("bare",)):
        if name == "bare":
            backends[name] = BareWorker(unused_advance)
        elif name == "subprocess":
            backends[name] = SubprocessWorker()
        elif name in {"os-isolated", "os_isolated"}:
            from sovereign_agent._internal.isolation import detect_best_policy

            backends["os-isolated"] = OSIsolatedWorker(isolation_policy=detect_best_policy())
        elif name == "docker":
            backends[name] = DockerWorker()
        else:
            raise ValueError(f"unsupported configured backend: {name}")
    seats = SeatRegistry(runtime)
    return GovernedExecutionEngine(
        runtime_root=runtime,
        repository_manager=RepositoryManager(runtime, repositories),
        seat_registry=seats,
        providers=providers,
        backends=backends,
    )


def _runtime(config_file: Path) -> RuntimeRoot:
    config = _read_object(config_file)
    return RuntimeRoot(Path(str(config["runtime_root"]))).initialize()


def _read_object(path: Path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8")
    if path.suffix.lower() in {".yaml", ".yml"}:
        import yaml  # type: ignore[import-untyped]

        value = yaml.safe_load(text)
    else:
        value = json.loads(text)
    if not isinstance(value, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return value


def _json(value: Any) -> None:
    typer.echo(json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False))


__all__ = [
    "EXIT_FAILED",
    "EXIT_INPUT",
    "EXIT_NOT_FOUND",
    "EXIT_OK",
    "execute_command",
    "governed_app",
    "register_execution_commands",
]
