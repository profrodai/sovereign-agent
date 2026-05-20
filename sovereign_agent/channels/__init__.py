"""Channels: where messages come from (v0.3, Module 1).

This package adds inbound/outbound channels to sovereign-agent. The public
surface is small:

  ChannelAdapter   — the Protocol an adapter satisfies (no base class needed)
  InboundEvent     — one message arriving from a channel
  OutboundMessage  — one message the agent wants delivered
  ChannelRegistry  — the set of adapters an orchestrator runs
  InboundRouter    — turns events into sessions (owned by the Orchestrator)
  CliChannelAdapter — the first concrete adapter; line-delimited JSON over
                      a Unix socket

See docs/modules/channels.md and Chapter 6 for the design walkthrough.
"""

from sovereign_agent.channels.adapter import (
    ChannelAdapter,
    InboundEvent,
    OutboundMessage,
)
from sovereign_agent.channels.cli import CliChannelAdapter, default_socket_path
from sovereign_agent.channels.registry import ChannelRegistry
from sovereign_agent.channels.router import InboundRouter

__all__ = [
    "ChannelAdapter",
    "InboundEvent",
    "OutboundMessage",
    "ChannelRegistry",
    "InboundRouter",
    "CliChannelAdapter",
    "default_socket_path",
]
