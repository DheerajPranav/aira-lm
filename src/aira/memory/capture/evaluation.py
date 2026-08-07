"""Deterministic utility evaluation for candidates.

Scores importance and confidence with human-readable reasons and drops low-value or
explicitly temporary text. Inferred statements need stronger evidence than explicit
requests, so bare inferred candidates sit near the threshold while explicit and
correction candidates clear it comfortably.
"""

from __future__ import annotations

import re

from aira.memory.capture.models import Assessment, Candidate
from aira.memory.domain.enums import MemoryKind, ProvenanceSource

# Minimum scores for a candidate to be admitted.
IMPORTANCE_THRESHOLD = 0.4
CONFIDENCE_THRESHOLD = 0.5

_TEMPORARY = re.compile(
    r"\b(?:for now|just for today|temporarily|this session|just testing|"
    r"ignore this|for a sec(?:ond)?|right now|at the moment)\b",
    re.IGNORECASE,
)

# Small importance bumps by kind — instructions and identity persist longest.
_KIND_BONUS: dict[MemoryKind, float] = {
    MemoryKind.INSTRUCTION: 0.15,
    MemoryKind.PREFERENCE: 0.05,
    MemoryKind.SEMANTIC: 0.05,
    MemoryKind.PROCEDURAL: 0.05,
    MemoryKind.EPISODIC: 0.0,
}


def _clamp(value: float) -> float:
    return max(0.0, min(1.0, value))


def evaluate(candidate: Candidate) -> Assessment:
    """Assess a candidate's importance, confidence and whether to keep it."""
    reasons: list[str] = []

    if _TEMPORARY.search(candidate.content):
        return Assessment(
            keep=False,
            importance=0.1,
            confidence=candidate.base_confidence,
            reasons=("dropped: explicitly temporary or low-value text",),
        )

    importance = _clamp(candidate.base_importance + _KIND_BONUS.get(candidate.kind, 0.0))
    confidence = candidate.base_confidence

    if candidate.source is ProvenanceSource.USER_EXPLICIT:
        confidence = _clamp(confidence + 0.05)
        reasons.append("explicit user request (strong evidence)")
    elif candidate.source is ProvenanceSource.USER_CORRECTION:
        importance = _clamp(importance + 0.05)
        reasons.append("user correction (strong evidence, high importance)")
    else:
        reasons.append("inferred from a user statement (weaker evidence)")

    if candidate.kind is MemoryKind.INSTRUCTION:
        reasons.append("instruction — retained with high importance")

    keep = importance >= IMPORTANCE_THRESHOLD and confidence >= CONFIDENCE_THRESHOLD
    if keep:
        reasons.append(f"admitted (importance={importance:.2f}, confidence={confidence:.2f})")
    else:
        reasons.append(
            f"below threshold (importance={importance:.2f}, confidence={confidence:.2f})"
        )

    return Assessment(
        keep=keep, importance=importance, confidence=confidence, reasons=tuple(reasons)
    )
