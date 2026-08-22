"""Optional Slack adapter. Works without slack_sdk using inbound payloads."""

from __future__ import annotations

from typing import ClassVar

from sovereign_agent.channels.webhook import WebhookAdapter


class SlackAdapter(WebhookAdapter):
    name = "slack"
    channel_type = "slack"
    kind: ClassVar[str] = "channel"

    def __init__(self, *args: object, **kwargs: object) -> None:
        try:
            import slack_sdk  # noqa: F401
        except ImportError:
            pass
        super().__init__(*args, **kwargs)  # type: ignore[misc]
