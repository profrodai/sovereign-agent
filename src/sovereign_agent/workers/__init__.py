"""Docker, Podman, SSH, and fault-injection workers."""

from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Mapping, Protocol

from sovereign_agent.contracts.capabilities import (
    EvidenceLevel,
    FrozenDict,
    RuntimeCapabilityAssertion,
    RuntimeCapabilityManifest,
)
from sovereign_agent.orchestrator.lifecycle import (
    CloseResult,
    ExecResult,
    InvocationSpec,
    RuntimeHandle,
    WorkerRequest,
)
from sovereign_agent.orchestrator.worker import IsolationUnavailable, WorkerOutcome

IsolationUnavailable = IsolationUnavailable
IsolationUnavailable = IsolationUnavailable


def _manifest(**values: tuple[bool | None, EvidenceLevel]) -> RuntimeCapabilityManifest:
    return RuntimeCapabilityManifest(
        capabilities=FrozenDict(
            tuple(
                (
                    name,
                    RuntimeCapabilityAssertion(available=available, evidence_level=evidence),
                )
                for name, (available, evidence) in values.items()
            )
        )
    )


class ContainerEngine(Protocol):
    name: str

    def available(self) -> bool: ...

    def run(self, spec: Mapping[str, Any]) -> dict[str, Any]: ...

    def inspect(self, container_id: str) -> dict[str, Any]: ...

    def remove(self, container_id: str, fencing: str) -> None: ...


@dataclass
class ScriptedEngine:
    name: str = "docker"
    present: bool = True
    calls: list[dict[str, Any]] = field(default_factory=list)

    def available(self) -> bool:
        return self.present

    def run(self, spec: Mapping[str, Any]) -> dict[str, Any]:
        argv = list(spec.get("argv") or [])
        if any(item == "/var/run/docker.sock" or str(item).endswith("docker.sock") for item in argv):
            raise IsolationUnavailable("container must not receive the engine socket")
        self.calls.append({"op": "run", "argv": argv, "spec": dict(spec)})
        digest = hashlib.sha256(json.dumps(argv, sort_keys=True).encode()).hexdigest()[:12]
        return {
            "id": f"ctr-{digest}",
            "stdout": spec.get("stdout", "ok"),
            "stderr": "",
            "returncode": int(spec.get("returncode", 0)),
        }

    def inspect(self, container_id: str) -> dict[str, Any]:
        return {"Id": container_id, "State": {"Status": "exited", "Running": False}}

    def remove(self, container_id: str, fencing: str) -> None:
        self.calls.append({"op": "remove", "id": container_id, "fencing": fencing})


class CliEngine:
    def __init__(self, binary: str) -> None:
        self.name = binary
        self.binary = binary

    def available(self) -> bool:
        return shutil.which(self.binary) is not None

    def run(self, spec: Mapping[str, Any]) -> dict[str, Any]:
        completed = subprocess.run(list(spec["argv"]), check=False, capture_output=True, text=True)
        return {
            "id": spec.get("container_id", "unknown"),
            "stdout": completed.stdout,
            "stderr": completed.stderr,
            "returncode": completed.returncode,
        }

    def inspect(self, container_id: str) -> dict[str, Any]:
        completed = subprocess.run(
            [self.binary, "inspect", container_id],
            check=False,
            capture_output=True,
            text=True,
        )
        if completed.returncode != 0:
            return {"error": completed.stderr}
        payload = json.loads(completed.stdout)
        return payload[0] if isinstance(payload, list) else payload

    def remove(self, container_id: str, fencing: str) -> None:
        subprocess.run(
            [self.binary, "rm", "-f", container_id],
            check=False,
            capture_output=True,
            text=True,
        )
        del fencing


