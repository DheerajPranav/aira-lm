"""Deterministic score fusion for retrieved memories.

Combines lexical relevance with importance, confidence, recency, reinforcement, project
relevance, kind priority and a decay penalty into one score, using configurable weights.
Every component is normalized to [0, 1] and every result carries a full weighted
breakdown. As defense in depth, non-active memories are dropped even if a retriever ever
returned one (invariant 2).
"""

from __future__ import annotations

import math
from datetime import datetime

from aira.config import DecayConfig, RetrievalConfig
from aira.memory.domain.enums import MemoryKind, MemoryStatus
from aira.memory.domain.records import MemoryRecord
from aira.memory.ranking.models import RankContext, RankedMemory, ScoreComponents
from aira.memory.recall.models import RetrievalResult

RECENCY_HALF_LIFE_DAYS = 30.0
REINFORCEMENT_CAP = 5.0

_KIND_PRIORITY: dict[MemoryKind, float] = {
    MemoryKind.INSTRUCTION: 1.0,
    MemoryKind.PREFERENCE: 0.8,
    MemoryKind.SEMANTIC: 0.7,
    MemoryKind.PROCEDURAL: 0.6,
    MemoryKind.EPISODIC: 0.4,
}


class RankingWeights:
    """Weights for each score component, sourced from configuration."""

    def __init__(
        self,
        *,
        lexical: float,
        importance: float,
        confidence: float,
        recency: float,
        reinforcement: float,
        project: float,
        kind: float,
        decay_penalty: float,
    ) -> None:
        self.lexical = lexical
        self.importance = importance
        self.confidence = confidence
        self.recency = recency
        self.reinforcement = reinforcement
        self.project = project
        self.kind = kind
        self.decay_penalty = decay_penalty

    @classmethod
    def from_config(cls, cfg: RetrievalConfig) -> RankingWeights:
        """Build weights from the ``[retrieval]`` configuration section."""
        return cls(
            lexical=cfg.lexical_weight,
            importance=cfg.importance_weight,
            confidence=cfg.confidence_weight,
            recency=cfg.recency_weight,
            reinforcement=cfg.reinforcement_weight,
            project=cfg.project_weight,
            kind=cfg.kind_weight,
            decay_penalty=cfg.decay_penalty_weight,
        )


class DecayParams:
    """Per-kind decay half-lives (days), sourced from the ``[decay]`` section."""

    def __init__(
        self, *, episodic: float, semantic: float, preference: float, instruction: float
    ) -> None:
        self.episodic = episodic
        self.semantic = semantic
        self.preference = preference
        self.instruction = instruction

    @classmethod
    def from_config(cls, cfg: DecayConfig) -> DecayParams:
        """Build decay parameters from the ``[decay]`` configuration section."""
        return cls(
            episodic=cfg.episodic_half_life_days,
            semantic=cfg.semantic_half_life_days,
            preference=cfg.preference_half_life_days,
            instruction=cfg.instruction_half_life_days,
        )

    def half_life(self, kind: MemoryKind) -> float:
        """Return the decay half-life (days) for a memory kind."""
        if kind is MemoryKind.EPISODIC:
            return self.episodic
        if kind is MemoryKind.PREFERENCE:
            return self.preference
        if kind is MemoryKind.INSTRUCTION:
            return self.instruction
        return self.semantic  # semantic and procedural


def _age_days(now: datetime, record: MemoryRecord) -> float:
    return max(0.0, (now - record.updated_at).total_seconds() / 86400.0)


class Ranker:
    """Fuses retrieval results into a deterministically ordered ranked list."""

    def __init__(self, weights: RankingWeights, decay: DecayParams) -> None:
        """Create a ranker over configured weights and decay parameters."""
        self._w = weights
        self._decay = decay

    def rank(
        self,
        results: list[RetrievalResult],
        *,
        now: datetime,
        context: RankContext | None = None,
    ) -> list[RankedMemory]:
        """Return results scored and ordered by fused relevance (descending)."""
        ctx = context or RankContext()
        active = [r for r in results if r.memory.status is MemoryStatus.ACTIVE]
        if not active:
            return []

        max_lexical = max((r.score for r in active), default=0.0)
        ranked = [self._score(r, max_lexical, now, ctx) for r in active]
        # Deterministic order: score desc, then oldest first, then id.
        ranked.sort(key=lambda rm: (-rm.score, rm.memory.created_at, rm.memory.id))
        return ranked

    def _score(
        self,
        result: RetrievalResult,
        max_lexical: float,
        now: datetime,
        ctx: RankContext,
    ) -> RankedMemory:
        record = result.memory
        age = _age_days(now, record)
        half_life = self._decay.half_life(record.kind)

        components = ScoreComponents(
            lexical=(result.score / max_lexical) if max_lexical > 0 else 0.0,
            importance=record.importance,
            confidence=record.confidence,
            recency=math.exp(-age / RECENCY_HALF_LIFE_DAYS),
            reinforcement=min(record.reinforcement_count / REINFORCEMENT_CAP, 1.0),
            project=1.0 if ctx.project is not None and record.project == ctx.project else 0.0,
            kind_priority=_KIND_PRIORITY.get(record.kind, 0.5),
            decay_penalty=1.0 - math.exp(-age / half_life),
        )
        breakdown = {
            "lexical": round(self._w.lexical * components.lexical, 6),
            "importance": round(self._w.importance * components.importance, 6),
            "confidence": round(self._w.confidence * components.confidence, 6),
            "recency": round(self._w.recency * components.recency, 6),
            "reinforcement": round(self._w.reinforcement * components.reinforcement, 6),
            "project": round(self._w.project * components.project, 6),
            "kind_priority": round(self._w.kind * components.kind_priority, 6),
            "decay_penalty": round(-self._w.decay_penalty * components.decay_penalty, 6),
        }
        score = round(sum(breakdown.values()), 6)
        return RankedMemory(memory=record, score=score, components=components, breakdown=breakdown)
