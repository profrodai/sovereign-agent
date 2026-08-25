"""Bounded subprocess invocation. Never uses shell=True."""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

from sovereign_agent.errors import Refusal
from sovereign_agent.ids import new_id, utc_now
from sovereign_agent.models import ActorReport, Receipt
from sovereign_agent.providers import PROVIDERS
from sovereign_agent.providers.scripted import InvocationSpec


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
        ) from error


def invoke_actor(
    provider_name: str, workspace: Path, output: Path, prompt: str
) -> tuple[Receipt, ActorReport | None]:
    provider = PROVIDERS.get(provider_name)
    if provider is None:
        raise Refusal(
            happened=f"Unknown provider {provider_name}.",
            why="Fail closed: only probed adapters may run.",
            inspect="sovereign-agent doctor",
            next_command="Use scripted until a live adapter is installed.",
        )
    capabilities = provider.probe()
    if not capabilities.available:
        raise Refusal(
            "Provider unavailable.",
            "Fail closed on missing executables.",
            "doctor",
            "Install the CLI or use scripted.",
        )
    spec = provider.build_invocation(workspace, output, prompt)
    started = utc_now()
    result = run_spec(spec)
    ended = utc_now()
    raw = workspace / "provider-raw"
    raw.mkdir(parents=True, exist_ok=True)
    (raw / "stdout.txt").write_text(result.stdout)
    (raw / "stderr.txt").write_text(result.stderr)
    report_path = output / "report.json"
    report: ActorReport | None = None
    status = "failed"
    if result.returncode == 0 and report_path.is_file():
        try:
            report = ActorReport.model_validate_json(report_path.read_text(encoding="utf-8"))
            status = (
                report.status if report.status in {"completed", "blocked", "failed"} else "failed"
            )
        except Exception:
            status = "failed"
    elif result.returncode == 0 and not report_path.is_file():
        status = "failed"
    receipt = Receipt(
        id=new_id("rct"),
        actor_id="",
        provider=provider_name,
        provider_session_ref=None,
        started_at=started,
        ended_at=ended,
        status=status,
        evidence_refs=[],
    )
    digest = hashlib.sha256(
        json.dumps(receipt.model_dump(mode="json"), sort_keys=True).encode()
    ).hexdigest()
    (workspace / "receipt.json").write_text(
        receipt.model_dump_json(indent=2) + f"\n# digest {digest}\n"
    )
    return receipt, report
