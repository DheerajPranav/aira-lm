"""Append-only audit event model.

An :class:`AuditEvent` is written in the same transaction as the memory state change it
describes (invariant 11). Its ``detail`` mapping is JSON-safe and must never contain
memory content or content-derived fields; for hard deletion it stays empty (invariants
2 and 7).
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum

from aira.memory.domain.clock import ensure_utc
from aira.memory.domain.enums import MemoryStatus
from aira.memory.domain.errors import ValidationError

# Fields that must never appear in an audit event's detail (content-derived).
_FORBIDDEN_DETAIL_KEYS = frozenset({"content", "content_hash", "canonical_key", "source_excerpt"})


class AuditAction(StrEnum):
    """The kind of lifecycle change an audit event records."""

    CREATE = "create"
    UPDATE = "update"
    SUPERSEDE = "supersede"
    ARCHIVE = "archive"
    EXPIRE = "expire"
    FORGET = "forget"
    HARD_DELETE = "hard_delete"
    IMPORT = "import"


def new_event_id() -> str:
    """Return a fresh unique audit-event id."""
    return uuid.uuid4().hex


@dataclass(frozen=True, slots=True)
class AuditEvent:
    """One append-only audit record for a memory lifecycle change."""

    id: str
    memory_id: str
    owner_id: str
    action: AuditAction
    at: datetime
    reason: str
    from_status: MemoryStatus | None = None
    to_status: MemoryStatus | None = None
    detail: dict[str, object] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.id.strip():
            raise ValidationError("audit event id must not be empty")
        if not self.memory_id.strip():
            raise ValidationError("audit event memory_id must not be empty")
        if not self.owner_id.strip():
            raise ValidationError("audit event owner_id must not be empty")
        ensure_utc(self.at, "audit.at")
        forbidden = _FORBIDDEN_DETAIL_KEYS & set(self.detail)
        if forbidden:
            raise ValidationError(
                f"audit detail must not contain content-derived keys: {sorted(forbidden)}"
            )
