"""Four-plane isolation policy, named honestly for application-level enforcement.

Filesystem, network, credentials, and tools are different questions. Passing
one never implies the others. Process isolation is reported only when a live
probe proves it; this module does not counterfeit an OS sandbox.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import NoReturn

from sovereign_agent.errors import Refusal


@dataclass(frozen=True)
class PlaneStatus:
    plane: str
    verdict: str
    enforcement: str
    detail: str


@dataclass(frozen=True)
class IsolationPolicy:
    filesystem_roots: tuple[Path, ...] = ()
    network_hosts: frozenset[str] = frozenset()
    credential_names: frozenset[str] = frozenset()
    allowed_tools: frozenset[str] = frozenset()
    denied_tools: frozenset[str] = frozenset()

    def authorize_path(self, path: Path) -> Path:
        candidate = path.resolve()
        if any(
            candidate == root.resolve() or root.resolve() in candidate.parents
            for root in self.filesystem_roots
        ):
            return candidate
        self._refuse("filesystem", str(candidate))

    def authorize_network(self, host: str) -> str:
        normalized = host.rstrip(".").lower()
        if normalized in {item.rstrip(".").lower() for item in self.network_hosts}:
            return normalized
        self._refuse("network", host)

    def authorize_credential(self, name: str) -> str:
        if name in self.credential_names:
            return name
        self._refuse("credential", name)

    def authorize_tool(self, name: str) -> str:
        if name not in self.denied_tools and name in self.allowed_tools:
            return name
        self._refuse("tool", name)

    def explain(self, process_probe: Callable[[], bool] | None = None) -> tuple[PlaneStatus, ...]:
        process_ok = process_probe is not None and process_probe()
        return (
            PlaneStatus(
                "process",
                "ENFORCED" if process_ok else "UNAVAILABLE",
                "behavioral probe",
                "live probe passed" if process_ok else "no proven OS sandbox",
            ),
            PlaneStatus(
                "filesystem",
                "ENFORCED",
                "resolved-path allowlist",
                f"{len(self.filesystem_roots)} root(s)",
            ),
            PlaneStatus(
                "network",
                "ENFORCED",
                "application allowlist",
                f"{len(self.network_hosts)} host(s); not an OS egress firewall",
            ),
            PlaneStatus(
                "credentials",
                "ENFORCED",
                "named broker allowlist",
                f"{len(self.credential_names)} name(s); values remain outside policy",
            ),
            PlaneStatus(
                "tools",
                "ENFORCED",
                "deny-then-allow policy",
                f"{len(self.allowed_tools)} allowed, {len(self.denied_tools)} denied",
            ),
        )

    @staticmethod
    def _refuse(plane: str, subject: str) -> NoReturn:
        raise Refusal(
            f"{plane} access to {subject!r} was refused.",
            "Each isolation plane is independently allowlisted; absence is denial.",
            "sovereign-agent mechanisms isolation",
            f"Add {subject!r} to the explicit {plane} policy or choose a permitted value.",
            category="isolation_refusal",
        )
