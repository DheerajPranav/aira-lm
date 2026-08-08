"""Aira ranking — deterministic score fusion, deduplication and context construction.

Turns retrieval results into a ranked list (with full score breakdowns), deduplicates
canonical and near-identical memories, and composes a bounded, delimited untrusted-memory
block within an exact byte-token budget. No response generation, vector retrieval or
learned reranker here.
"""

from __future__ import annotations

from aira.memory.ranking.context import (
    CLOSE_TAG,
    OPEN_TAG,
    PREAMBLE,
    ContextComposer,
    compose_memory_context,
)
from aira.memory.ranking.dedup import deduplicate
from aira.memory.ranking.models import (
    ContextBlock,
    ContextDecision,
    ContextItem,
    RankContext,
    RankedMemory,
    ScoreComponents,
)
from aira.memory.ranking.scoring import DecayParams, Ranker, RankingWeights
from aira.memory.ranking.tokenizer import ByteTokenizer, Tokenizer

__all__ = [
    "CLOSE_TAG",
    "OPEN_TAG",
    "PREAMBLE",
    "ByteTokenizer",
    "ContextBlock",
    "ContextComposer",
    "ContextDecision",
    "ContextItem",
    "DecayParams",
    "RankContext",
    "RankedMemory",
    "Ranker",
    "RankingWeights",
    "ScoreComponents",
    "Tokenizer",
    "compose_memory_context",
    "deduplicate",
]
