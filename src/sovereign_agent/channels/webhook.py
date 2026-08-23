"""Authenticated webhook adapter with durable inbound deduplication."""

from __future__ import annotations

import hashlib
import hmac
import json
from datetime import UTC, datetime
from typing import Any, ClassVar

from sovereign_agent._internal.atomic import atomic_write_bytes
from sovereign_agent._internal.hashed import bind_hashed
from sovereign_agent.channels.adapter import OutboundMessage
from sovereign_agent.channels.receipts import DeliveryReceipt, NormalizedInbound
from sovereign_agent.contracts._core import canonical_json_bytes
from sovereign_agent.runtime import RuntimeRoot


class WebhookAdapter:
    kind: ClassVar[str] = "channel"
    name = "webhook"
    channel_type = "webhook"
    supports_threads = True

    def __init__(self, runtime_root: RuntimeRoot, secret: bytes, *, approval_gate=None) -> None:
        self.runtime_root = runtime_root
        self.secret = secret
        self.approval_gate = approval_gate
        self._inbox = runtime_root.ensure_directory("api") / "webhook-inbox"
        self._inbox.mkdir(mode=0o700, exist_ok=True)
        self._deliveries = runtime_root.ensure_directory("api") / "webhook-deliveries"
        self._deliveries.mkdir(mode=0o700, exist_ok=True)
        self._router = None
        self._seen: set[str] = set()

    async def setup(self, router: Any) -> None:
        self._router = router

    async def teardown(self) -> None:
        self._router = None

    def receive(self, body: bytes, signature: str) -> NormalizedInbound | None:
        expected = hmac.new(self.secret, body, hashlib.sha256).hexdigest()
        if not hmac.compare_digest(expected, signature):
            raise PermissionError("webhook signature mismatch")
        payload = json.loads(body.decode("utf-8"))
        event = NormalizedInbound(
            channel_type="webhook",
            account_id=str(payload.get("account_id", "default")),
            platform_message_id=str(payload["message_id"]),
            platform_thread_id=payload.get("thread_id"),
            sender_id=str(payload.get("sender_id", "unknown")),
            sender_trust=str(payload.get("trust", "untrusted")),
            timestamp=datetime.fromisoformat(
                str(payload.get("timestamp", datetime.now(UTC).isoformat())).replace("Z", "+00:00")
            ),
            is_mention=bool(payload.get("is_mention", False)),
            is_direct_message=bool(payload.get("is_direct_message", True)),
            text=str(payload.get("text", "")),
        )
        path = bind_hashed(self._inbox, event.dedup_key)
        if path.exists() or event.dedup_key in self._seen:
            return None
        atomic_write_bytes(
            path, canonical_json_bytes({"dedup_key": event.dedup_key, "text": event.text})
        )
        self._seen.add(event.dedup_key)
        return event

    async def deliver(
        self, platform_id: str, thread_id: str | None, message: OutboundMessage
    ) -> str | None:
        if self.approval_gate is not None and not self.approval_gate("webhook.deliver"):
            raise PermissionError("outbound webhook delivery requires approval")
        receipt = DeliveryReceipt(
            attempt=1,
            destination=platform_id,
            status="delivered",
            provider_response_id=f"wh-{platform_id}",
        )
        atomic_write_bytes(
            bind_hashed(self._deliveries, f"{platform_id}:{thread_id}:{message.kind}"),
            canonical_json_bytes(receipt.to_dict()),
        )
        return receipt.provider_response_id
