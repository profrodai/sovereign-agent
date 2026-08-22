"""Replay defense for authenticated envelopes."""

from __future__ import annotations

from collections.abc import Callable
from datetime import UTC, datetime, timedelta

from sovereign_agent._internal.atomic import atomic_write_bytes
from sovereign_agent._internal.file_lock import exclusive_file_lock
from sovereign_agent._internal.hashed import bind_hashed
from sovereign_agent.api.envelope import ProtocolEnvelope, ProtocolError
from sovereign_agent.api.signing import Keyring, verify
from sovereign_agent.contracts._core import canonical_json_bytes
from sovereign_agent.runtime import RuntimeRoot


class ReplayDetected(ProtocolError):
    def __init__(self, message_id: str) -> None:
        super().__init__("replay", detail=f"message_id already observed: {message_id}")


class Authenticator:
    """HMAC verification plus durable replay ledger. Not organizational authorization."""

    def __init__(
        self,
        runtime_root: RuntimeRoot,
        keyring: Keyring,
        *,
        skew: timedelta = timedelta(minutes=5),
        clock: Callable[[], datetime] | None = None,
    ) -> None:
        self.runtime_root = runtime_root
        self.keyring = keyring
        self.skew = skew
        self._clock = clock or (lambda: datetime.now(UTC))
        self._dir = runtime_root.ensure_directory("api") / "replay"
        self._dir.mkdir(mode=0o700, parents=True, exist_ok=True)
        self._lock = runtime_root.locks_dir / "replay.lock"

    def authenticate(self, envelope: ProtocolEnvelope) -> None:
        verify(envelope, self.keyring)
        now = self._clock()
        if now.tzinfo is None:
            raise ProtocolError("malformed-envelope", detail="clock must be timezone-aware")
        now = now.astimezone(UTC)
        sent = envelope.sent_at.astimezone(UTC)
        if sent > now + self.skew or now - sent > self.skew:
            raise ProtocolError("replay", detail="sent_at is outside the accepted skew window")
        path = bind_hashed(self._dir, f"{envelope.auth.key_id}:{envelope.message_id}")
        with exclusive_file_lock(self._lock):
            if path.exists():
                raise ReplayDetected(envelope.message_id)
            atomic_write_bytes(
                path,
                canonical_json_bytes(
                    {
                        "key_id": envelope.auth.key_id,
                        "message_id": envelope.message_id,
                        "observed_at": now.isoformat().replace("+00:00", "Z"),
                    }
                ),
            )
