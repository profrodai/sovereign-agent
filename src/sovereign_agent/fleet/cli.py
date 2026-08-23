"""Fleet operator CLI: worker list/show/drain/probe, execution locate, fleet status."""

from __future__ import annotations

from pathlib import Path

import typer

from sovereign_agent.execution.cli import _json

fleet_app = typer.Typer(name="fleet", help="Bounded execution fleet.", no_args_is_help=True)
worker_app = typer.Typer(name="worker", help="Worker registry.", no_args_is_help=True)
execution_app = typer.Typer(
    name="execution", help="Execution locate/reconcile.", no_args_is_help=True
)
fleet_app.add_typer(worker_app, name="worker")
fleet_app.add_typer(execution_app, name="execution")


def _coordinator(root: Path):
    from sovereign_agent.fleet.coordinator import FleetCoordinator

    return FleetCoordinator(root)


@worker_app.command("list")
def worker_list(runtime_root: Path = typer.Option(..., "--runtime-root")) -> None:
    _json({"workers": _coordinator(runtime_root).status()["workers"]})


@worker_app.command("show")
def worker_show(
    worker_id: str,
    runtime_root: Path = typer.Option(..., "--runtime-root"),
) -> None:
    workers = _coordinator(runtime_root).status()["workers"]
    match = next((item for item in workers if item["identity"]["worker_id"] == worker_id), None)
    if match is None:
        raise typer.Exit(1)
    _json(match)


@worker_app.command("drain")
def worker_drain(
    worker_id: str,
    runtime_root: Path = typer.Option(..., "--runtime-root"),
) -> None:
    _json(_coordinator(runtime_root).drain_worker(worker_id).to_dict())


@worker_app.command("probe")
def worker_probe(
    worker_id: str,
    runtime_root: Path = typer.Option(..., "--runtime-root"),
) -> None:
    record = _coordinator(runtime_root).registry.require(worker_id)
    _json({"worker_id": worker_id, "admitted": record.admitted, "expired": record.expired})


@execution_app.command("locate")
def execution_locate(
    execution_id: str,
    runtime_root: Path = typer.Option(..., "--runtime-root"),
) -> None:
    _json(_coordinator(runtime_root).locate(execution_id))


@execution_app.command("reconcile")
def execution_reconcile(
    execution_id: str,
    runtime_root: Path = typer.Option(..., "--runtime-root"),
) -> None:
    _json(_coordinator(runtime_root).locate(execution_id))


@fleet_app.command("status")
def fleet_status(runtime_root: Path = typer.Option(..., "--runtime-root")) -> None:
    _json(_coordinator(runtime_root).status())


def register_fleet_commands(app: typer.Typer) -> None:
    app.add_typer(fleet_app, name="fleet")
