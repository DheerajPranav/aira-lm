"""Deterministic Okapi BM25 retriever (the fallback, and a reference implementation).

Scores the active, owner-scoped candidate set in pure Python. Because it reads live rows
through the repository (which excludes forbidden states and other owners), it can never
return forgotten, superseded, expired, deleted or cross-owner memories — there is no
separate index to fall out of sync.
"""

from __future__ import annotations

import math
from collections import Counter

from aira.memory.domain.enums import MemoryStatus
from aira.memory.domain.records import MemoryRecord
from aira.memory.recall.models import RetrievalFilters, RetrievalResult, matches_filters
from aira.memory.recall.tokenize import query_terms, tokenize
from aira.memory.vault.repository import MemoryRepository

_K1 = 1.5
_B = 0.75
_MAX_CANDIDATES = 10_000


class Bm25Retriever:
    """Keyword retrieval by BM25 over the active candidate set."""

    def __init__(self, repository: MemoryRepository, *, k1: float = _K1, b: float = _B) -> None:
        """Create a BM25 retriever over a repository."""
        self._repo = repository
        self._k1 = k1
        self._b = b

    def search(
        self,
        owner_id: str,
        query: str,
        *,
        filters: RetrievalFilters | None = None,
        limit: int = 5,
    ) -> list[RetrievalResult]:
        """Return up to ``limit`` active memories ranked by BM25 relevance."""
        terms = query_terms(query)
        if not terms or limit <= 0:
            return []

        candidates = [
            record
            for record in self._repo.list_memories(
                owner_id, statuses=(MemoryStatus.ACTIVE,), limit=_MAX_CANDIDATES
            )
            if matches_filters(record, filters)
        ]
        if not candidates:
            return []

        docs = [(record, Counter(tokenize(record.content))) for record in candidates]
        avgdl = sum(sum(counts.values()) for _, counts in docs) / len(docs)
        idf = self._idf(terms, docs)

        scored: list[RetrievalResult] = []
        for record, counts in docs:
            contributions = self._score(terms, counts, avgdl, idf)
            total = sum(contributions.values())
            if total > 0:
                scored.append(
                    RetrievalResult(
                        memory=record,
                        score=total,
                        explanation={"backend": "bm25", "terms": contributions},
                    )
                )

        # Deterministic order: score desc, then oldest first, then id.
        scored.sort(key=lambda r: (-r.score, r.memory.created_at, r.memory.id))
        return scored[:limit]

    def _idf(
        self, terms: list[str], docs: list[tuple[MemoryRecord, Counter[str]]]
    ) -> dict[str, float]:
        n = len(docs)
        idf: dict[str, float] = {}
        for term in terms:
            df = sum(1 for _, counts in docs if counts.get(term, 0) > 0)
            idf[term] = math.log(1 + (n - df + 0.5) / (df + 0.5))
        return idf

    def _score(
        self,
        terms: list[str],
        counts: Counter[str],
        avgdl: float,
        idf: dict[str, float],
    ) -> dict[str, float]:
        dl = sum(counts.values())
        contributions: dict[str, float] = {}
        for term in terms:
            f = counts.get(term, 0)
            if f == 0:
                continue
            denom = f + self._k1 * (1 - self._b + self._b * (dl / avgdl if avgdl else 0))
            contributions[term] = round(idf[term] * (f * (self._k1 + 1)) / denom, 6)
        return contributions
