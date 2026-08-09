"""Type-specific decay scoring for Aira Fade.

Decay is a deterministic function of a memory's age since it was last touched
(``updated_at``, so an update or reinforcement refreshes it) and a per-kind half-life
from the ``[decay]`` configuration. The score is in (0, 1]; lower means staler.
"""

from __future__ import annotations

import math
from datetime import datetime

from aira.config import DecayConfig
from aira.memory.domain.enums import MemoryKind
from aira.memory.domain.records import MemoryRecord


def half_life_days(kind: MemoryKind, cfg: DecayConfig) -> float:
    """Return the decay half-life (days) for a memory kind."""
    if kind is MemoryKind.EPISODIC:
        return cfg.episodic_half_life_days
    if kind is MemoryKind.PREFERENCE:
        return cfg.preference_half_life_days
    if kind is MemoryKind.INSTRUCTION:
        return cfg.instruction_half_life_days
    return cfg.semantic_half_life_days  # semantic and procedural


def decay_score(record: MemoryRecord, now: datetime, cfg: DecayConfig) -> float:
    """Return the decay score in (0, 1]; 1.0 is fresh, approaching 0 as it ages."""
    age_days = max(0.0, (now - record.updated_at).total_seconds() / 86400.0)
    return math.exp(-age_days / half_life_days(record.kind, cfg))
