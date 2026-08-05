"""The memory lifecycle state machine.

Pure functions that take a :class:`~aira.memory.domain.records.MemoryRecord` and return
the next state, rejecting transitions that are not allowed from the current status.
Each returns a :class:`TransitionResult` carrying a human-readable reason. No audit
persistence happens here — that is Aira Trail (Step 04); this layer only computes the
next valid state.

Allowed source statuses per transition:

===========  ===================================================
Transition   Allowed from
===========  ===================================================
UPDATE       ACTIVE
SUPERSEDE    ACTIVE  (replacement must also be ACTIVE)
ARCHIVE      ACTIVE, SUPERSEDED
EXPIRE       ACTIVE, ARCHIVED
FORGET       ACTIVE, SUPERSEDED, ARCHIVED, EXPIRED
HARD_DELETE  ACTIVE, SUPERSEDED, ARCHIVED, EXPIRED, FORGOTTEN
===========  ===================================================
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import datetime
from enum import StrEnum

from aira.memory.domain.clock import ensure_utc, utc_now
from aira.memory.domain.enums import MemoryStatus
from aira.memory.domain.errors import IllegalTransitionError, ValidationError
from aira.memory.domain.records import MemoryRecord, Tombstone


class Transition(StrEnum):
    """A lifecycle state change."""

    CREATE = "create"
    UPDATE = "update"
    SUPERSEDE = "supersede"
    ARCHIVE = "archive"
    EXPIRE = "expire"
    FORGET = "forget"
    HARD_DELETE = "hard_delete"


ALLOWED_SOURCES: dict[Transition, frozenset[MemoryStatus]] = {
    Transition.UPDATE: frozenset({MemoryStatus.ACTIVE}),
    Transition.SUPERSEDE: frozenset({MemoryStatus.ACTIVE}),
    Transition.ARCHIVE: frozenset({MemoryStatus.ACTIVE, MemoryStatus.SUPERSEDED}),
    Transition.EXPIRE: frozenset({MemoryStatus.ACTIVE, MemoryStatus.ARCHIVED}),
    Transition.FORGET: frozenset(
        {
            MemoryStatus.ACTIVE,
            MemoryStatus.SUPERSEDED,
            MemoryStatus.ARCHIVED,
            MemoryStatus.EXPIRED,
        }
    ),
    Transition.HARD_DELETE: frozenset(
        {
            MemoryStatus.ACTIVE,
            MemoryStatus.SUPERSEDED,
            MemoryStatus.ARCHIVED,
            MemoryStatus.EXPIRED,
            MemoryStatus.FORGOTTEN,
        }
    ),
}


@dataclass(frozen=True, slots=True)
class TransitionResult:
    """The outcome of a single-record transition, with a human-readable reason."""

    transition: Transition
    from_status: MemoryStatus
    to_status: MemoryStatus
    at: datetime
    reason: str
    state: MemoryRecord | Tombstone


@dataclass(frozen=True, slots=True)
class SupersedeResult:
    """The outcome of superseding one memory with another.

    ``superseded`` is the prior record marked SUPERSEDED; ``replacement`` is the new
    ACTIVE record that links back to it.
    """

    at: datetime
    reason: str
    superseded: MemoryRecord
    replacement: MemoryRecord


def can_transition(transition: Transition, status: MemoryStatus) -> bool:
    """Return whether ``transition`` is allowed from ``status``."""
    return status in ALLOWED_SOURCES.get(transition, frozenset())


def _guard(transition: Transition, record: MemoryRecord) -> None:
    if not can_transition(transition, record.status):
        allowed = sorted(s.value for s in ALLOWED_SOURCES.get(transition, frozenset()))
        raise IllegalTransitionError(
            f"cannot {transition.value} a memory in status '{record.status.value}'; "
            f"allowed from {allowed}"
        )


def _stamp(now: datetime | None) -> datetime:
    return ensure_utc(now, "now") if now is not None else utc_now()


def update_memory(
    record: MemoryRecord,
    *,
    content: str | None = None,
    importance: float | None = None,
    confidence: float | None = None,
    now: datetime | None = None,
    reason: str | None = None,
) -> TransitionResult:
    """Update an ACTIVE memory in place (stays ACTIVE), refreshing ``updated_at``.

    Content, if given, is re-normalized and re-hashed; the canonical key is unchanged.
    """
    _guard(Transition.UPDATE, record)
    if content is None and importance is None and confidence is None:
        raise ValidationError("update requires at least one changed field")
    at = _stamp(now)
    base = record if content is None else record.with_content(content, now=at)
    updated = replace(
        base,
        importance=importance if importance is not None else base.importance,
        confidence=confidence if confidence is not None else base.confidence,
        updated_at=at,
    )
    return TransitionResult(
        transition=Transition.UPDATE,
        from_status=record.status,
        to_status=updated.status,
        at=at,
        reason=reason or "memory updated in place",
        state=updated,
    )


def supersede_memory(
    old: MemoryRecord,
    replacement: MemoryRecord,
    *,
    now: datetime | None = None,
    reason: str | None = None,
) -> SupersedeResult:
    """Supersede an ACTIVE memory with an ACTIVE replacement, linking the two.

    Raises:
        IllegalTransitionError: If either record is not ACTIVE.
        ValidationError: If the records belong to different owners or are the same record.
    """
    _guard(Transition.SUPERSEDE, old)
    if replacement.status is not MemoryStatus.ACTIVE:
        raise IllegalTransitionError("the replacement memory must be ACTIVE")
    if old.id == replacement.id:
        raise ValidationError("a memory cannot supersede itself")
    if old.owner_id != replacement.owner_id:
        raise ValidationError("supersede requires both memories to share an owner")
    at = _stamp(now)
    superseded = replace(
        old,
        status=MemoryStatus.SUPERSEDED,
        superseded_by=replacement.id,
        updated_at=at,
    )
    linked_replacement = replace(replacement, supersedes=old.id, updated_at=at)
    return SupersedeResult(
        at=at,
        reason=reason or f"superseded by {replacement.id}",
        superseded=superseded,
        replacement=linked_replacement,
    )


def _to_status(
    transition: Transition,
    record: MemoryRecord,
    target: MemoryStatus,
    default_reason: str,
    now: datetime | None,
    reason: str | None,
) -> TransitionResult:
    _guard(transition, record)
    at = _stamp(now)
    updated = replace(record, status=target, updated_at=at)
    return TransitionResult(
        transition=transition,
        from_status=record.status,
        to_status=target,
        at=at,
        reason=reason or default_reason,
        state=updated,
    )


def archive_memory(
    record: MemoryRecord, *, now: datetime | None = None, reason: str | None = None
) -> TransitionResult:
    """Archive a memory (ACTIVE or SUPERSEDED → ARCHIVED)."""
    return _to_status(
        Transition.ARCHIVE, record, MemoryStatus.ARCHIVED, "archived below threshold", now, reason
    )


def expire_memory(
    record: MemoryRecord, *, now: datetime | None = None, reason: str | None = None
) -> TransitionResult:
    """Expire a memory (ACTIVE or ARCHIVED → EXPIRED)."""
    return _to_status(
        Transition.EXPIRE, record, MemoryStatus.EXPIRED, "expired by retention", now, reason
    )


def forget_memory(
    record: MemoryRecord, *, now: datetime | None = None, reason: str | None = None
) -> TransitionResult:
    """Forget a memory at the user's request (most active-ish states → FORGOTTEN)."""
    return _to_status(
        Transition.FORGET, record, MemoryStatus.FORGOTTEN, "forgotten by user", now, reason
    )


def hard_delete(
    record: MemoryRecord, *, now: datetime | None = None, reason: str | None = None
) -> TransitionResult:
    """Hard-delete a memory, returning a content-free :class:`Tombstone`.

    The resulting state is a tombstone that holds only identity and deletion metadata,
    so nothing content-derived survives (invariants 2 and 7).
    """
    _guard(Transition.HARD_DELETE, record)
    at = _stamp(now)
    tombstone = Tombstone(
        id=record.id,
        owner_id=record.owner_id,
        deleted_at=at,
        reason=reason or "hard-deleted by user",
    )
    return TransitionResult(
        transition=Transition.HARD_DELETE,
        from_status=record.status,
        to_status=MemoryStatus.DELETED,
        at=at,
        reason=tombstone.reason,
        state=tombstone,
    )
