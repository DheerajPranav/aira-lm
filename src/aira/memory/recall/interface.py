"""Retriever protocols for Aira Recall.

The active first-release retrievers are keyword-based (FTS5 or BM25). Vector and graph
retrievers are declared here as protocols so callers can be written against them, but
they are **deferred** — there is no implementation in the first release (ADR-003). They
are interfaces, not fakes.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from aira.memory.recall.models import RetrievalFilters, RetrievalResult


@runtime_checkable
class Retriever(Protocol):
    """An owner-scoped, lifecycle-aware retriever."""

    def search(
        self,
        owner_id: str,
        query: str,
        *,
        filters: RetrievalFilters | None = None,
        limit: int = 5,
    ) -> list[RetrievalResult]:
        """Return the most relevant active memories for ``owner_id`` and ``query``."""
        ...


class VectorRetriever(Protocol):
    """Deferred: semantic (embedding) retrieval. No first-release implementation."""

    def search(
        self,
        owner_id: str,
        query: str,
        *,
        filters: RetrievalFilters | None = None,
        limit: int = 5,
    ) -> list[RetrievalResult]:
        """Deferred to a later release once a local embedding path is justified."""
        ...


class GraphRetriever(Protocol):
    """Deferred: related-memory graph retrieval. No first-release implementation."""

    def search(
        self,
        owner_id: str,
        query: str,
        *,
        filters: RetrievalFilters | None = None,
        limit: int = 5,
    ) -> list[RetrievalResult]:
        """Deferred to a later release (see the roadmap)."""
        ...
