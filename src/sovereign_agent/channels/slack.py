"""Optional Slack adapter. Works without slack_sdk using inbound payloads."""

from __future__ import annotations

from collections.abc import Callable
from typing import ClassVar

from sovereign_agent.channels.webhook import WebhookAdapter
from sovereign_agent.runtime import RuntimeRoot


class SlackAdapter(WebhookAdapter):
    name = "slack"
    channel_type = "slack"
    kind: ClassVar[str] = "channel"

    def __init__(
        self,
        runtime_root: RuntimeRoot,
        secret: bytes,
        *,
        approval_gate: Callable[[str], bool] | None = None,
    ) -> None:
        super().__init__(runtime_root, secret, approval_gate=approval_gate)
