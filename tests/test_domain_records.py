"""Validation tests for domain records (MemoryRecord, Provenance, Tombstone)."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import replace
from datetime import UTC, datetime, timedelta

import pytest

from aira.memory.domain import (
    MemoryKind,
    MemoryRecord,
    MemoryStatus,
    Provenance,
    ProvenanceSource,
    RetentionPolicy,
    Tombstone,
    ValidationError,
    content_digest,
    make_memory,
)

Factory = Callable[..., MemoryRecord]


def test_make_memory_defaults_to_active(make_record: Factory) -> None:
    rec = make_record()
    assert rec.status is MemoryStatus.ACTIVE
    assert rec.created_at == rec.updated_at


def test_content_is_normalized_and_hashed(make_record: Factory) -> None:
    rec = make_record(content="  alex   prefers  dark mode ")
    assert rec.content == "alex prefers dark mode"
    assert rec.content_hash == content_digest(rec.content)


def test_default_canonical_key(make_record: Factory) -> None:
    rec = make_record(content="Dark Mode", kind=MemoryKind.PREFERENCE)
    assert rec.canonical_key == "preference:dark mode"


def test_empty_owner_rejected(provenance: Provenance) -> None:
    with pytest.raises(ValidationError, match="owner_id"):
        make_memory(
            id="m", owner_id="  ", content="x", kind=MemoryKind.SEMANTIC, provenance=provenance
        )


def test_empty_content_rejected(provenance: Provenance) -> None:
    with pytest.raises(ValidationError, match="content"):
        make_memory(
            id="m", owner_id="o", content="   ", kind=MemoryKind.SEMANTIC, provenance=provenance
        )


@pytest.mark.parametrize("bad", [-0.01, 1.01, 2.0])
def test_importance_out_of_range(make_record: Factory, bad: float) -> None:
    with pytest.raises(ValidationError, match="importance"):
        make_record(importance=bad)


@pytest.mark.parametrize("bad", [-0.01, 1.5])
def test_confidence_out_of_range(make_record: Factory, bad: float) -> None:
    with pytest.raises(ValidationError, match="confidence"):
        make_record(confidence=bad)


def test_naive_timestamp_rejected(provenance: Provenance) -> None:
    naive = datetime(2026, 1, 1, 12, 0, 0)  # noqa: DTZ001 - intentionally naive for the test
    with pytest.raises(ValidationError, match="timezone-aware"):
        make_memory(
            id="m",
            owner_id="o",
            content="x",
            kind=MemoryKind.SEMANTIC,
            provenance=provenance,
            now=naive,
        )


def test_provenance_required_fields() -> None:
    with pytest.raises(ValidationError, match="actor"):
        Provenance(
            source=ProvenanceSource.USER_EXPLICIT,
            actor="",
            method="m",
            captured_at=datetime(2026, 1, 1, tzinfo=UTC),
        )


def test_prohibited_retention_rejected(provenance: Provenance) -> None:
    with pytest.raises(ValidationError, match="PROHIBITED"):
        make_memory(
            id="m",
            owner_id="o",
            content="x",
            kind=MemoryKind.SEMANTIC,
            provenance=provenance,
            retention=RetentionPolicy.PROHIBITED,
        )


def test_fixed_expiry_requires_expires_at(provenance: Provenance) -> None:
    with pytest.raises(ValidationError, match="expires_at"):
        make_memory(
            id="m",
            owner_id="o",
            content="x",
            kind=MemoryKind.SEMANTIC,
            provenance=provenance,
            retention=RetentionPolicy.FIXED_EXPIRY,
        )


def test_record_cannot_hold_deleted_status(make_record: Factory) -> None:
    rec = make_record()
    with pytest.raises(ValidationError, match="DELETED"):
        replace(rec, status=MemoryStatus.DELETED)


def test_updated_before_created_rejected(make_record: Factory, fixed_now: datetime) -> None:
    rec = make_record()
    with pytest.raises(ValidationError, match="updated_at"):
        replace(rec, updated_at=fixed_now - timedelta(days=1))


def test_tampered_hash_rejected(make_record: Factory) -> None:
    rec = make_record()
    with pytest.raises(ValidationError, match="content_hash"):
        replace(rec, content_hash="deadbeef")


def test_active_cannot_have_superseded_by(make_record: Factory) -> None:
    rec = make_record()
    with pytest.raises(ValidationError, match="ACTIVE"):
        replace(rec, superseded_by="other")


def test_with_content_refreshes_hash_and_timestamp(
    make_record: Factory, fixed_now: datetime
) -> None:
    rec = make_record()
    later = fixed_now + timedelta(hours=1)
    updated = rec.with_content("owner-a prefers light mode", now=later)
    assert updated.content == "owner-a prefers light mode"
    assert updated.content_hash == content_digest(updated.content)
    assert updated.updated_at == later
    assert updated.canonical_key == rec.canonical_key  # identity stable across edits


def test_tombstone_has_no_content_field(make_record: Factory, fixed_now: datetime) -> None:
    tomb = Tombstone(id="m", owner_id="o", deleted_at=fixed_now, reason="user asked")
    assert tomb.status is MemoryStatus.DELETED
    # By type, a tombstone carries no content or content-derived metadata.
    for forbidden in ("content", "content_hash", "canonical_key"):
        assert not hasattr(tomb, forbidden)
