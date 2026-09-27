# Prof Rod | Build Your Always-On AI Agent From Scratch
# Full book and learning materials: https://profrod.ai/book
# Join the Prof Rod learner community: https://profrod.ai/community
# Original source and updates: https://github.com/profrodai/sovereign-agent

"""Chapter 1 learner file: what a model call is, built from scratch.

A language model turns text into tokens, tokens into a probability distribution over the next
token, and a distribution into text by sampling. This file builds each step with the standard
library, small enough to read in one sitting: byte-pair encoding, a bigram model that produces
logits, softmax with temperature, sampling (including top-p), entropy, and cross-entropy with
perplexity. Chapter 1 derives every formula used here and measures them against a real model.
"""

from __future__ import annotations

import math
import random
import re
from collections import Counter, defaultdict
from collections.abc import Sequence
from dataclasses import dataclass

# Lucy's notes: the small corpus the chapter trains on. Each line is one note from the shop.
SHOP_NOTES = """\
Vanilla is running low: two tubs left in the freezer.
Chocolate is plentiful: eleven tubs in the freezer.
Strawberry has almost gone: one tub left in the freezer.
Order six tubs of vanilla before the weekend.
The supplier delivers vanilla on Tuesday morning.
A tub of vanilla costs 250 cents; a tub of chocolate costs 300 cents.
A tub of strawberry costs 275 cents.
Check the freezer before the shop opens at nine.
The morning brief lists every tub in the freezer.
Vanilla sold eight scoops before noon.
Chocolate sold five scoops before noon.
Strawberry sold three scoops before noon.
Order four tubs of strawberry before the weekend.
Do not order chocolate this week.
The supplier needs orders before Monday evening.
Lucy approves every order before the supplier sees it.
The brief says what is low and what to order.
Two tubs of vanilla is below the target of eight tubs.
One tub of strawberry is below the target of five tubs.
Eleven tubs of chocolate is above the target of six tubs.
"""

# Held out: notes the model never trains on, used to measure how well it predicts new text.
HELD_OUT_NOTES = """\
Vanilla is running low: three tubs left in the freezer.
Order five tubs of vanilla before Tuesday morning.
Strawberry sold four scoops before noon.
"""

# Split text into words with their leading space, and punctuation runs, before merging, so a
# token never spans two words. GPT-2's tokenizer uses the same idea with a larger pattern.
PRETOKEN = re.compile(r" ?[A-Za-z]+| ?[0-9]+| ?[^\sA-Za-z0-9]+|\s+")


def pretokens(text: str) -> list[bytes]:
    return [piece.encode("utf-8") for piece in PRETOKEN.findall(text)]


def _merge(symbols: list[bytes], pair: tuple[bytes, bytes]) -> list[bytes]:
    merged, i = [], 0
    while i < len(symbols):
        if i + 1 < len(symbols) and (symbols[i], symbols[i + 1]) == pair:
            merged.append(symbols[i] + symbols[i + 1])
            i += 2
        else:
            merged.append(symbols[i])
            i += 1
    return merged


def train_bpe(text: str, merges: int) -> list[tuple[bytes, bytes]]:
    """Learn up to `merges` byte-pair merges: repeatedly join the most frequent adjacent pair.

    Every token is a sequence of bytes, so any text can be encoded, whatever its alphabet. Ties
    in frequency are broken by the pair's bytes, so training is deterministic.
    """
    words = Counter(pretokens(text))
    split = {word: [bytes([b]) for b in word] for word in words}
    learned: list[tuple[bytes, bytes]] = []
    for _ in range(merges):
        pairs: Counter[tuple[bytes, bytes]] = Counter()
        for word, count in words.items():
            symbols = split[word]
            for pair in zip(symbols, symbols[1:], strict=False):
                pairs[pair] += count
        if not pairs:
            break
        best = min(pairs, key=lambda pair: (-pairs[pair], pair))
        if pairs[best] < 2:
            break
        learned.append(best)
        for word in split:
            split[word] = _merge(split[word], best)
    return learned


def encode(text: str, merges: Sequence[tuple[bytes, bytes]]) -> list[bytes]:
    """Apply the learned merges, in the order they were learned, to each pretoken."""
    tokens: list[bytes] = []
    for word in pretokens(text):
        symbols = [bytes([b]) for b in word]
        for pair in merges:
            symbols = _merge(symbols, pair)
        tokens.extend(symbols)
    return tokens


def decode(tokens: Sequence[bytes], errors: str = "strict") -> str:
    """Join the bytes and decode them. A byte-level model can sample a sequence that is not valid
    UTF-8, so text a model generated should be decoded with errors="replace"."""
    return b"".join(tokens).decode("utf-8", errors)


