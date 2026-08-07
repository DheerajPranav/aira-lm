"""Aira Recall — owner-scoped, lifecycle-aware keyword retrieval.

FTS5 when the SQLite build supports it, otherwise a deterministic BM25 fallback. Both
exclude forbidden states and other owners before ranking and return explainable scores.
Vector and graph retrievers are declared as deferred protocols, not implementations.
"""

from __future__ import annotations

from aira.memory.recall.bm25 import Bm25Retriever
from aira.memory.recall.factory import build_retriever
from aira.memory.recall.fts import Fts5Retriever
from aira.memory.recall.interface import GraphRetriever, Retriever, VectorRetriever
from aira.memory.recall.models import RetrievalFilters, RetrievalResult, matches_filters
from aira.memory.recall.tokenize import query_terms, tokenize

__all__ = [
    "Bm25Retriever",
    "Fts5Retriever",
    "GraphRetriever",
    "RetrievalFilters",
    "RetrievalResult",
    "Retriever",
    "VectorRetriever",
    "build_retriever",
    "matches_filters",
    "query_terms",
    "tokenize",
]
