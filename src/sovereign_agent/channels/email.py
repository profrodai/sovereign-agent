"""Email ingest/draft adapter. Sending is approval-gated and off by default."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from email.message import EmailMessage
from typing import ClassVar

from sovereign_agent._internal.atomic import atomic_write_text
from sovereign_agent.channels.adapter import OutboundMessage
from sovereign_agent.channels.receipts import DeliveryReceipt
from sovereign_agent.runtime import RuntimeRoot


class EmailSendBlocked(PermissionError):
    pass


@dataclass
class EmailDraft:
    to: str
    subject: str
    body: str
    path: str


class EmailAdapter:
    kind: ClassVar[str] = "channel"
    name = "email"
    channel_type = "email"
    supports_threads = False

    def __init__(
        self,
        runtime_root: RuntimeRoot,
        *,
        approval_gate: Callable[[str], bool] | None = None,
    ) -> None:
        self.runtime_root = runtime_root
        self.approval_gate = approval_gate
        self._drafts = runtime_root.ensure_directory("api") / "email-drafts"
        self._drafts.mkdir(mode=0o700, exist_ok=True)
        self._router: object | None = None

    async def setup(self, router: object) -> None:
        self._router = router

    async def teardown(self) -> None:
        self._router = None

    def ingest(self, raw: bytes) -> dict[str, str]:
        text = raw.decode("utf-8", errors="replace")
        return {"channel_type": "email", "text": text, "dedup_key": str(hash(raw))}

    def draft(self, to: str, subject: str, body: str) -> EmailDraft:
        message = EmailMessage()
        message["To"] = to
        message["Subject"] = subject
        message.set_content(body)
        path = self._drafts / f"{abs(hash((to, subject)))}.eml"
        atomic_write_text(path, message.as_string())
        return EmailDraft(to=to, subject=subject, body=body, path=str(path))

    async def deliver(
        self, platform_id: str, thread_id: str | None, message: OutboundMessage
    ) -> str | None:
        del thread_id
        allowed = self.approval_gate is not None and self.approval_gate("email.send")
        if not allowed:
            raise EmailSendBlocked("email sending is disabled unless approval policy permits it")
        receipt = DeliveryReceipt(
            attempt=1, destination=platform_id, status="sent", provider_response_id="smtp-local"
        )
        return receipt.provider_response_id