@dataclass(frozen=True)
class BigramModel:
    """P(next token | previous token), from counts with add-alpha smoothing.

    The smallest model with the interface every language model has: given the context, return a
    score (logit) for every token in the vocabulary.
    """

    vocabulary: tuple[bytes, ...]
    counts: dict[bytes, Counter[bytes]]
    alpha: float

    def logits(self, previous: bytes) -> list[float]:
        # log(count + alpha) differs from the log-probability only by a constant, and softmax
        # ignores constants, so these are logits.
        row = self.counts.get(previous, Counter())
        return [math.log(row[token] + self.alpha) for token in self.vocabulary]


def vocabulary(merges: Sequence[tuple[bytes, bytes]]) -> tuple[bytes, ...]:
    """Every single byte, then every merged token: any text encodes into this vocabulary."""
    return tuple(bytes([b]) for b in range(256)) + tuple(a + b for a, b in merges)


def train_bigram(
    tokens: Sequence[bytes], merges: Sequence[tuple[bytes, bytes]], alpha: float = 0.001
) -> BigramModel:
    counts: dict[bytes, Counter[bytes]] = defaultdict(Counter)
    for previous, following in zip(tokens, tokens[1:], strict=False):
        counts[previous][following] += 1
    return BigramModel(vocabulary(merges), dict(counts), alpha)


def softmax(logits: Sequence[float], temperature: float = 1.0) -> list[float]:
    """p_i = exp(z_i / T) / sum_j exp(z_j / T), computed after subtracting the largest logit.

    Subtracting a constant changes no probability but keeps exp() from overflowing.
    Temperature 0 means greedy decoding: all probability on the largest logit.
    """
    if temperature == 0:
        best = max(range(len(logits)), key=lambda i: logits[i])
        return [1.0 if i == best else 0.0 for i in range(len(logits))]
    top = max(logits)
    weights = [math.exp((z - top) / temperature) for z in logits]
    total = sum(weights)
    return [w / total for w in weights]


def top_p(probabilities: Sequence[float], p: float) -> list[float]:
    """Keep the smallest set of most-likely tokens whose total is at least p, renormalized."""
    order = sorted(range(len(probabilities)), key=lambda i: -probabilities[i])
    kept, total = set(), 0.0
    for i in order:
        kept.add(i)
        total += probabilities[i]
        if total >= p:
            break
    return [probabilities[i] / total if i in kept else 0.0 for i in range(len(probabilities))]


def sample(probabilities: Sequence[float], rng: random.Random) -> int:
    """Draw one index with the given probabilities (inverse transform sampling)."""
    u, running = rng.random(), 0.0
    for i, probability in enumerate(probabilities):
        running += probability
        if u < running:
            return i
    return max(i for i, probability in enumerate(probabilities) if probability > 0)


def generate(
    model: BigramModel,
    start: bytes,
    length: int,
    rng: random.Random,
    temperature: float = 1.0,
    nucleus: float = 1.0,
) -> list[bytes]:
    tokens = [start]
    for _ in range(length):
        probabilities = top_p(softmax(model.logits(tokens[-1]), temperature), nucleus)
        tokens.append(model.vocabulary[sample(probabilities, rng)])
    return tokens


def entropy_bits(probabilities: Sequence[float]) -> float:
    """H(p) = -sum p log2 p: the average surprise, in bits, of one draw."""
    return -sum(p * math.log2(p) for p in probabilities if p > 0)


def cross_entropy_bits(model: BigramModel, tokens: Sequence[bytes]) -> float:
    """Average -log2 P(token | previous) over a text: bits per token the model pays to predict it.

    Held-out text must be encoded with the model's own merges; its vocabulary contains every
    byte, so every such token can be scored.
    """
    index = {token: i for i, token in enumerate(model.vocabulary)}
    total = 0.0
    for previous, following in zip(tokens, tokens[1:], strict=False):
        total -= math.log2(softmax(model.logits(previous))[index[following]])
    return total / (len(tokens) - 1)


def perplexity(model: BigramModel, tokens: Sequence[bytes]) -> float:
    """2 ** cross-entropy: how many equally likely tokens the model is, on average, torn between."""
    return 2 ** cross_entropy_bits(model, tokens)


def cost_cents(
    input_tokens: int, output_tokens: int, input_per_million: float, output_per_million: float
) -> float:
    """What a call costs when a provider prices input and output tokens per million, in cents."""
    return (input_tokens * input_per_million + output_tokens * output_per_million) / 1_000_000
