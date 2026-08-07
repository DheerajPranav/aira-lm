"""Result and filter types for Aira Recall."""

from __future__ import annotations

from dataclasses import dataclass, field

from aira.memory.domain.enums import MemoryKind, MemoryLifetime
from aira.memory.domain.records import MemoryRecord


@dataclass(frozen=True, slots=True)
class RetrievalFilters:
    """Optional post-owner, post-lifecycle filters applied before ranking."""

    kind: MemoryKind | None = None
    lifetime: MemoryLifetime | None = None
    project: str | None = None
    tag: str | None = None


@dataclass(frozen=True, slots=True)
class RetrievalResult:
    """One retrieved memory with its lexical relevance and an explanation.

    ``score`` is a non-negative lexical relevance (higher is more relevant); its exact
    scale depends on the backend. ``explanation`` is a safe, human-readable breakdown.
    """

    memory: MemoryRecord
    score: float
    explanation: dict[str, object] = field(default_factory=dict)


def matches_filters(record: MemoryRecord, filters: RetrievalFilters | None) -> bool:
    """Return whether a record satisfies the optional kind/lifetime/project/tag filters."""
    if filters is None:
        return True
    if filters.kind is not None and record.kind is not filters.kind:
        return False
    if filters.lifetime is not None and record.lifetime is not filters.lifetime:
        return False
    if filters.project is not None and record.project != filters.project:
        return False
    return not (filters.tag is not None and filters.tag not in record.tags)
