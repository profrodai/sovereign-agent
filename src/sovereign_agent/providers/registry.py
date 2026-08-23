"""Provider registry built on the generic Plugin/Registry abstraction."""

from sovereign_agent.registries import Registry

from .protocol import AgentProvider


class ProviderRegistry(Registry[AgentProvider]):
    def __init__(self) -> None:
        super().__init__(kind_filter="provider")


PROVIDER_REGISTRY = ProviderRegistry()

__all__ = ["PROVIDER_REGISTRY", "ProviderRegistry"]
