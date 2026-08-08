"""Types for ranking and context construction."""

from __future__ import annotations

from dataclasses import dataclass, field

from aira.memory.domain.records import MemoryRecord


@dataclass(frozen=True, slots=True)
class RankContext:
    """Optional context that influences ranking (e.g. the active project)."""

    project: str | None = None


@dataclass(frozen=True, slots=True)
class ScoreComponents:
    """The normalized [0, 1] signals that feed score fusion."""

    lexical: float
    importance: float
    confidence: float
    recency: float
    reinforcement: float
    project: float
    kind_priority: float
    decay_penalty: float


@dataclass(frozen=True, slots=True)
class RankedMemory:
    """A candidate memory with its fused score and a full, weighted breakdown."""

    memory: MemoryRecord
    score: float
    components: ScoreComponents
    breakdown: dict[str, float]


@dataclass(frozen=True, slots=True)
class ContextDecision:
    """Why a memory was included in or excluded from the composed context."""

    memory_id: str
    included: bool
    reason: str


@dataclass(frozen=True, slots=True)
class ContextItem:
    """One rendered line of the untrusted-memory block."""

    index: int
    memory_id: str
    text: str


@dataclass(frozen=True, slots=True)
class ContextBlock:
    """A bounded, delimited, untrusted-memory block ready to hand to a backend."""

    text: str
    items: tuple[ContextItem, ...]
    decisions: tuple[ContextDecision, ...]
    token_count: int
    budget: int
    top_k: int
    debug: bool = field(default=False)

    @property
    def is_empty(self) -> bool:
        """Whether no memory was included."""
        return not self.items
