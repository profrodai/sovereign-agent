"""Generic plugin registries (v0.3, Module 3).

This subpackage names the contract every pluggable thing in sovereign-agent
shares, and provides one generic implementation. See:

  - protocol.py — the Plugin Protocol (name + kind)
  - registry.py — Registry[T], the generic collection

Module-level singletons (CHANNEL_REGISTRY, etc.) live in the subpackages
that own each plugin kind, not here.
"""

from sovereign_agent.registries.protocol import Plugin
from sovereign_agent.registries.registry import Registry

__all__ = ["Plugin", "Registry"]
