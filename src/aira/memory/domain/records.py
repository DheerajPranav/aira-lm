"""Immutable, validated domain records for Aira Memory.

A :class:`MemoryRecord` is a frozen value object that validates itself on construction:
required owner and provenance, scores in range, UTC-aware and ordered timestamps, and a
content hash that matches its content. A :class:`Tombstone` is the result of a hard
delete and, by type, carries no content or content-derived metadata (invariant 2, 7).

No persistence, extraction, retrieval or secret detection lives here.
"""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from datetime import datetime

from aira.memory.domain.clock import ensure_utc, utc_now
from aira.memory.domain.enums import (
    ConsentCategory,
    MemoryKind,
    MemoryLifetime,
    MemoryStatus,
    ProvenanceSource,
    RetentionPolicy,
    Sensitivity,
)
from aira.memory.domain.errors import ValidationError
from aira.memory.domain.hashing import canonical_key as derive_canonical_key
from aira.memory.domain.hashing import content_digest, normalize_content


@dataclass(frozen=True, slots=True)
class Provenance:
    """How the system learned a memory. Required on every :class:`MemoryRecord`."""

    source: ProvenanceSource
    actor: str
    method: str
    captured_at: datetime
    source_excerpt: str | None = None

    def __post_init__(self) -> None:
        if not self.actor.strip():
            raise ValidationError("provenance.actor must not be empty")
        if not self.method.strip():
            raise ValidationError("provenance.method must not be empty")
        ensure_utc(self.captured_at, "provenance.captured_at")


@dataclass(frozen=True, slots=True)
class MemoryRecord:
    """A single, validated unit of memory.

    Construct new records with :func:`make_memory`, which normalizes content and
    computes the content hash and a default canonical key. Lifecycle changes are applied
    by :mod:`aira.memory.domain.lifecycle`, which returns new instances.
    """

    id: str
    owner_id: str
    kind: MemoryKind
    lifetime: MemoryLifetime
    status: MemoryStatus
    content: str
    content_hash: str
    canonical_key: str
    provenance: Provenance
    sensitivity: Sensitivity
    consent: ConsentCategory
    retention: RetentionPolicy
    importance: float
    confidence: float
    created_at: datetime
    updated_at: datetime
    expires_at: datetime | None = None
    supersedes: str | None = None
    superseded_by: str | None = None
    reinforcement_count: int = 0
    tags: tuple[str, ...] = ()
    project: str | None = None
    idempotency_key: str | None = None

    def __post_init__(self) -> None:
        if not self.id.strip():
            raise ValidationError("id must not be empty")
        if not self.owner_id.strip():
            raise ValidationError("owner_id must not be empty")
        if not self.content.strip():
            raise ValidationError("content must not be empty")

        if self.status is MemoryStatus.DELETED:
            raise ValidationError("a MemoryRecord cannot hold DELETED status; use a Tombstone")
        if self.retention is RetentionPolicy.PROHIBITED:
            raise ValidationError("a memory with PROHIBITED retention must not be persisted")

        # Content hash must match the (normalized) content: guarantees deterministic,
        # tamper-evident hashing and that callers used the factory / lifecycle helpers.
        expected = content_digest(self.content)
        if self.content_hash != expected:
            raise ValidationError("content_hash does not match content")
        if self.content != normalize_content(self.content):
            raise ValidationError("content must be normalized")

        _check_unit("importance", self.importance)
        _check_unit("confidence", self.confidence)
        if self.reinforcement_count < 0:
            raise ValidationError("reinforcement_count must be >= 0")

        ensure_utc(self.created_at, "created_at")
        ensure_utc(self.updated_at, "updated_at")
        if self.updated_at < self.created_at:
            raise ValidationError("updated_at must not precede created_at")
        if self.expires_at is not None:
            ensure_utc(self.expires_at, "expires_at")
            if self.expires_at < self.created_at:
                raise ValidationError("expires_at must not precede created_at")
        if self.retention is RetentionPolicy.FIXED_EXPIRY and self.expires_at is None:
            raise ValidationError("FIXED_EXPIRY retention requires expires_at")

        # Superseding links must be consistent with status. A SUPERSEDED memory must
        # point to its successor; an ACTIVE memory must not (it has no successor yet).
        # Later inactive states (archived/expired/forgotten) may retain the link as
        # history if the memory was superseded before reaching them.
        if self.status is MemoryStatus.SUPERSEDED and self.superseded_by is None:
            raise ValidationError("a SUPERSEDED memory must record superseded_by")
        if self.status is MemoryStatus.ACTIVE and self.superseded_by is not None:
            raise ValidationError("an ACTIVE memory must not record superseded_by")
        if self.superseded_by == self.id:
            raise ValidationError("a memory cannot supersede itself")
        if self.supersedes == self.id:
            raise ValidationError("a memory cannot supersede itself")

    def with_content(self, content: str, *, now: datetime | None = None) -> MemoryRecord:
        """Return a copy with normalized new content, refreshed hash and ``updated_at``.

        Does not change ``canonical_key`` (the fact's identity is stable across edits).
        """
        normalized = normalize_content(content)
        stamp = ensure_utc(now, "now") if now is not None else utc_now()
        return replace(
            self,
            content=normalized,
            content_hash=content_digest(normalized),
            updated_at=stamp,
        )


