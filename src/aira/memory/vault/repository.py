"""Owner-scoped, transactional memory repository (Aira Vault).

Every method requires an ``owner_id`` and scopes its SQL to that owner, so one owner can
never read or mutate another's memories (invariant 1). Each mutation writes the memory
state change and its audit event in a single transaction (invariant 11). Hard deletion
removes the row and records a content-free audit event (invariants 2 and 7). All SQL is
parameterized.
"""

from __future__ import annotations

import sqlite3
from collections.abc import Callable, Sequence
from datetime import datetime

from aira.memory.domain.enums import MemoryStatus
from aira.memory.domain.lifecycle import (
    SupersedeResult,
    TransitionResult,
    archive_memory,
    expire_memory,
    forget_memory,
    supersede_memory,
    update_memory,
)
from aira.memory.domain.lifecycle import (
    hard_delete as domain_hard_delete,
)
from aira.memory.domain.records import MemoryRecord, Tombstone
from aira.memory.trail.events import AuditAction, AuditEvent, new_event_id
from aira.memory.vault.errors import NotFoundError
from aira.memory.vault.mapper import (
    audit_to_row,
    memory_to_row,
    row_to_audit,
    row_to_memory,
)

_INACTIVE_EXPORTABLE = (
    MemoryStatus.ACTIVE,
    MemoryStatus.SUPERSEDED,
    MemoryStatus.ARCHIVED,
    MemoryStatus.EXPIRED,
    MemoryStatus.FORGOTTEN,
)


