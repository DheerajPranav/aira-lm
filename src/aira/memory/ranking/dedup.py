"""Deterministic deduplication of ranked memories.

Walks the ranked list in order and keeps the first memory seen for each canonical key
and, among survivors, for each content hash. Because the list is already deterministically
ordered, the survivor is always the highest-ranked representative.
"""

from __future__ import annotations

from aira.memory.ranking.models import ContextDecision, RankedMemory


def deduplicate(ranked: list[RankedMemory]) -> tuple[list[RankedMemory], list[ContextDecision]]:
    """Return (kept, dropped-decisions) after canonical and near-identical dedup."""
    kept: list[RankedMemory] = []
    dropped: list[ContextDecision] = []
    seen_keys: set[str] = set()
    seen_hashes: set[str] = set()

    for rm in ranked:
        key = rm.memory.canonical_key
        content_hash = rm.memory.content_hash
        if key in seen_keys:
            dropped.append(
                ContextDecision(rm.memory.id, False, "duplicate canonical key (kept higher-ranked)")
            )
            continue
        if content_hash in seen_hashes:
            dropped.append(
                ContextDecision(rm.memory.id, False, "near-identical content (kept higher-ranked)")
            )
            continue
        seen_keys.add(key)
        seen_hashes.add(content_hash)
        kept.append(rm)

    return kept, dropped