@dataclass(frozen=True, slots=True)
class Tombstone:
    """The remains of a hard-deleted memory.

    Carries only identity and deletion metadata — no content, content hash, canonical
    key or other content-derived fields — so hard deletion leaves nothing recoverable
    (invariants 2 and 7). ``status`` is always ``DELETED``.
    """

    id: str
    owner_id: str
    deleted_at: datetime
    reason: str
    status: MemoryStatus = field(default=MemoryStatus.DELETED)

    def __post_init__(self) -> None:
        if not self.id.strip():
            raise ValidationError("id must not be empty")
        if not self.owner_id.strip():
            raise ValidationError("owner_id must not be empty")
        if self.status is not MemoryStatus.DELETED:
            raise ValidationError("a Tombstone must have DELETED status")
        ensure_utc(self.deleted_at, "deleted_at")


def _check_unit(name: str, value: float) -> None:
    if not 0.0 <= value <= 1.0:
        raise ValidationError(f"{name} must be within [0, 1], got {value}")


def make_memory(
    *,
    id: str,
    owner_id: str,
    kind: MemoryKind,
    content: str,
    provenance: Provenance,
    lifetime: MemoryLifetime = MemoryLifetime.LONG_TERM,
    sensitivity: Sensitivity = Sensitivity.PERSONAL,
    consent: ConsentCategory = ConsentCategory.PERSONALIZATION,
    retention: RetentionPolicy = RetentionPolicy.DURABLE_UNTIL_DELETION,
    importance: float = 0.5,
    confidence: float = 0.5,
    now: datetime | None = None,
    canonical_key: str | None = None,
    expires_at: datetime | None = None,
    tags: tuple[str, ...] = (),
    project: str | None = None,
    idempotency_key: str | None = None,
) -> MemoryRecord:
    """Create a new ACTIVE :class:`MemoryRecord` with derived content fields.

    Normalizes ``content``, computes its hash, derives a default canonical key when one
    is not supplied, and stamps ``created_at``/``updated_at``. A fixed ``now`` may be
    passed for deterministic tests.

    Raises:
        ValidationError: If any field is invalid (see :class:`MemoryRecord`).
    """
    stamp = ensure_utc(now, "now") if now is not None else utc_now()
    normalized = normalize_content(content)
    key = canonical_key if canonical_key is not None else derive_canonical_key(kind, normalized)
    return MemoryRecord(
        id=id,
        owner_id=owner_id,
        kind=kind,
        lifetime=lifetime,
        status=MemoryStatus.ACTIVE,
        content=normalized,
        content_hash=content_digest(normalized),
        canonical_key=key,
        provenance=provenance,
        sensitivity=sensitivity,
        consent=consent,
        retention=retention,
        importance=importance,
        confidence=confidence,
        created_at=stamp,
        updated_at=stamp,
        expires_at=expires_at,
        tags=tags,
        project=project,
        idempotency_key=idempotency_key,
    )