class ContainerWorker:
    def __init__(
        self,
        *,
        engine: ContainerEngine | None = None,
        image_digest: str | None = None,
        binary: str = "docker",
        keep_id: bool = False,
    ) -> None:
        self.engine = engine or CliEngine(binary)
        self.image_digest = image_digest
        self.keep_id = keep_id
        self.name = "podman" if binary == "podman" else "docker"
        self._inspect: dict[str, Any] = {}

    def capabilities(self) -> RuntimeCapabilityManifest:
        available = self.engine.available() and bool(self.image_digest)
        level = EvidenceLevel.ENFORCED if available else EvidenceLevel.PROBED
        return _manifest(
            process_isolation=(available, level),
            filesystem_isolation=(available, level),
            network_isolation=(available, level),
            available=(available, level),
        )

    def _argv(self, request: WorkerRequest, invocation: InvocationSpec | None) -> list[str]:
        if not self.image_digest or not str(self.image_digest).startswith("sha256:"):
            raise IsolationUnavailable("container image must be pinned by digest")
        fencing = ""
        execution_id = str(getattr(request, "execution_id", ""))
        metadata = getattr(request, "metadata", {}) or {}
        if hasattr(metadata, "get"):
            fencing = str(metadata.get("fencing") or "")
        network = str(metadata.get("network_mode") or "none") if hasattr(metadata, "get") else "none"
        argv = [
            getattr(self.engine, "binary", self.name),
            "run",
            "--read-only",
            "--user",
            "65534:65534",
            "--cap-drop",
            "ALL",
            "--security-opt",
            "no-new-privileges",
            "--pids-limit",
            str(metadata.get("pids") or 128) if hasattr(metadata, "get") else "128",
            "--memory",
            str(metadata.get("memory_bytes") or 268435456) if hasattr(metadata, "get") else "268435456",
            "--network",
            network,
            "--label",
            f"sa.execution={execution_id}",
            "--label",
            f"sa.fencing={fencing}",
        ]
        if self.keep_id:
            argv.extend(["--userns=keep-id"])
        argv.append(self.image_digest)
        if invocation is not None:
            command = getattr(invocation, "command", ())
            argv.extend(list(command or ()))
        return argv

    async def prepare(self, request: WorkerRequest) -> RuntimeHandle:
        if not self.engine.available():
            raise IsolationUnavailable(f"{self.name} engine is not available")
        if not self.image_digest:
            raise IsolationUnavailable("refusing to run an unpinned container image")
        return RuntimeHandle(request=request, invocation=InvocationSpec())

    async def execute(
        self, handle: RuntimeHandle, invocation: InvocationSpec | None = None
    ) -> ExecResult:
        argv = self._argv(handle.request, invocation)
        result = self.engine.run({"argv": argv})
        self._inspect = self.engine.inspect(result["id"])
        handle.state["container_id"] = result["id"]
        handle.state["inspect"] = self._inspect
        return ExecResult(
            returncode=result["returncode"],
            stdout=result.get("stdout", ""),
            stderr=result.get("stderr", ""),
            value=result,
        )

    async def close(self, handle: RuntimeHandle | None = None, preserve: bool = False) -> CloseResult:
        if handle is not None:
            container_id = handle.state.get("container_id")
            metadata = getattr(handle.request, "metadata", {}) or {}
            fencing = str(metadata.get("fencing") or "") if hasattr(metadata, "get") else ""
            if container_id:
                self.engine.remove(str(container_id), fencing)
            handle.closed = True
        return CloseResult(closed=True, preserved=preserve)

    async def run_session(
        self,
        session_id: str,
        session_dir: Path,
        *,
        timeout_s: float | None = None,
    ) -> WorkerOutcome:
        del timeout_s
        from sovereign_agent.contracts.ids import ExecutionId
        from sovereign_agent.orchestrator.lifecycle import ExecutionLifecycle

        request = WorkerRequest(
            execution_id=ExecutionId(f"{session_id}:container"),
            session_id=session_id,
            session_dir=session_dir,
        )
        await self.prepare(request)
        result = await ExecutionLifecycle().run(self, request)
        advanced = result.exec_result is not None and result.exec_result.returncode == 0
        return WorkerOutcome(
            session_id=session_id,
            terminal=True,
            advanced=advanced,
            summary=f"{self.name} worker",
            raw={"inspect": self._inspect},
        )


