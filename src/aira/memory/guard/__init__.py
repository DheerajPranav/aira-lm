"""Aira Guard — the pre-persistence safety and privacy gate.

Deterministic and offline: no third-party PII service, no LLM. It detects and redacts
secrets, flags do-not-remember and instruction-override language, classifies
sensitivity, and never emits a raw secret. Capture (Step 05) runs the guard before any
evaluation or persistence.
"""

from __future__ import annotations

from aira.memory.guard.guard import (
    DEFAULT_MAX_INPUT_BYTES,
    DeterministicGuard,
    classify_sensitivity,
    default_guard,
)
from aira.memory.guard.interface import (
    REDACTION_TOKENS,
    Guard,
    GuardCategory,
    GuardDecision,
    GuardEvent,
    GuardFinding,
    GuardResult,
)

__all__ = [
    "DEFAULT_MAX_INPUT_BYTES",
    "REDACTION_TOKENS",
    "DeterministicGuard",
    "Guard",
    "GuardCategory",
    "GuardDecision",
    "GuardEvent",
    "GuardFinding",
    "GuardResult",
    "classify_sensitivity",
    "default_guard",
]
