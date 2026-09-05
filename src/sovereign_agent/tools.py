"""Bounded tool discovery. Finding a tool never grants permission to use it."""

from __future__ import annotations

import re
from dataclasses import dataclass

from sovereign_agent.isolation import IsolationPolicy


def _words(text: str) -> set[str]:
    return set(re.findall(r"[a-z0-9]+", text.lower()))


@dataclass(frozen=True)
class Tool:
    name: str
    description: str
    keywords: tuple[str, ...] = ()


@dataclass(frozen=True)
class Discovery:
    tools: tuple[Tool, ...]
    total_matches: int
    truncated: bool


class ToolCatalog:
    def __init__(self, tools: list[Tool]) -> None:
        names = [tool.name for tool in tools]
        if len(names) != len(set(names)):
            raise ValueError("tool names must be unique")
        self._tools = tuple(sorted(tools, key=lambda item: item.name))

    def discover(self, query: str, limit: int = 5) -> Discovery:
        if not 1 <= limit <= 10:
            raise ValueError("discovery limit must be between 1 and 10")
        wanted = _words(query)
        ranked: list[tuple[int, Tool]] = []
        for tool in self._tools:
            score = 3 * len(wanted & _words(tool.name))
            score += len(wanted & _words(tool.description))
            score += 2 * len(wanted & _words(" ".join(tool.keywords)))
            if score:
                ranked.append((score, tool))
        ranked.sort(key=lambda item: (-item[0], item[1].name))
        found = tuple(tool for _, tool in ranked[:limit])
        return Discovery(found, len(ranked), len(ranked) > limit)

    @staticmethod
    def authorize(tool: Tool, policy: IsolationPolicy) -> Tool:
        policy.authorize_tool(tool.name)
        return tool
