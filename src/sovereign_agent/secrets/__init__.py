"""Short-lived secret leases injected only at process spawn."""

from __future__ import annotations

import secrets
import time
from collections.abc import Mapping
from dataclasses import dataclass


class SecretError(RuntimeError):
    pass


@dataclass
class SecretLease:
    lease_id: str
    execution_id: str
    names: tuple[str, ...]
    expires_at_s: float
    revoked: bool = False
    injected: bool = False


class SecretBroker:
    """Resolve opaque refs after placement. Never persist secret values."""

    def __init__(self, providers: Mapping[str, Mapping[str, str]] | None = None) -> None:
        self._providers = {name: dict(values) for name, values in (providers or {}).items()}
        self._leases: dict[str, SecretLease] = {}
        self._values: dict[str, dict[str, str]] = {}

    def register_provider(self, name: str, values: Mapping[str, str]) -> None:
        if name not in {"env", "file"}:
            raise SecretError("only env and file providers are first-party")
        self._providers[name] = dict(values)

    def issue(
        self, execution_id: str, refs: Mapping[str, str], *, ttl_s: float = 30.0
    ) -> SecretLease:
        resolved: dict[str, str] = {}
        for alias, spec in refs.items():
            provider, _, key = spec.partition(":")
            store = self._providers.get(provider)
            if store is None or key not in store:
                raise SecretError(f"unresolved secret ref {spec}")
            resolved[alias] = store[key]
        lease = SecretLease(
            lease_id=f"sec-{secrets.token_hex(8)}",
            execution_id=execution_id,
            names=tuple(resolved),
            expires_at_s=time.time() + ttl_s,
        )
        self._leases[lease.lease_id] = lease
        self._values[lease.lease_id] = resolved
        return lease

    def inject(self, lease_id: str, *, now_s: float | None = None) -> dict[str, str]:
        lease = self._leases.get(lease_id)
        if lease is None or lease.revoked:
            raise SecretError("secret lease is not active")
        if (now_s or time.time()) >= lease.expires_at_s:
            self.revoke(lease_id)
            raise SecretError("secret lease expired")
        lease.injected = True
        return dict(self._values[lease_id])

    def revoke(self, lease_id: str) -> None:
        lease = self._leases.get(lease_id)
        if lease is None:
            return
        lease.revoked = True
        self._values.pop(lease_id, None)

    def revoke_execution(self, execution_id: str) -> None:
        for lease_id, lease in list(self._leases.items()):
            if lease.execution_id == execution_id:
                self.revoke(lease_id)


SecretBroker = SecretBroker