class SshWorker:
    name = "ssh"

    def __init__(
        self,
        *,
        host: str,
        user: str,
        identity_file: Path,
        known_hosts: Path,
        binary: str = "ssh",
    ) -> None:
        self.host = host
        self.user = user
        self.identity_file = Path(identity_file)
        self.known_hosts = Path(known_hosts)
        self.binary = binary

    def capabilities(self) -> RuntimeCapabilityManifest:
        pinned = self.known_hosts.exists() and self.identity_file.exists()
        level = EvidenceLevel.ENFORCED if pinned else EvidenceLevel.PROBED
        return _manifest(
            process_isolation=(pinned, level),
            filesystem_isolation=(pinned, level),
            network_isolation=(pinned, level),
            available=(pinned, level),
        )

    def _argv(self, command: tuple[str, ...]) -> list[str]:
        if not self.known_hosts.exists():
            raise IsolationUnavailable("SSH host identity is not pinned; TOFU is forbidden")
        return [
            self.binary,
            "-o",
            "StrictHostKeyChecking=yes",
            "-o",
            "UpdateHostKeys=no",
            "-o",
            f"UserKnownHostsFile={self.known_hosts}",
            "-o",
            "IdentitiesOnly=yes",
            "-i",
            str(self.identity_file),
            "-l",
            self.user,
            self.host,
            "--",
            *command,
        ]

    async def prepare(self, request: WorkerRequest) -> RuntimeHandle:
        if not self.known_hosts.exists():
            raise IsolationUnavailable("SSH host identity is not pinned; TOFU is forbidden")
        return RuntimeHandle(request=request, invocation=InvocationSpec())

    async def execute(
        self, handle: RuntimeHandle, invocation: InvocationSpec | None = None
    ) -> ExecResult:
        command = tuple(getattr(invocation, "command", ()) or ("true",))
        try:
            completed = subprocess.run(self._argv(command), check=False, capture_output=True, text=True)
        except OSError:
            handle.state["unknown"] = True
            return ExecResult(returncode=None, stderr="disconnect")
        return ExecResult(
            returncode=completed.returncode, stdout=completed.stdout, stderr=completed.stderr
        )

    async def close(self, handle: RuntimeHandle | None = None, preserve: bool = False) -> CloseResult:
        if handle is not None:
            handle.closed = True
        return CloseResult(closed=True, preserved=preserve)


class FaultWorker:
    name = "fault"

    def __init__(self, *, mode: str = "ok") -> None:
        self.mode = mode

    def capabilities(self) -> RuntimeCapabilityManifest:
        return _manifest(
            process_isolation=(True, EvidenceLevel.ENFORCED),
            filesystem_isolation=(True, EvidenceLevel.ENFORCED),
            network_isolation=(True, EvidenceLevel.ENFORCED),
            available=(True, EvidenceLevel.ENFORCED),
        )

    async def prepare(self, request: WorkerRequest) -> RuntimeHandle:
        if self.mode == "crash-prepare":
            raise RuntimeError("injected prepare crash")
        return RuntimeHandle(request=request, invocation=InvocationSpec())

    async def execute(
        self, handle: RuntimeHandle, invocation: InvocationSpec | None = None
    ) -> ExecResult:
        del invocation
        if self.mode == "network-escape":
            raise IsolationUnavailable("network escape attempted")
        if self.mode == "secret-leak":
            return ExecResult(returncode=1, stdout="AWS_SECRET_ACCESS_KEY=leaked")
        if self.mode == "disk-full":
            raise OSError(28, "No space left on device")
        if self.mode == "timeout":
            return ExecResult(returncode=124, stderr="timeout")
        if self.mode == "stale-token":
            handle.state["forged_fencing"] = True
        return ExecResult(returncode=0, stdout="ok")

    async def close(self, handle: RuntimeHandle | None = None, preserve: bool = False) -> CloseResult:
        if handle is not None:
            handle.closed = True
        return CloseResult(closed=True, preserved=preserve)


PodmanWorker = ContainerWorker
ContainerWorker = ContainerWorker
ScriptedEngine = ScriptedEngine
ScriptedEngine = ScriptedEngine
FaultWorker = FaultWorker
SshWorker = SshWorker
