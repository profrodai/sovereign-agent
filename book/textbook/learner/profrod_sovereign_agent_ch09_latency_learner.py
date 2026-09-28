# Prof Rod | Build Your Always-On AI Agent From Scratch
# Full book and learning materials: https://profrod.ai/book
# Join the Prof Rod learner community: https://profrod.ai/community
# Original source and updates: https://github.com/profrodai/sovereign-agent

"""Chapter 9 learner file: the latency a person feels in a chat.

A reply from a model arrives in two phases: prefill reads the whole prompt, then decode writes
the answer one token at a time. This file computes, with the standard library only, a least-
squares line through measured times, the time to the first token and to the whole reply, and how
much prompt a conversation makes the model read with and without a prefix cache. Chapter 9 derives
each and measures them on local models.
"""

from __future__ import annotations

from collections.abc import Sequence


def fit_line(xs: Sequence[float], ys: Sequence[float]) -> tuple[float, float]:
    """Least-squares intercept and slope of y = a + b * x."""
    n = len(xs)
    mean_x, mean_y = sum(xs) / n, sum(ys) / n
    slope = sum((x - mean_x) * (y - mean_y) for x, y in zip(xs, ys, strict=True)) / sum(
        (x - mean_x) ** 2 for x in xs
    )
    return mean_y - slope * mean_x, slope


def prefill_seconds(prompt_tokens: int, per_token: float, per_token_squared: float) -> float:
    """Prefill time for n prompt tokens: b * n for the work every token needs, plus c * n^2 for
    attention, in which each token is compared with every token before it."""
    return per_token * prompt_tokens + per_token_squared * prompt_tokens**2


def first_token_seconds(
    prompt_tokens: int, per_token: float, per_token_squared: float, decode_per_token: float
) -> float:
    """Time to the first generated token: read the prompt, then write one token."""
    return prefill_seconds(prompt_tokens, per_token, per_token_squared) + decode_per_token


def reply_seconds(
    prompt_tokens: int,
    output_tokens: int,
    per_token: float,
    per_token_squared: float,
    decode_per_token: float,
) -> float:
    """Time to the whole reply: the first token, then the rest one at a time."""
    first = first_token_seconds(prompt_tokens, per_token, per_token_squared, decode_per_token)
    return first + (output_tokens - 1) * decode_per_token


def conversation_prefill(turns: int, tokens_per_turn: int, cached: bool) -> int:
    """Prompt tokens the model reads over a conversation in which every turn adds
    `tokens_per_turn` to the history. Without a prefix cache, turn i rereads all i turns, a total
    of m * k * (k + 1) / 2; with one, each turn reads only what is new, a total of m * k."""
    if cached:
        return turns * tokens_per_turn
    return tokens_per_turn * turns * (turns + 1) // 2
