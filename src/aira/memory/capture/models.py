"""Types for the capture (write-path) pipeline.

A raw turn is turned into zero or more *candidates*, each *assessed* for utility, and
then resolved into concrete *operations* (remember / supersede / forget / ignore) with a
transparent policy trace. Nothing here persists; the service applies operations.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum

from aira.memory.domain.enums import (
    MemoryKind,
    MemoryLifetime,
    ProvenanceSource,
)
from aira.memory.domain.records import MemoryRecord
from aira.memory.guard.interface import GuardResult


class Speaker(StrEnum):
    """Who produced a turn. Assistant statements are not promoted to user facts."""

    USER = "user"
    ASSISTANT = "assistant"


class CandidateAction(StrEnum):
    """What a candidate proposes to do."""

    REMEMBER = "remember"
    FORGET = "forget"


@dataclass(frozen=True, slots=True)
class Candidate:
    """A structured fact/preference/instruction extracted from a turn (pre-evaluation)."""

    action: CandidateAction
    kind: MemoryKind
    canonical_key: str
    content: str
    source: ProvenanceSource
    method: str
    base_importance: float
    base_confidence: float
    lifetime: MemoryLifetime = MemoryLifetime.LONG_TERM
    project: str | None = None
    is_correction: bool = False
    source_excerpt: str = ""


@dataclass(frozen=True, slots=True)
class Assessment:
    """The evaluator's verdict for a candidate."""

    keep: bool
    importance: float
    confidence: float
    reasons: tuple[str, ...]


# --- operations (a tagged union) ---------------------------------------------------


@dataclass(frozen=True, slots=True)
class RememberOp:
    """Persist a new memory."""

    record: MemoryRecord
    reason: str


@dataclass(frozen=True, slots=True)
class SupersedeOp:
    """Replace an existing active memory with a new one sharing its canonical key."""

    old_id: str
    replacement: MemoryRecord
    reason: str


@dataclass(frozen=True, slots=True)
class ForgetOp:
    """Forget an existing memory at the user's request."""

    memory_id: str
    reason: str


@dataclass(frozen=True, slots=True)
class IgnoreOp:
    """Record that nothing was stored, with a human-readable reason."""

    reason: str
    excerpt: str = ""


CaptureOperation = RememberOp | SupersedeOp | ForgetOp | IgnoreOp


@dataclass(frozen=True, slots=True)
class TraceEntry:
    """One step of the policy trace (debug-friendly, safe to display)."""

    stage: str
    detail: str


@dataclass(frozen=True, slots=True)
class CaptureResult:
    """The outcome of processing one turn: planned operations and a policy trace."""

    operations: tuple[CaptureOperation, ...]
    trace: tuple[TraceEntry, ...]
    guard: GuardResult
    blocked: bool = field(default=False)

    def of_type(self, op_type: type) -> list[CaptureOperation]:
        """Return operations of a given type (convenience for callers and tests)."""
        return [op for op in self.operations if isinstance(op, op_type)]

    @property
    def stored_anything(self) -> bool:
        """Whether the turn resulted in at least one write operation."""
        return any(isinstance(op, RememberOp | SupersedeOp | ForgetOp) for op in self.operations)
