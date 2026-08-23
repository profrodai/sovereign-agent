"""Network policy mapping to backend mechanisms with fail-closed evidence."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from sovereign_agent.contracts.execution import NetworkPolicy


@dataclass(frozen=True)
class NetworkEnforcement:
    policy: NetworkPolicy
    mechanism: str
    evidence: str


class NetworkGuard:
    def enforce(self, policy: NetworkPolicy | str, *, backend: str, allowlist: tuple[str, ...] = ()) -> NetworkEnforcement:
        if isinstance(policy, str):
            policy = NetworkPolicy(policy)
        if policy is NetworkPolicy.UNKNOWN:
            raise PermissionError("unknown network policy fails closed")
        if policy is NetworkPolicy.DENIED:
            mechanism = {"docker": "network=none", "podman": "network=none", "ssh": "forced-command wrap"}[backend]
            return NetworkEnforcement(policy, mechanism, f"{backend}:{mechanism}")
        if policy is NetworkPolicy.RESTRICTED:
            if not allowlist:
                raise PermissionError("restricted network requires an allowlist")
            mechanism = f"allowlist={','.join(allowlist)}"
            return NetworkEnforcement(policy, mechanism, f"{backend}:{mechanism}")
        if policy is NetworkPolicy.UNRESTRICTED:
            return NetworkEnforcement(policy, "explicit-unrestricted", f"{backend}:requested-unrestricted")
        if getattr(policy, "value", None) == "disabled" or policy is getattr(NetworkPolicy, "DISABLED", None):
            return NetworkEnforcement(policy, "stack-disabled", f"{backend}:disabled")
        raise PermissionError(f"unenforceable network policy {policy}")
