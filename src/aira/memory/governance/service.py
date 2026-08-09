"""User-control operations over memory (Aira governance).

Everything here is owner-scoped and audited by the repository. User control overrides
automated retention (invariant 9); nothing here hard-deletes implicitly — ``delete_all``
is explicit. Corrections and imports are screened through Aira Guard before anything is
written.
"""

from __future__ import annotations

import uuid
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime

from aira.memory.domain.clock import utc_now
from aira.memory.domain.enums import (
    ConsentCategory,
    MemoryStatus,
    ProvenanceSource,
    RetentionPolicy,
)
from aira.memory.domain.records import MemoryRecord, Provenance, make_memory
from aira.memory.guard.interface import Guard
from aira.memory.trail.events import AuditEvent
from aira.memory.vault.backup import export_jsonl, import_jsonl
from aira.memory.vault.errors import NotFoundError
from aira.memory.vault.repository import MemoryRepository

_NON_DELETED = (
    MemoryStatus.ACTIVE,
    MemoryStatus.SUPERSEDED,
    MemoryStatus.ARCHIVED,
    MemoryStatus.EXPIRED,
    MemoryStatus.FORGOTTEN,
)


class GovernanceError(Exception):
    """A governance operation was rejected (e.g. guard-blocked correction)."""


@dataclass(frozen=True, slots=True)
class Explanation:
    """Why a memory exists: its record (if present) and its audit trail."""

    memory: MemoryRecord | None
    events: tuple[AuditEvent, ...]


def _default_id() -> str:
    return uuid.uuid4().hex


class GovernanceService:
    """User-facing memory controls: inspect, explain, correct, forget, delete, export/import."""

    def __init__(
        self,
        repository: MemoryRepository,
        guard: Guard,
        *,
        new_id: Callable[[], str] = _default_id,
    ) -> None:
        """Create the service over a repository and a guard."""
        self._repo = repository
        self._guard = guard
        self._new_id = new_id

    def inspect_all(self, owner_id: str, *, include_inactive: bool = False) -> list[MemoryRecord]:
        """List an owner's memories (active by default; all non-deleted if requested)."""
        statuses = _NON_DELETED if include_inactive else (MemoryStatus.ACTIVE,)
        return self._repo.list_memories(owner_id, statuses=statuses, limit=1_000_000)

    def explain(self, owner_id: str, memory_id: str) -> Explanation:
        """Return a memory's current record and its full audit trail."""
        record = self._repo.get(owner_id, memory_id, include_inactive=True)
        events = self._repo.audit_events_for(owner_id, memory_id)
        return Explanation(memory=record, events=tuple(events))

    def correct(
        self,
        owner_id: str,
        memory_id: str,
        new_content: str,
        *,
        now: datetime | None = None,
    ) -> MemoryRecord:
        """Correct an active memory by superseding it with guard-screened new content."""
        stamp = now if now is not None else utc_now()
        current = self._repo.get(owner_id, memory_id)
        if current is None:
            raise NotFoundError(f"no active memory to correct: {memory_id}")
        scan = self._guard.scan(new_content, owner_id=owner_id, now=stamp)
        if scan.blocked:
            raise GovernanceError(f"correction blocked by guard: {scan.reason}")

        replacement = make_memory(
            id=self._new_id(),
            owner_id=owner_id,
            kind=current.kind,
            content=new_content,
            provenance=Provenance(
                source=ProvenanceSource.USER_CORRECTION,
                actor=owner_id,
                method="explicit user correction",
                captured_at=stamp,
            ),
            importance=current.importance,
            confidence=max(current.confidence, 0.85),
            lifetime=current.lifetime,
            sensitivity=current.sensitivity,
            consent=current.consent,
            retention=current.retention,
            canonical_key=current.canonical_key,
            project=current.project,
            now=stamp,
        )
        result = self._repo.supersede(
            owner_id, memory_id, replacement, now=stamp, reason="user correction"
        )
        return result.replacement

    def reinforce(
        self, owner_id: str, memory_id: str, *, now: datetime | None = None
    ) -> MemoryRecord:
        """Reinforce a memory on explicit usefulness evidence (never automatic)."""
        return self._repo.reinforce(owner_id, memory_id, now=now)

    def archive(
        self, owner_id: str, memory_id: str, *, now: datetime | None = None
    ) -> MemoryRecord:
        """Archive a memory at the user's request."""
        return self._repo.archive(owner_id, memory_id, now=now, reason="archived by user")

    def forget(self, owner_id: str, memory_id: str, *, now: datetime | None = None) -> MemoryRecord:
        """Forget a memory at the user's request."""
        return self._repo.forget(owner_id, memory_id, now=now, reason="forgotten by user")

    def hard_delete(self, owner_id: str, memory_id: str, *, now: datetime | None = None) -> None:
        """Hard-delete a single memory at the user's request."""
        self._repo.hard_delete(owner_id, memory_id, now=now, reason="hard-deleted by user")

    def set_retention(
        self,
        owner_id: str,
        memory_id: str,
        retention: RetentionPolicy,
        *,
        consent: ConsentCategory | None = None,
        expires_at: datetime | None = None,
        now: datetime | None = None,
    ) -> MemoryRecord:
        """Set a memory's retention/consent — user control over automated recommendations."""
        return self._repo.set_policy(
            owner_id,
            memory_id,
            retention=retention,
            consent=consent,
            expires_at=expires_at,
            now=now,
            reason="retention set by user",
        )

    def export(self, owner_id: str, *, include_inactive: bool = False) -> str:
        """Export an owner's memories to JSONL (forbidden states excluded by default)."""
        return export_jsonl(self._repo, owner_id, include_inactive=include_inactive)

    def import_(self, owner_id: str, text: str) -> int:
        """Validate, guard-screen and atomically import JSONL into an owner's space.

        Raises:
            ImportRejectedError: On malformed, oversized, unknown-schema or blocked content.
                Nothing is written on rejection.
        """
        return import_jsonl(self._repo, owner_id, text, guard=self._guard)

    def delete_all(self, owner_id: str, *, now: datetime | None = None) -> int:
        """Hard-delete all of one owner's memories. Owner-scoped; returns the count."""
        stamp = now if now is not None else utc_now()
        records = self._repo.list_memories(owner_id, statuses=_NON_DELETED, limit=1_000_000)
        for record in records:
            self._repo.hard_delete(owner_id, record.id, now=stamp, reason="user delete-all")
        return len(records)
