"""Tests for Aira Vault and Trail: persistence, owner isolation, transactions, audit."""

from __future__ import annotations

import json
import sqlite3
from collections.abc import Callable
from datetime import datetime, timedelta
from pathlib import Path

import pytest

from aira.memory.domain import MemoryRecord, MemoryStatus, normalize_content
from aira.memory.guard import default_guard
from aira.memory.trail import AuditAction
from aira.memory.vault import (
    SCHEMA_VERSION,
    ImportRejectedError,
    MemoryRepository,
    NotFoundError,
    apply_migrations,
    backup_database,
    connect,
    export_jsonl,
    import_jsonl,
    integrity_check,
)

Factory = Callable[..., MemoryRecord]


@pytest.fixture
def repo() -> MemoryRepository:
    return MemoryRepository(connect(":memory:"))


# --- create / get / persistence ----------------------------------------------------


def test_create_and_get(repo: MemoryRepository, make_record: Factory) -> None:
    rec = make_record(id="m1")
    repo.create(rec)
    got = repo.get("owner-a", "m1")
    assert got is not None
    assert got.content == rec.content
    assert got.content_hash == rec.content_hash


def test_persistence_across_restart(tmp_path: Path, make_record: Factory) -> None:
    db = tmp_path / "aira.db"
    conn = connect(db)
    MemoryRepository(conn).create(make_record(id="m1"))
    conn.close()

    reopened = MemoryRepository(connect(db))
    assert reopened.get("owner-a", "m1") is not None


# --- owner isolation (invariant 1) -------------------------------------------------


def test_owner_cannot_read_or_mutate_other(repo: MemoryRepository, make_record: Factory) -> None:
    repo.create(make_record(id="m1", owner_id="owner-a"))

    assert repo.get("owner-b", "m1") is None
    assert repo.list_memories("owner-b") == []
    assert repo.export("owner-b") == []
    for op in (repo.update, repo.archive, repo.expire, repo.forget, repo.hard_delete):
        with pytest.raises(NotFoundError):
            op("owner-b", "m1")


# --- transactional rollback (invariant 11) -----------------------------------------


def test_rollback_when_audit_write_fails(
    repo: MemoryRepository, make_record: Factory, monkeypatch: pytest.MonkeyPatch
) -> None:
    def boom(_event: object) -> None:
        raise RuntimeError("injected audit failure")

    monkeypatch.setattr(repo, "_insert_audit", boom)
    with pytest.raises(RuntimeError, match="injected"):
        repo.create(make_record(id="m1"))
    # neither the memory nor an audit row survived
    assert repo.get("owner-a", "m1", include_inactive=True) is None


# --- idempotency -------------------------------------------------------------------


def test_duplicate_idempotency_key_is_deduped(repo: MemoryRepository, make_record: Factory) -> None:
    a = repo.create(make_record(id="m1", idempotency_key="k1"))
    b = repo.create(make_record(id="m2", idempotency_key="k1"))
    assert a.id == b.id == "m1"
    assert len(repo.list_memories("owner-a")) == 1
    assert len(repo.audit_events_for("owner-a", "m1")) == 1


# --- lifecycle filters (invariant 2) -----------------------------------------------


def test_forgotten_excluded_by_default(
    repo: MemoryRepository, make_record: Factory, fixed_now: datetime
) -> None:
    repo.create(make_record(id="m1"))
    repo.forget("owner-a", "m1", now=fixed_now + timedelta(hours=1))
    assert repo.get("owner-a", "m1") is None
    assert repo.list_memories("owner-a") == []
    inactive = repo.get("owner-a", "m1", include_inactive=True)
    assert inactive is not None
    assert inactive.status is MemoryStatus.FORGOTTEN


def test_superseded_and_expired_excluded(
    repo: MemoryRepository, make_record: Factory, fixed_now: datetime
) -> None:
    repo.create(make_record(id="old", content="owner-a prefers dark mode"))
    replacement = make_record(id="new", content="owner-a prefers light mode")
    repo.supersede("owner-a", "old", replacement, now=fixed_now + timedelta(hours=1))
    active_ids = {m.id for m in repo.list_memories("owner-a")}
    assert active_ids == {"new"}

    repo.create(make_record(id="m2"))
    repo.expire("owner-a", "m2", now=fixed_now + timedelta(hours=1))
    assert all(m.id != "m2" for m in repo.list_memories("owner-a"))


# --- hard delete removes content (invariants 2, 7) ---------------------------------


