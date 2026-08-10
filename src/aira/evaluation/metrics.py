"""Deterministic retrieval metrics for Aira Bench.

Pure functions over an ordered list of retrieved ids and a set of relevant ids. No LLM
judge is used anywhere; relevance is decided by known expected facts (substring match at
the scenario level, resolved to ids before these functions are called).
"""

from __future__ import annotations

from collections.abc import Sequence


def precision(retrieved: Sequence[str], relevant: set[str]) -> float:
    """Fraction of retrieved items that are relevant (0 when nothing retrieved)."""
    if not retrieved:
        return 0.0
    hits = sum(1 for item in retrieved if item in relevant)
    return hits / len(retrieved)


def recall(retrieved: Sequence[str], relevant: set[str]) -> float:
    """Fraction of relevant items that were retrieved (1.0 when nothing is relevant)."""
    if not relevant:
        return 1.0
    hits = sum(1 for item in relevant if item in set(retrieved))
    return hits / len(relevant)


def recall_at_k(retrieved: Sequence[str], relevant: set[str], k: int) -> float:
    """Recall considering only the top-k retrieved items."""
    return recall(list(retrieved)[:k], relevant)


def reciprocal_rank(retrieved: Sequence[str], relevant: set[str]) -> float:
    """1/rank of the first relevant retrieved item, or 0.0 if none is relevant."""
    for index, item in enumerate(retrieved, start=1):
        if item in relevant:
            return 1.0 / index
    return 0.0


def rate(numerator: int, denominator: int) -> float:
    """A safe ratio; 0.0 when the denominator is 0."""
    return numerator / denominator if denominator else 0.0


def mean(values: Sequence[float]) -> float:
    """Arithmetic mean; 0.0 for an empty sequence."""
    return sum(values) / len(values) if values else 0.0
