"""Fail-closed capability-aware placement. Never silently degrades isolation."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

from sovereign_agent.contracts.capabilities import EvidenceLevel, RuntimeCapabilityManifest
from sovereign_agent.contracts.execution import NetworkPolicy, SandboxMinimum
from sovereign_agent.fleet.registry import WorkerRecord, enforced


class PlacementRefusal(ValueError):
    def __init__(self, reasons: list[str]) -> None:
        super().__init__("; ".join(reasons))
        self.reasons = reasons


@dataclass(frozen=True)
class PlacementDecision:
    worker_id: str
    reasons_accepted: tuple[str, ...]
    candidates_rejected: tuple[tuple[str, str], ...]


_SANDBOX_CAPABILITY = {
    SandboxMinimum.NONE: None,
    SandboxMinimum.BARE: None,
    SandboxMinimum.PROCESS: "process_isolation",
    SandboxMinimum.FILESYSTEM_ISOLATED: "filesystem_isolation",
    SandboxMinimum.NETWORK_RESTRICTED: "network_isolation",
}


class PlacementEngine:
    def place(
        self,
        *,
        requirements: Mapping[str, Any],
        effects: Mapping[str, Any],
        constraints: Mapping[str, Any],
        workers: list[WorkerRecord],
    ) -> PlacementDecision:
        del effects
        rejections: list[tuple[str, str]] = []
        selected: WorkerRecord | None = None
        accepted: list[str] = []
        sandbox = _sandbox(constraints)
        network = _network(constraints)
        required_caps = list(requirements.get("runtime") or requirements.get("capabilities") or [])
        for worker in workers:
            reason = self._refuse(worker, sandbox, network, required_caps, constraints)
            if reason is not None:
                rejections.append((worker.identity.worker_id, reason))
                continue
            if selected is None and not worker.draining and not worker.expired and worker.admitted:
                selected = worker
                accepted.append(f"enforced isolation and network on {worker.identity.backend}")
        if selected is None:
            raise PlacementRefusal(
                [f"{worker_id}: {reason}" for worker_id, reason in rejections]
                or ["no admitted workers"]
            )
        return PlacementDecision(
            worker_id=selected.identity.worker_id,
            reasons_accepted=tuple(accepted),
            candidates_rejected=tuple(rejections),
        )

    def _refuse(
        self,
        worker: WorkerRecord,
        sandbox: SandboxMinimum,
        network: NetworkPolicy,
        required_caps: list[Any],
        constraints: Mapping[str, Any],
    ) -> str | None:
        if worker.expired:
            return "worker expired; quarantine only"
        if not worker.admitted:
            return "worker not admitted after probe"
        if worker.draining:
            return "worker draining"
        try:
            manifest = RuntimeCapabilityManifest.from_dict(
                {"capabilities": worker.manifest.get("capabilities", worker.manifest)}
                if "capabilities" not in worker.manifest
                else worker.manifest
            )
        except Exception as exc:  # noqa: BLE001
            return f"manifest unreadable: {exc}"
        cap_name = _SANDBOX_CAPABILITY.get(sandbox)
        if cap_name and not enforced(manifest, cap_name):
            return f"{cap_name} not ENFORCED; refusing silent isolation downgrade"
        if network in {NetworkPolicy.DENIED, NetworkPolicy.RESTRICTED}:
            if not enforced(manifest, "network_isolation"):
                return "network policy cannot be enforced; labels are insufficient"
            mechanism = (worker.manifest.get("network") or {}).get("mechanism")
            if not mechanism:
                return "network mechanism evidence missing"
        if network is NetworkPolicy.UNKNOWN:
            return "network policy unknown; fail closed"
        platform = constraints.get("platform")
        if platform and worker.identity.host and constraints.get("require_platform"):
            if str(platform) not in worker.manifest.get("platforms", [worker.identity.host]):
                return f"platform {platform} not proven"
        for item in required_caps:
            name = item if isinstance(item, str) else str(item)
            assertion = manifest.get(name)
            if assertion is None or not assertion.is_available():
                return f"required capability {name} unavailable"
            if not assertion.has_evidence(EvidenceLevel.ENFORCED):
                return f"required capability {name} is claimed but not ENFORCED"
        return None


PlacementEngine = PlacementEngine
PlacementRefusal = PlacementRefusal
PlacementDecision = PlacementDecision


def _sandbox(constraints: Mapping[str, Any]) -> SandboxMinimum:
    value = constraints.get("sandbox_minimum") or constraints.get("sandbox") or "none"
    if isinstance(value, SandboxMinimum):
        return value
    return SandboxMinimum(str(value))


def _network(constraints: Mapping[str, Any]) -> NetworkPolicy:
    value = constraints.get("network") or "unknown"
    if isinstance(value, NetworkPolicy):
        return value
    return NetworkPolicy(str(value))


PlacementEngine = PlacementEngine
