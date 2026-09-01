"""Provider registry. Cursor is a first-class adapter, equal to Claude and Codex."""

from sovereign_agent.errors import Refusal
from sovereign_agent.providers.base import IntelligenceProvider
from sovereign_agent.providers.claude import ClaudeProvider
from sovereign_agent.providers.codex import CodexProvider
from sovereign_agent.providers.cursor import CursorProvider
from sovereign_agent.providers.openai_compatible import OpenAICompatibleProvider
from sovereign_agent.providers.scripted import ScriptedProvider

PROVIDERS: dict[str, IntelligenceProvider] = {
    "scripted": ScriptedProvider(),
    "claude": ClaudeProvider(),
    "codex": CodexProvider(),
    "cursor": CursorProvider(),
    "ollama": OpenAICompatibleProvider(),
}


def get_provider(name: str) -> IntelligenceProvider:
    provider = PROVIDERS.get(name)
    if provider is None:
        raise Refusal(
            happened=f"Unknown provider {name}.",
            why="An actor binds to a registry name, not to a model nickname.",
            inspect="sovereign-agent doctor",
            next_command="Use scripted, claude, codex, cursor, or ollama.",
        )
    return provider
