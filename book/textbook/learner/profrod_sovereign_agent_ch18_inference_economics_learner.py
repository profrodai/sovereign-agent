# Prof Rod | Build Your Always-On AI Agent From Scratch
# Full book and learning materials: https://profrod.ai/book
# Join the Prof Rod learner community: https://profrod.ai/community
# Original source and updates: https://github.com/profrodai/sovereign-agent

"""Chapter 18 learner file: what serving a model costs, built from scratch.

A model call has two phases. Prefill reads the whole prompt at once and is limited by arithmetic;
decode produces one token at a time and, at small batch sizes, is limited by how fast the weights
can be read from memory. This file computes, with the standard library only: the arithmetic and
the bytes behind one token; the decode-rate ceiling that memory bandwidth sets; the key-value
cache's memory, from the model's architecture; a latency model with a prefill and a decode term;
nearest-rank percentiles; Little's law for concurrency; and the cost of a task in tokens and cents.
Chapter 18 derives each formula and measures it on a local model.
"""

from __future__ import annotations

import math
from collections.abc import Sequence


def flops_per_token(parameters: float) -> float:
    """About two floating-point operations per parameter per token: one multiply, one add."""
    return 2 * parameters


def decode_ceiling(bandwidth_bytes_per_second: float, model_bytes: float) -> float:
    """Tokens per second when each decode step must read every weight once, at batch size one."""
    return bandwidth_bytes_per_second / model_bytes


def arithmetic_intensity(batch: int, bytes_per_parameter: float) -> float:
    """Operations per byte of weights read in one decode step: 2 * batch / bytes per parameter.

    One read of the weights serves every sequence in the batch, so intensity grows with the batch.
    Decode stays memory-bound until intensity reaches the hardware's operations-per-byte ratio.
    """
    return 2 * batch / bytes_per_parameter


def kv_cache_bytes(layers: int, kv_heads: int, head_dim: int, tokens: int, bytes_per_value=2):
    """Memory for the key-value cache: a key and a value vector per layer, KV head and token."""
    return 2 * layers * kv_heads * head_dim * bytes_per_value * tokens


def latency_seconds(prompt_tokens, output_tokens, prefill_rate, decode_rate, overhead=0.0):
    """Time for one request: fixed overhead, then prefill, then one decode step per output token."""
    return overhead + prompt_tokens / prefill_rate + output_tokens / decode_rate


def percentile(values: Sequence[float], q: float) -> float:
    """Nearest-rank percentile: the smallest value with at least q percent of values at or below."""
    if not values or not 0 < q <= 100:
        raise ValueError("need values and 0 < q <= 100")
    ordered = sorted(values)
    return ordered[math.ceil(q / 100 * len(ordered)) - 1]


def concurrency(arrivals_per_second: float, seconds_per_request: float) -> float:
    """Little's law: the average number of requests in progress is arrival rate times latency."""
    return arrivals_per_second * seconds_per_request


def cost_cents(input_tokens, output_tokens, input_dollars_per_million, output_dollars_per_million):
    """Cost of one call in cents, from per-million-token prices for input and output."""
    dollars = (
        input_tokens * input_dollars_per_million + output_tokens * output_dollars_per_million
    ) / 1_000_000
    return 100 * dollars


def loop_input_tokens(calls: int, first_prompt: int, added_per_call: int) -> int:
    """Input tokens billed over an agent loop that resends the whole transcript on every call.

    Call k (from 0) sends the first prompt plus k additions, so the total is
    calls * first_prompt + added_per_call * calls * (calls - 1) / 2: quadratic in the loop length.
    """
    return calls * first_prompt + added_per_call * calls * (calls - 1) // 2