class MemoryRepository:
    """Persistence and audit for memories, scoped to an owner on every call."""

    def __init__(self, connection: sqlite3.Connection) -> None:
        """Wrap an open, migrated SQLite connection."""
        self._conn = connection

    # --- reads ---------------------------------------------------------------------

    def get(
        self, owner_id: str, memory_id: str, *, include_inactive: bool = False
    ) -> MemoryRecord | None:
        """Return a memory by id for this owner, or ``None``.

        By default only ACTIVE memories are returned (normal retrieval excludes
        forbidden states); ``include_inactive`` returns any non-deleted status.
        """
        row = self._fetch(owner_id, memory_id)
        if row is None:
            return None
        record = row_to_memory(row)
        if not include_inactive and record.status is not MemoryStatus.ACTIVE:
            return None
        return record

    def list_memories(
        self,
        owner_id: str,
        *,
        statuses: Sequence[MemoryStatus] | None = None,
        kind: str | None = None,
        project: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[MemoryRecord]:
        """List this owner's memories, defaulting to ACTIVE only, newest-stable ordered."""
        wanted = tuple(statuses) if statuses is not None else (MemoryStatus.ACTIVE,)
        placeholders = ",".join("?" for _ in wanted)
        sql = f"SELECT * FROM memories WHERE owner_id = ? AND status IN ({placeholders})"
        params: list[object] = [owner_id, *[s.value for s in wanted]]
        if kind is not None:
            sql += " AND kind = ?"
            params.append(kind)
        if project is not None:
            sql += " AND project = ?"
            params.append(project)
        sql += " ORDER BY created_at ASC, id ASC LIMIT ? OFFSET ?"
        params += [limit, offset]
        rows = self._conn.execute(sql, params).fetchall()
        return [row_to_memory(r) for r in rows]

    def audit_events_for(self, owner_id: str, memory_id: str) -> list[AuditEvent]:
        """Return the append-only audit trail for one memory, scoped to its owner."""
        rows = self._conn.execute(
            "SELECT * FROM audit_events WHERE owner_id = ? AND memory_id = ? "
            "ORDER BY at ASC, rowid ASC",  # rowid tiebreak = insertion (chronological) order
            (owner_id, memory_id),
        ).fetchall()
        return [row_to_audit(r) for r in rows]

    def export(self, owner_id: str, *, include_inactive: bool = False) -> list[MemoryRecord]:
        """Export this owner's memories. Excludes forbidden states unless asked otherwise."""
        statuses = _INACTIVE_EXPORTABLE if include_inactive else (MemoryStatus.ACTIVE,)
        return self.list_memories(owner_id, statuses=statuses, limit=1_000_000)

    # --- writes --------------------------------------------------------------------

    def create(self, record: MemoryRecord, *, reason: str = "created") -> MemoryRecord:
        """Persist a new memory and its CREATE audit event in one transaction.

        Idempotent on ``idempotency_key``: if a memory with the same key already exists
        for the owner, the existing record is returned and nothing is written.
        """
        if record.idempotency_key is not None:
            existing = self._conn.execute(
                "SELECT * FROM memories WHERE owner_id = ? AND idempotency_key = ?",
                (record.owner_id, record.idempotency_key),
            ).fetchone()
            if existing is not None:
                return row_to_memory(existing)

        event = AuditEvent(
            id=new_event_id(),
            memory_id=record.id,
            owner_id=record.owner_id,
            action=AuditAction.CREATE,
            at=record.created_at,
            reason=reason,
            from_status=None,
            to_status=record.status,
        )
        with self._conn:
            self._insert(record)
            self._insert_audit(event)
        return record

    def update(
        self,
        owner_id: str,
        memory_id: str,
        *,
        content: str | None = None,
        importance: float | None = None,
        confidence: float | None = None,
        now: datetime | None = None,
        reason: str | None = None,
    ) -> MemoryRecord:
        """Update an ACTIVE memory in place, writing an UPDATE audit event."""
        current = self._load_for_transition(owner_id, memory_id)
        result = update_memory(
            current,
            content=content,
            importance=importance,
            confidence=confidence,
            now=now,
            reason=reason,
        )
        return self._persist_update(owner_id, memory_id, current.status, AuditAction.UPDATE, result)

    def archive(
        self,
        owner_id: str,
        memory_id: str,
        *,
        now: datetime | None = None,
        reason: str | None = None,
    ) -> MemoryRecord:
        """Archive a memory, writing an ARCHIVE audit event."""
        return self._simple_transition(
            owner_id, memory_id, archive_memory, AuditAction.ARCHIVE, now, reason
        )

    def expire(
        self,
        owner_id: str,
        memory_id: str,
        *,
        now: datetime | None = None,
        reason: str | None = None,
    ) -> MemoryRecord:
        """Expire a memory, writing an EXPIRE audit event."""
        return self._simple_transition(
            owner_id, memory_id, expire_memory, AuditAction.EXPIRE, now, reason
        )

    def forget(
        self,
        owner_id: str,
        memory_id: str,
        *,
        now: datetime | None = None,
        reason: str | None = None,
    ) -> MemoryRecord:
        """Forget a memory at the user's request, writing a FORGET audit event."""
        return self._simple_transition(
            owner_id, memory_id, forget_memory, AuditAction.FORGET, now, reason
        )

    def supersede(
        self,
        owner_id: str,
        old_id: str,
        replacement: MemoryRecord,
        *,
        now: datetime | None = None,
        reason: str | None = None,
    ) -> SupersedeResult:
        """Supersede an ACTIVE memory with a replacement, writing linked audit events."""
        old = self._load_for_transition(owner_id, old_id)
        result = supersede_memory(old, replacement, now=now, reason=reason)
        ev_old = AuditEvent(
            id=new_event_id(),
            memory_id=old.id,
            owner_id=owner_id,
            action=AuditAction.SUPERSEDE,
            at=result.at,
            reason=result.reason,
            from_status=old.status,
            to_status=MemoryStatus.SUPERSEDED,
            detail={"superseded_by": replacement.id},
        )
        ev_new = AuditEvent(
            id=new_event_id(),
            memory_id=replacement.id,
            owner_id=owner_id,
            action=AuditAction.CREATE,
            at=result.at,
            reason=f"supersedes {old.id}",
            from_status=None,
            to_status=MemoryStatus.ACTIVE,
            detail={"supersedes": old.id},
        )
        with self._conn:
            self._update_row(result.superseded)
            self._insert(result.replacement)
            self._insert_audit(ev_old)
            self._insert_audit(ev_new)
        return result

    def hard_delete(
        self,
        owner_id: str,
        memory_id: str,
        *,
        now: datetime | None = None,
        reason: str | None = None,
    ) -> Tombstone:
        """Hard-delete a memory: remove its row and write a content-free audit event."""
        current = self._load_for_transition(owner_id, memory_id)
        result = domain_hard_delete(current, now=now, reason=reason)
        tombstone = result.state
        assert isinstance(tombstone, Tombstone)  # noqa: S101 - narrow the union
        event = AuditEvent(
            id=new_event_id(),
            memory_id=memory_id,
            owner_id=owner_id,
            action=AuditAction.HARD_DELETE,
            at=result.at,
            reason=result.reason,
            from_status=current.status,
            to_status=MemoryStatus.DELETED,
            detail={},
        )
        with self._conn:
            self._delete_row(owner_id, memory_id)
            self._insert_audit(event)
        return tombstone

    def import_records(
        self, owner_id: str, records: Sequence[MemoryRecord], *, reason: str = "imported"
    ) -> int:
        """Insert many records and their IMPORT audit events atomically.

        All records must already belong to ``owner_id``. If any insertion fails the whole
        import rolls back (invariant 11). Returns the number of records written.
        """
        for record in records:
            if record.owner_id != owner_id:
                raise ValueError("all imported records must belong to the importing owner")
        with self._conn:
            for record in records:
                self._insert(record)
                self._insert_audit(
                    AuditEvent(
                        id=new_event_id(),
                        memory_id=record.id,
                        owner_id=owner_id,
                        action=AuditAction.IMPORT,
                        at=record.updated_at,
                        reason=reason,
                        from_status=None,
                        to_status=record.status,
                    )
                )
        return len(records)

    # --- internals -----------------------------------------------------------------

    def _fetch(self, owner_id: str, memory_id: str) -> sqlite3.Row | None:
        row: sqlite3.Row | None = self._conn.execute(
            "SELECT * FROM memories WHERE owner_id = ? AND id = ?",
            (owner_id, memory_id),
        ).fetchone()
        return row

    def _load_for_transition(self, owner_id: str, memory_id: str) -> MemoryRecord:
        row = self._fetch(owner_id, memory_id)
        if row is None:
            raise NotFoundError(f"memory not found for this owner: {memory_id}")
        return row_to_memory(row)

    def _simple_transition(
        self,
        owner_id: str,
        memory_id: str,
        fn: Callable[..., TransitionResult],
        action: AuditAction,
        now: datetime | None,
        reason: str | None,
    ) -> MemoryRecord:
        current = self._load_for_transition(owner_id, memory_id)
        result = fn(current, now=now, reason=reason)
        return self._persist_update(owner_id, memory_id, current.status, action, result)

    def _persist_update(
        self,
        owner_id: str,
        memory_id: str,
        from_status: MemoryStatus,
        action: AuditAction,
        result: TransitionResult,
    ) -> MemoryRecord:
        state = result.state
        assert isinstance(state, MemoryRecord)  # noqa: S101 - transitions here return records
        event = AuditEvent(
            id=new_event_id(),
            memory_id=memory_id,
            owner_id=owner_id,
            action=action,
            at=result.at,
            reason=result.reason,
            from_status=from_status,
            to_status=state.status,
        )
        with self._conn:
            self._update_row(state)
            self._insert_audit(event)
        return state

    def _insert(self, record: MemoryRecord) -> None:
        row = memory_to_row(record)
        columns = ", ".join(row)
        placeholders = ", ".join(f":{c}" for c in row)
        self._conn.execute(
            f"INSERT INTO memories ({columns}) VALUES ({placeholders})",  # noqa: S608 - fixed columns
            row,
        )

    def _update_row(self, record: MemoryRecord) -> None:
        row = memory_to_row(record)
        assignments = ", ".join(f"{c} = :{c}" for c in row if c not in ("id", "owner_id"))
        self._conn.execute(
            f"UPDATE memories SET {assignments} WHERE id = :id AND owner_id = :owner_id",  # noqa: S608
            row,
        )

    def _delete_row(self, owner_id: str, memory_id: str) -> None:
        self._conn.execute(
            "DELETE FROM memories WHERE owner_id = ? AND id = ?",
            (owner_id, memory_id),
        )

    def _insert_audit(self, event: AuditEvent) -> None:
        row = audit_to_row(event)
        columns = ", ".join(row)
        placeholders = ", ".join(f":{c}" for c in row)
        self._conn.execute(
            f"INSERT INTO audit_events ({columns}) VALUES ({placeholders})",  # noqa: S608 - fixed columns
            row,
        )
