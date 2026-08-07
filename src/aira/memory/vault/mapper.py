"""Mapping between domain objects and SQLite rows / export dicts.

Reconstructing a :class:`MemoryRecord` from a row runs its full validation (including
content-hash integrity), so corrupt or tampered rows are rejected on read.
"""

from __future__ import annotations

import json
import sqlite3
from collections.abc import Mapping
from datetime import datetime
from typing import Any

from aira.memory.domain.enums import (
    ConsentCategory,
    MemoryKind,
    MemoryLifetime,
    MemoryStatus,
    ProvenanceSource,
    RetentionPolicy,
    Sensitivity,
)
from aira.memory.domain.records import MemoryRecord, Provenance
from aira.memory.trail.events import AuditAction, AuditEvent

EXPORT_SCHEMA_VERSION = 1


def _dt(value: str | None) -> datetime | None:
    return datetime.fromisoformat(value) if value else None


def memory_to_row(record: MemoryRecord) -> dict[str, Any]:
    """Flatten a memory record into a column mapping for insertion/update."""
    p = record.provenance
    return {
        "id": record.id,
        "owner_id": record.owner_id,
        "kind": record.kind.value,
        "lifetime": record.lifetime.value,
        "status": record.status.value,
        "content": record.content,
        "content_hash": record.content_hash,
        "canonical_key": record.canonical_key,
        "prov_source": p.source.value,
        "prov_actor": p.actor,
        "prov_method": p.method,
        "prov_captured_at": p.captured_at.isoformat(),
        "prov_source_excerpt": p.source_excerpt,
        "sensitivity": record.sensitivity.value,
        "consent": record.consent.value,
        "retention": record.retention.value,
        "importance": record.importance,
        "confidence": record.confidence,
        "created_at": record.created_at.isoformat(),
        "updated_at": record.updated_at.isoformat(),
        "expires_at": record.expires_at.isoformat() if record.expires_at else None,
        "supersedes": record.supersedes,
        "superseded_by": record.superseded_by,
        "reinforcement_count": record.reinforcement_count,
        "tags": json.dumps(list(record.tags)),
        "project": record.project,
        "idempotency_key": record.idempotency_key,
    }


def row_to_memory(row: sqlite3.Row) -> MemoryRecord:
    """Rebuild a validated memory record from a database row."""
    provenance = Provenance(
        source=ProvenanceSource(row["prov_source"]),
        actor=row["prov_actor"],
        method=row["prov_method"],
        captured_at=datetime.fromisoformat(row["prov_captured_at"]),
        source_excerpt=row["prov_source_excerpt"],
    )
    return MemoryRecord(
        id=row["id"],
        owner_id=row["owner_id"],
        kind=MemoryKind(row["kind"]),
        lifetime=MemoryLifetime(row["lifetime"]),
        status=MemoryStatus(row["status"]),
        content=row["content"],
        content_hash=row["content_hash"],
        canonical_key=row["canonical_key"],
        provenance=provenance,
        sensitivity=Sensitivity(row["sensitivity"]),
        consent=ConsentCategory(row["consent"]),
        retention=RetentionPolicy(row["retention"]),
        importance=row["importance"],
        confidence=row["confidence"],
        created_at=datetime.fromisoformat(row["created_at"]),
        updated_at=datetime.fromisoformat(row["updated_at"]),
        expires_at=_dt(row["expires_at"]),
        supersedes=row["supersedes"],
        superseded_by=row["superseded_by"],
        reinforcement_count=row["reinforcement_count"],
        tags=tuple(json.loads(row["tags"])),
        project=row["project"],
        idempotency_key=row["idempotency_key"],
    )


def audit_to_row(event: AuditEvent) -> dict[str, Any]:
    """Flatten an audit event into a column mapping for insertion."""
    return {
        "id": event.id,
        "memory_id": event.memory_id,
        "owner_id": event.owner_id,
        "action": event.action.value,
        "at": event.at.isoformat(),
        "reason": event.reason,
        "from_status": event.from_status.value if event.from_status else None,
        "to_status": event.to_status.value if event.to_status else None,
        "detail": json.dumps(event.detail),
    }


def row_to_audit(row: sqlite3.Row) -> AuditEvent:
    """Rebuild an audit event from a database row."""
    return AuditEvent(
        id=row["id"],
        memory_id=row["memory_id"],
        owner_id=row["owner_id"],
        action=AuditAction(row["action"]),
        at=datetime.fromisoformat(row["at"]),
        reason=row["reason"],
        from_status=MemoryStatus(row["from_status"]) if row["from_status"] else None,
        to_status=MemoryStatus(row["to_status"]) if row["to_status"] else None,
        detail=json.loads(row["detail"]),
    )


def memory_to_export(record: MemoryRecord) -> dict[str, Any]:
    """Serialize a memory record for JSONL export, tagged with the export schema version."""
    row = memory_to_row(record)
    row["schema_version"] = EXPORT_SCHEMA_VERSION
    return row


def dict_to_memory(data: Mapping[str, Any], *, owner_id: str) -> MemoryRecord:
    """Build a validated memory record from an export/import mapping, rebinding the owner.

    The owner is always set to ``owner_id`` (import binds records to the importing owner,
    never the source owner). Raises ``KeyError``/``ValueError`` on malformed input; the
    caller wraps these as an import rejection.
    """
    provenance = Provenance(
        source=ProvenanceSource(data["prov_source"]),
        actor=data["prov_actor"],
        method=data["prov_method"],
        captured_at=datetime.fromisoformat(data["prov_captured_at"]),
        source_excerpt=data.get("prov_source_excerpt"),
    )
    tags = data.get("tags", "[]")
    tag_tuple = tuple(json.loads(tags)) if isinstance(tags, str) else tuple(tags)
    return MemoryRecord(
        id=data["id"],
        owner_id=owner_id,
        kind=MemoryKind(data["kind"]),
        lifetime=MemoryLifetime(data["lifetime"]),
        status=MemoryStatus(data["status"]),
        content=data["content"],
        content_hash=data["content_hash"],
        canonical_key=data["canonical_key"],
        provenance=provenance,
        sensitivity=Sensitivity(data["sensitivity"]),
        consent=ConsentCategory(data["consent"]),
        retention=RetentionPolicy(data["retention"]),
        importance=float(data["importance"]),
        confidence=float(data["confidence"]),
        created_at=datetime.fromisoformat(data["created_at"]),
        updated_at=datetime.fromisoformat(data["updated_at"]),
        expires_at=_dt(data.get("expires_at")),
        supersedes=data.get("supersedes"),
        superseded_by=data.get("superseded_by"),
        reinforcement_count=int(data.get("reinforcement_count", 0)),
        tags=tag_tuple,
        project=data.get("project"),
        idempotency_key=data.get("idempotency_key"),
    )
