"""Credential gateway (Decision 5).

Resolves per-tool credentials through ``SecretBroker`` after placement.
Values are injected only at process spawn, never persisted in receipts.
"""

from __future__ import annotations

import logging
import os

from sovereign_agent.secrets import SecretBroker

log = logging.getLogger(__name__)


class CredentialGateway:
    """Loads credentials from env and optional short-lived secret leases."""

    def __init__(
        self,
        env: dict[str, str] | None = None,
        *,
        broker: SecretBroker | None = None,
    ) -> None:
        self._env = dict(env) if env is not None else dict(os.environ)
        self._broker = broker
        self._tool_leases: dict[str, str] = {}

    def get(self, key: str) -> str | None:
        return self._env.get(key)

    def require(self, key: str) -> str:
        value = self._env.get(key)
        if not value:
            raise RuntimeError(f"credential {key!r} is not set")
        return value

    def bind_tool_lease(self, tool_name: str, lease_id: str) -> None:
        self._tool_leases[tool_name] = lease_id

    def for_tool(self, tool_name: str) -> dict[str, str]:
        """Return spawn-only credentials for ``tool_name``.

        Without a bound secret lease this stays empty. Binding a lease
        injects values only into the returned mapping for process spawn.
        """
        if self._broker is None:
            log.debug("CredentialGateway.for_tool(%r): no broker bound", tool_name)
            return {}
        lease_id = self._tool_leases.get(tool_name)
        if not lease_id:
            return {}
        return self._broker.inject(lease_id)


__all__ = ["CredentialGateway"]
