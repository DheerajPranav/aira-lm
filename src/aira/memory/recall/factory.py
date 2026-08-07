"""Retriever selection: FTS5 when available, deterministic BM25 otherwise."""

from __future__ import annotations

from aira.memory.recall.bm25 import Bm25Retriever
from aira.memory.recall.fts import Fts5Retriever
from aira.memory.recall.interface import Retriever
from aira.memory.vault.repository import MemoryRepository


def build_retriever(repository: MemoryRepository) -> Retriever:
    """Return the best available keyword retriever for a repository.

    Uses FTS5 if the repository's search index is enabled; otherwise falls back to the
    pure-Python BM25 retriever. Both are owner-scoped, lifecycle-aware and deterministic.
    """
    if repository.fts_enabled:
        return Fts5Retriever(repository)
    return Bm25Retriever(repository)
