"""v0.4 operator commands for API, connector, service, and introspection."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import typer

from sovereign_agent.execution.cli import (
    EXIT_FAILED,
    EXIT_INPUT,
    EXIT_NOT_FOUND,
    _engine,
    _json,
    receipt_app,
    relay_app,
)

connect_app = typer.Typer(name="connect", help="Probe serialized connectors.", no_args_is_help=True)
request_app = typer.Typer(
    name="request", help="Submit and inspect governed requests.", no_args_is_help=True
)
service_app = typer.Typer(name="service", help="Coordinator lifecycle.", no_args_is_help=True)
api_app = typer.Typer(name="api", help="Local authenticated API.", no_args_is_help=True)
seats_app = typer.Typer(name="seats", help="List supervised seats.", no_args_is_help=True)
executions_app = typer.Typer(name="executions", help="List executions.", no_args_is_help=True)
approvals_v04_app = typer.Typer(
    name="approvals-v04", help="Durable approval waits.", no_args_is_help=True
)


@connect_app.command("zeo")
def connect_zeo(
    action: str = typer.Argument("probe"),
    endpoint: str | None = typer.Option(None, "--endpoint"),
) -> None:
    del endpoint
    if action != "probe":
        raise typer.Exit(EXIT_INPUT)
    _json({"ok": True, "boundary": "serialized-contracts", "imports_zero_employee": False})


@request_app.command("submit")
def request_submit(
    request_file: Path = typer.Argument(..., exists=True, dir_okay=False),
    config_file: Path = typer.Option(..., "--config", exists=True, dir_okay=False),
) -> None:
    import asyncio

    from sovereign_agent.connectors import ConnectorError, ZeroEmployeeConnector

    connector = ZeroEmployeeConnector(_engine(config_file))
    try:
        ack, receipt = asyncio.run(connector.execute(request_file))
        _json({"ack": ack.to_dict(), "receipt": receipt.to_dict()})
        if not receipt.is_successful:
            raise typer.Exit(EXIT_FAILED)
    except ConnectorError as exc:
        _json({"error": str(exc)})
        raise typer.Exit(EXIT_INPUT) from exc


@request_app.command("status")
def request_status(
    execution_id: str,
    config_file: Path = typer.Option(..., "--config", exists=True, dir_okay=False),
) -> None:
    from sovereign_agent.connectors import ConnectorError, ZeroEmployeeConnector

    try:
        _json(ZeroEmployeeConnector(_engine(config_file)).status(execution_id))
    except ConnectorError as exc:
        _json({"error": str(exc)})
        raise typer.Exit(EXIT_NOT_FOUND) from exc


@receipt_app.command("export")
def receipt_export(
    execution_id: str,
    config_file: Path = typer.Option(..., "--config", exists=True, dir_okay=False),
    fmt: str = typer.Option("json", "--format"),
) -> None:
    del fmt
    from sovereign_agent.connectors import ConnectorError, ZeroEmployeeConnector

    try:
        _json(ZeroEmployeeConnector(_engine(config_file)).export_receipt(execution_id))
    except ConnectorError as exc:
        _json({"error": str(exc)})
        raise typer.Exit(EXIT_NOT_FOUND) from exc


@receipt_app.command("verify")
def receipt_verify(receipt_file: Path = typer.Argument(..., exists=True, dir_okay=False)) -> None:
    from sovereign_agent.connectors import ZeroEmployeeConnector

    result = ZeroEmployeeConnector.verify_receipt(receipt_file)
    _json(result)
    if not result["valid"]:
        raise typer.Exit(EXIT_FAILED)


@api_app.command("serve")
def api_serve(
    runtime_root: Path = typer.Option(..., "--runtime-root"),
    socket_path: Path = typer.Option(..., "--socket"),
    key_id: str = typer.Option("operator-local-01", "--key-id"),
    secret: str = typer.Option(..., "--secret", envvar="SOVEREIGN_AGENT_API_SECRET"),
) -> None:
    from sovereign_agent.api import Keyring, UnixSocketApiServer, build_local_stack
    from sovereign_agent.runtime import RuntimeRoot

    runtime = RuntimeRoot(runtime_root).initialize()
    dispatcher, _ = build_local_stack(runtime, Keyring({key_id: secret.encode()}))
    with UnixSocketApiServer(socket_path, dispatcher):
        typer.echo(f"listening on {socket_path}")
        try:
            import time

            while True:
                time.sleep(3600)
        except KeyboardInterrupt:
            return


@service_app.command("status")
def service_status(runtime_root: Path = typer.Option(..., "--runtime-root")) -> None:
    from sovereign_agent.operations import snapshot
    from sovereign_agent.runtime import RuntimeRoot
    from sovereign_agent.service import ServiceRuntime

    runtime = (
        RuntimeRoot.open(runtime_root)
        if (runtime_root / "runtime.json").exists()
        else RuntimeRoot(runtime_root).initialize()
    )
    svc = ServiceRuntime(runtime)
    _json(snapshot(runtime, service=svc.readiness().to_dict()))


@service_app.command("doctor")
def service_doctor(runtime_root: Path = typer.Option(..., "--runtime-root")) -> None:
    service_status(runtime_root)


@service_app.command("drain")
def service_drain(runtime_root: Path = typer.Option(..., "--runtime-root")) -> None:
    from sovereign_agent.runtime import RuntimeRoot
    from sovereign_agent.service import ServiceRuntime

    svc = ServiceRuntime(RuntimeRoot.open(runtime_root))
    svc.drain()
    _json({"draining": True})


@service_app.command("stop")
def service_stop(runtime_root: Path = typer.Option(..., "--runtime-root")) -> None:
    from sovereign_agent.runtime import RuntimeRoot
    from sovereign_agent.service import ServiceRuntime

    svc = ServiceRuntime(RuntimeRoot.open(runtime_root))
    svc.stop()
    _json({"stopped": True})


@service_app.command("backup")
def service_backup(
    destination: Path = typer.Argument(...),
    runtime_root: Path = typer.Option(..., "--runtime-root"),
) -> None:
    from sovereign_agent.operations import backup
    from sovereign_agent.runtime import RuntimeRoot

    path = backup(RuntimeRoot.open(runtime_root), destination)
    _json({"backup": str(path)})


@service_app.command("restore")
def service_restore(
    archive: Path = typer.Argument(...),
    destination: Path = typer.Option(..., "--destination"),
    verify_only: bool = typer.Option(False, "--verify-only"),
) -> None:
    from sovereign_agent.operations import restore

    path = restore(archive, destination, verify_only=verify_only)
    _json({"restore": str(path), "verify_only": verify_only})


@seats_app.command("list")
def seats_list(
    runtime_root: Path = typer.Option(..., "--runtime-root"),
    json_out: bool = typer.Option(True, "--json"),
) -> None:
    from sovereign_agent.operations import snapshot
    from sovereign_agent.registry import SeatRegistry
    from sovereign_agent.registry.supervisor import SeatSupervisor
    from sovereign_agent.runtime import RuntimeRoot

    runtime = RuntimeRoot.open(runtime_root)
    registry = SeatRegistry(runtime)
    supervisor = SeatSupervisor(runtime, registry)
    items = [
        {**item.to_dict(), "presence": supervisor.observe(item).value} for item in registry.list()
    ]
    _json(snapshot(runtime, seats=items) if json_out else {"seats": items})


@executions_app.command("list")
def executions_list(
    runtime_root: Path = typer.Option(..., "--runtime-root"),
    state: str | None = typer.Option(None, "--state"),
    json_out: bool = typer.Option(True, "--json"),
) -> None:
    del json_out
    from sovereign_agent.operations import snapshot
    from sovereign_agent.runtime import RuntimeRoot

    runtime = RuntimeRoot.open(runtime_root)
    rows = []
    for path in runtime.executions_dir.glob("*/state.json"):
        data = json.loads(path.read_text(encoding="utf-8"))
        if state and data.get("phase") != state:
            continue
        rows.append({"execution_id": data.get("execution_id"), "phase": data.get("phase")})
    _json(snapshot(runtime, executions=rows, high_water={"executions": len(rows)}))


@approvals_v04_app.command("pending")
def approvals_pending(
    runtime_root: Path = typer.Option(..., "--runtime-root"),
    json_out: bool = typer.Option(True, "--json"),
) -> None:
    del json_out
    from sovereign_agent.approvals import ApprovalService
    from sovereign_agent.operations import snapshot
    from sovereign_agent.runtime import RuntimeRoot

    runtime = RuntimeRoot.open(runtime_root)
    _json(snapshot(runtime, approvals=ApprovalService(runtime).pending()))


def status_command(
    runtime_root: Path = typer.Option(..., "--runtime-root"),
    json_out: bool = typer.Option(True, "--json"),
) -> None:
    del json_out
    from sovereign_agent.operations import snapshot
    from sovereign_agent.runtime import RuntimeRoot
    from sovereign_agent.service import ServiceRuntime

    runtime = RuntimeRoot.open(runtime_root)
    _json(snapshot(runtime, readiness=ServiceRuntime(runtime).readiness().to_dict()))


def capabilities_command(
    runtime_root: Path = typer.Option(..., "--runtime-root"),
    verified_only: bool = typer.Option(False, "--verified-only"),
    json_out: bool = typer.Option(True, "--json"),
) -> None:
    del json_out
    from sovereign_agent.operations import snapshot
    from sovereign_agent.registry import SeatRegistry
    from sovereign_agent.runtime import RuntimeRoot

    runtime = RuntimeRoot.open(runtime_root)
    caps = [
        {"seat": seat.instance_id.value, "capability": name, "verified": True}
        for seat in SeatRegistry(runtime).list()
        for name in seat.capabilities
    ]
    if verified_only:
        caps = [item for item in caps if item["verified"]]
    _json(snapshot(runtime, capabilities=caps))


@relay_app.command("inspect")
def relay_inspect(
    conversation: str | None = typer.Option(None, "--conversation"),
    config_file: Path | None = typer.Option(None, "--config"),
    runtime_root: Path | None = typer.Option(None, "--runtime-root"),
) -> None:
    from sovereign_agent.execution.cli import _read_object
    from sovereign_agent.operations import snapshot
    from sovereign_agent.registry import SeatRegistry
    from sovereign_agent.relay import DurableRelay
    from sovereign_agent.runtime import RuntimeRoot

    root = runtime_root
    if config_file is not None:
        root = Path(str(_read_object(config_file)["runtime_root"]))
    if root is None:
        raise typer.Exit(EXIT_INPUT)
    runtime = RuntimeRoot.open(root)
    relay = DurableRelay(runtime, SeatRegistry(runtime))
    payload: dict[str, Any] = {"dead_letters": len(relay.dead_letters())}
    if conversation:
        payload["conversation"] = relay.inspect_conversation(conversation)
    _json(snapshot(runtime, relay=payload))


def register_v04_commands(app: typer.Typer) -> None:
    app.add_typer(connect_app, name="connect")
    app.add_typer(request_app, name="request")
    app.add_typer(service_app, name="service")
    app.add_typer(api_app, name="api")
    app.add_typer(seats_app, name="seats")
    app.add_typer(executions_app, name="executions")
    app.add_typer(approvals_v04_app, name="approvals-v04")
    app.command("status")(status_command)
    app.command("capabilities")(capabilities_command)
