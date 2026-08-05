"""Aira Memory domain layer: typed records and a validated lifecycle state machine.

Storage-independent. Import the enums, records, hashing helpers and lifecycle functions
from here. Persistence (Aira Vault), audit (Aira Trail), capture, retrieval and ranking
build on this layer in later steps.
"""

from __future__ import annotations

from aira.memory.domain.clock import ensure_utc, utc_now
from aira.memory.domain.enums import (
    RETRIEVABLE_STATUSES,
    ConsentCategory,
    MemoryAction,
    MemoryKind,
    MemoryLifetime,
    MemoryStatus,
    ProvenanceSource,
    RetentionPolicy,
    Sensitivity,
    is_retrievable,
)
from aira.memory.domain.errors import (
    DomainError,
    IllegalTransitionError,
    ValidationError,
)
from aira.memory.domain.hashing import (
    canonical_key,
    content_digest,
    normalize_content,
)
from aira.memory.domain.lifecycle import (
    ALLOWED_SOURCES,
    SupersedeResult,
    Transition,
    TransitionResult,
    archive_memory,
    can_transition,
    expire_memory,
    forget_memory,
    hard_delete,
    supersede_memory,
    update_memory,
)
from aira.memory.domain.records import MemoryRecord, Provenance, Tombstone, make_memory

__all__ = [
    "ALLOWED_SOURCES",
    "RETRIEVABLE_STATUSES",
    "ConsentCategory",
    "DomainError",
    "IllegalTransitionError",
    "MemoryAction",
    "MemoryKind",
    "MemoryLifetime",
    "MemoryRecord",
    "MemoryStatus",
    "Provenance",
    "ProvenanceSource",
    "RetentionPolicy",
    "Sensitivity",
    "SupersedeResult",
    "Tombstone",
    "Transition",
    "TransitionResult",
    "ValidationError",
    "archive_memory",
    "can_transition",
    "canonical_key",
    "content_digest",
    "ensure_utc",
    "expire_memory",
    "forget_memory",
    "hard_delete",
    "is_retrievable",
    "make_memory",
    "normalize_content",
    "supersede_memory",
    "update_memory",
    "utc_now",
]
