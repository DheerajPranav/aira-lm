"""SQLite FTS5 keyword retriever.

Uses the FTS5 index (maintained by the repository to hold only active content) as a
candidate generator, then re-fetches each candidate through the owner-scoped,
active-only ``get`` so nothing forbidden or cross-owner can appear even if an index
entry were ever stale. Results keep the FTS relevance order.
"""

from __future__ import annotations

from aira.memory.recall.models import RetrievalFilters, RetrievalResult, matches_filters
from aira.memory.recall.tokenize import fts_match_expression, query_terms
from aira.memory.vault.repository import MemoryRepository

_MAX_CANDIDATES = 200


class Fts5Retriever:
    """Keyword retrieval backed by SQLite FTS5."""

    def __init__(self, repository: MemoryRepository, *, candidate_multiplier: int = 5) -> None:
        """Create an FTS5 retriever over a repository whose search index is enabled."""
        self._repo = repository
        self._candidate_multiplier = candidate_multiplier

    def search(
        self,
        owner_id: str,
        query: str,
        *,
        filters: RetrievalFilters | None = None,
        limit: int = 5,
    ) -> list[RetrievalResult]:
        """Return up to ``limit`` active memories ranked by FTS5 relevance."""
        terms = query_terms(query)
        if not terms or limit <= 0:
            return []

        candidate_limit = min(_MAX_CANDIDATES, max(limit * self._candidate_multiplier, limit))
        pairs = self._repo.fts_search(fts_match_expression(terms), limit=candidate_limit)

        results: list[RetrievalResult] = []
        for memory_id, rank in pairs:
            record = self._repo.get(owner_id, memory_id)  # owner-scoped, active-only
            if record is None or not matches_filters(record, filters):
                continue
            results.append(
                RetrievalResult(
                    memory=record,
                    score=-rank,  # FTS5 bm25(): lower is better, so negate for higher-is-better
                    explanation={"backend": "fts5", "rank": round(rank, 6)},
                )
            )
            if len(results) >= limit:
                break
        return results
