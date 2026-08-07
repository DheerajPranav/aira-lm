"""Aira Vault — local transactional persistence for memories.

SQLite-backed, owner-scoped and parameterized. Memory state and its audit event are
written together in one transaction; hard deletion removes content and records a
content-free audit event. Retrieval, ranking and chat build on this layer later.
"""

from __future__ import annotations

from aira.memory.vault.backup import (
    MAX_IMPORT_BYTES,
    backup_database,
    export_jsonl,
    import_jsonl,
    integrity_check,
)
from aira.memory.vault.connection import connect
from aira.memory.vault.errors import ImportRejectedError, NotFoundError, VaultError
from aira.memory.vault.repository import MemoryRepository
from aira.memory.vault.schema import (
    SCHEMA_VERSION,
    apply_migrations,
    ensure_search_index,
    search_enabled,
)

__all__ = [
    "MAX_IMPORT_BYTES",
    "SCHEMA_VERSION",
    "ImportRejectedError",
    "MemoryRepository",
    "NotFoundError",
    "VaultError",
    "apply_migrations",
    "backup_database",
    "connect",
    "ensure_search_index",
    "export_jsonl",
    "import_jsonl",
    "integrity_check",
    "search_enabled",
]