def test_hard_delete_removes_content_and_audit_has_none(
    repo: MemoryRepository, make_record: Factory, fixed_now: datetime
) -> None:
    secret_ish = "owner-a lives at 42 Rivendell Lane"
    repo.create(make_record(id="m1", content=secret_ish))
    tomb = repo.hard_delete("owner-a", "m1", now=fixed_now + timedelta(hours=1))
    assert tomb.id == "m1"

    assert repo.get("owner-a", "m1", include_inactive=True) is None
    # audit event exists but carries no content
    events = repo.audit_events_for("owner-a", "m1")
    assert any(e.action is AuditAction.HARD_DELETE for e in events)
    dumped = json.dumps([e.detail for e in events])
    assert normalize_content(secret_ish) not in dumped
    assert secret_ish not in dumped


# --- audit for every mutation ------------------------------------------------------


def test_audit_event_per_mutation(
    repo: MemoryRepository, make_record: Factory, fixed_now: datetime
) -> None:
    later = fixed_now + timedelta(hours=1)
    repo.create(make_record(id="m1"))
    repo.update("owner-a", "m1", importance=0.9, now=later)
    repo.archive("owner-a", "m1", now=later)
    actions = [e.action for e in repo.audit_events_for("owner-a", "m1")]
    assert actions == [AuditAction.CREATE, AuditAction.UPDATE, AuditAction.ARCHIVE]


# --- SQL injection resistance ------------------------------------------------------


def test_parameterized_sql_resists_injection(repo: MemoryRepository, make_record: Factory) -> None:
    evil = "Robert'); DROP TABLE memories;-- and dark mode"
    repo.create(make_record(id="m-evil", content=evil, owner_id="o'wner"))
    got = repo.get("o'wner", "m-evil")
    assert got is not None
    assert got.content == normalize_content(evil)
    # table survived; a normal query still works
    assert len(repo.list_memories("o'wner")) == 1


# --- migrations --------------------------------------------------------------------


def test_migrations_idempotent_and_versioned() -> None:
    conn = sqlite3.connect(":memory:")
    assert apply_migrations(conn) == SCHEMA_VERSION
    assert apply_migrations(conn) == SCHEMA_VERSION  # idempotent
    tables = {r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    assert {"memories", "audit_events", "schema_version"} <= tables


def test_integrity_and_backup(tmp_path: Path, make_record: Factory) -> None:
    conn = connect(tmp_path / "a.db")
    repo = MemoryRepository(conn)
    repo.create(make_record(id="m1"))
    assert integrity_check(conn) is True
    dest = backup_database(conn, tmp_path / "backup.db")
    restored = MemoryRepository(connect(dest))
    assert restored.get("owner-a", "m1") is not None


# --- export / import ---------------------------------------------------------------


def test_export_import_roundtrip_rebinds_owner(
    repo: MemoryRepository, make_record: Factory
) -> None:
    repo.create(make_record(id="m1", owner_id="owner-a", content="owner-a prefers dark mode"))
    payload = export_jsonl(repo, "owner-a")
    assert payload  # non-empty

    # Memory ids are globally unique; import into a separate store (as a real import would).
    other = MemoryRepository(connect(":memory:"))
    count = import_jsonl(other, "owner-b", payload, guard=default_guard())
    assert count == 1
    imported = other.list_memories("owner-b")
    assert len(imported) == 1
    assert imported[0].owner_id == "owner-b"  # rebound to importer


def test_import_blocks_secret_content(repo: MemoryRepository) -> None:
    line = json.dumps(
        {
            "schema_version": 1,
            "id": "x",
            "kind": "semantic",
            "lifetime": "long_term",
            "status": "active",
            "content": "my key is AKIAIOSFODNN7EXAMPLE",
            "content_hash": "irrelevant",
            "canonical_key": "semantic:x",
            "prov_source": "user_explicit",
            "prov_actor": "owner-a",
            "prov_method": "explicit",
            "prov_captured_at": "2026-01-01T00:00:00+00:00",
            "sensitivity": "personal",
            "consent": "personalization",
            "retention": "durable_until_deletion",
            "importance": 0.5,
            "confidence": 0.5,
            "created_at": "2026-01-01T00:00:00+00:00",
            "updated_at": "2026-01-01T00:00:00+00:00",
        }
    )
    with pytest.raises(ImportRejectedError, match="guard"):
        import_jsonl(repo, "owner-b", line, guard=default_guard())
    assert repo.list_memories("owner-b") == []


def test_malformed_import_writes_nothing(repo: MemoryRepository, make_record: Factory) -> None:
    good = export_jsonl(
        MemoryRepository(connect(":memory:")),
        "owner-a",
    )  # empty export
    bad = good + '\n{"schema_version": 1, "content": "hi"}'  # missing required fields
    with pytest.raises(ImportRejectedError):
        import_jsonl(repo, "owner-b", bad, guard=default_guard())
    assert repo.list_memories("owner-b") == []


def test_import_rejects_unknown_schema_version(repo: MemoryRepository) -> None:
    line = json.dumps({"schema_version": 999, "content": "hi"})
    with pytest.raises(ImportRejectedError, match="schema_version"):
        import_jsonl(repo, "owner-b", line, guard=default_guard())
