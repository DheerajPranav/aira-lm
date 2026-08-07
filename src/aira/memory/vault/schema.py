"""SQLite schema and forward-only migrations for Aira Vault.

Migrations are a versioned, ordered list. :func:`apply_migrations` brings a database up
to the latest version and is idempotent, so it is safe to call on every startup.
"""

from __future__ import annotations

import sqlite3

SCHEMA_VERSION = 1

_MIGRATION_1 = """
CREATE TABLE memories (
    id                  TEXT PRIMARY KEY,
    owner_id            TEXT NOT NULL,
    kind                TEXT NOT NULL,
    lifetime            TEXT NOT NULL,
    status              TEXT NOT NULL,
    content             TEXT NOT NULL,
    content_hash        TEXT NOT NULL,
    canonical_key       TEXT NOT NULL,
    prov_source         TEXT NOT NULL,
    prov_actor          TEXT NOT NULL,
    prov_method         TEXT NOT NULL,
    prov_captured_at    TEXT NOT NULL,
    prov_source_excerpt TEXT,
    sensitivity         TEXT NOT NULL,
    consent             TEXT NOT NULL,
    retention           TEXT NOT NULL,
    importance          REAL NOT NULL,
    confidence          REAL NOT NULL,
    created_at          TEXT NOT NULL,
    updated_at          TEXT NOT NULL,
    expires_at          TEXT,
    supersedes          TEXT,
    superseded_by       TEXT,
    reinforcement_count INTEGER NOT NULL DEFAULT 0,
    tags                TEXT NOT NULL DEFAULT '[]',
    project             TEXT,
    idempotency_key     TEXT
);

CREATE INDEX idx_memories_owner_status ON memories (owner_id, status);
CREATE INDEX idx_memories_owner_key ON memories (owner_id, canonical_key);
CREATE UNIQUE INDEX idx_memories_owner_idem
    ON memories (owner_id, idempotency_key)
    WHERE idempotency_key IS NOT NULL;

CREATE TABLE audit_events (
    id          TEXT PRIMARY KEY,
    memory_id   TEXT NOT NULL,
    owner_id    TEXT NOT NULL,
    action      TEXT NOT NULL,
    at          TEXT NOT NULL,
    reason      TEXT NOT NULL,
    from_status TEXT,
    to_status   TEXT,
    detail      TEXT NOT NULL DEFAULT '{}'
);

CREATE INDEX idx_audit_owner_memory ON audit_events (owner_id, memory_id);
"""

# Ordered (version, DDL) pairs. Append new migrations; never rewrite old ones.
MIGRATIONS: list[tuple[int, str]] = [(1, _MIGRATION_1)]


def _current_version(conn: sqlite3.Connection) -> int:
    conn.execute("CREATE TABLE IF NOT EXISTS schema_version (version INTEGER NOT NULL)")
    row = conn.execute("SELECT version FROM schema_version").fetchone()
    return int(row[0]) if row is not None else 0


def apply_migrations(conn: sqlite3.Connection) -> int:
    """Bring ``conn`` up to the latest schema version. Returns the resulting version.

    Idempotent: already-applied migrations are skipped.
    """
    current = _current_version(conn)
    with conn:
        for version, ddl in MIGRATIONS:
            if version > current:
                conn.executescript(ddl)
                current = version
        conn.execute("DELETE FROM schema_version")
        conn.execute("INSERT INTO schema_version (version) VALUES (?)", (current,))
    return current
