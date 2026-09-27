# Prof Rod | Build Your Always-On AI Agent From Scratch
# Full book and learning materials: https://profrod.ai/book
# Join the Prof Rod learner community: https://profrod.ai/community
# Original source and updates: https://github.com/profrodai/sovereign-agent

"""Chapter 2 learner file: structured output, from masked logits to validation.

A model asked for JSON samples tokens like any other text, so a long answer can break its format
anywhere. Constrained decoding prevents that by masking, at every step, the tokens that could not
continue a valid answer. This file builds both ideas on a model small enough to enumerate: the
chance that an unconstrained answer stays valid, a logit mask, and the exact distribution that
masking produces, compared with the distribution you might have expected, the model's own
conditioned on validity. Chapter 2 derives each and measures a real model with and without a
schema.
"""

from __future__ import annotations

import math
from collections.abc import Callable, Iterable, Mapping, Sequence

END = "$"


def stays_valid(per_token_error: float, tokens: int) -> float:
    """Chance that every one of `tokens` independent steps avoids an invalid token."""
    return (1 - per_token_error) ** tokens


def mask(logits: Sequence[float], allowed: Iterable[int]) -> list[float]:
    """Set every disallowed logit to minus infinity, so softmax gives it probability zero."""
    keep = set(allowed)
    if not keep:
        raise ValueError("at least one token must stay allowed")
    return [z if i in keep else -math.inf for i, z in enumerate(logits)]


def softmax(logits: Sequence[float]) -> list[float]:
    top = max(logits)
    weights = [math.exp(z - top) for z in logits]
    total = sum(weights)
    return [w / total for w in weights]


# A toy model maps a prefix (a tuple of tokens) to its next-token distribution. A sequence ends
# when END is drawn.
Toy = Mapping[tuple[str, ...], Mapping[str, float]]


def sequences(model: Toy, prefix: tuple[str, ...] = ()) -> dict[tuple[str, ...], float]:
    """Every complete sequence the model can produce, with its probability."""
    out: dict[tuple[str, ...], float] = {}
    for token, p in model[prefix].items():
        if token == END:
            out[prefix] = out.get(prefix, 0.0) + p
        else:
            for sequence, q in sequences(model, prefix + (token,)).items():
                out[sequence] = out.get(sequence, 0.0) + p * q
    return out


def conditioned(
    model: Toy, valid: Callable[[tuple[str, ...]], bool]
) -> dict[tuple[str, ...], float]:
    """The model's distribution restricted to valid sequences: p(x | x valid)."""
    everything = sequences(model)
    total = sum(p for s, p in everything.items() if valid(s))
    if total == 0:
        raise ValueError("the model never produces a valid sequence")
    return {s: p / total for s, p in everything.items() if valid(s)}


def masked(
    model: Toy,
    valid: Callable[[tuple[str, ...]], bool],
    viable: Callable[[tuple[str, ...]], bool],
    prefix: tuple[str, ...] = (),
) -> dict[tuple[str, ...], float]:
    """Token-by-token constrained decoding. At each step keep END only if the sequence so far is
    valid, and another token only if the longer prefix can still become valid; renormalize what
    is kept, and continue."""
    options = {
        token: p
        for token, p in model[prefix].items()
        if (valid(prefix) if token == END else viable(prefix + (token,)))
    }
    total = sum(options.values())
    if total == 0:
        raise ValueError(f"no viable continuation after {prefix}")
    out: dict[tuple[str, ...], float] = {}
    for token, p in options.items():
        if token == END:
            out[prefix] = out.get(prefix, 0.0) + p / total
        else:
            for sequence, q in masked(model, valid, viable, prefix + (token,)).items():
                out[sequence] = out.get(sequence, 0.0) + p / total * q
    return out


def total_variation(p: Mapping, q: Mapping) -> float:
    """Half the summed absolute difference: the largest gap in probability over any event."""
    return sum(abs(p.get(k, 0.0) - q.get(k, 0.0)) for k in set(p) | set(q)) / 2
