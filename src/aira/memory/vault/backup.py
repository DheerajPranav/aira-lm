"""Local backup, integrity check and JSONL import/export for Aira Vault.

Export excludes forbidden states by default and is owner-scoped. Import validates the
schema version, bounds input size, rebinds records to the importing owner, screens each
record's content through Aira Guard, and writes atomically — a single bad record leaves
the database unchanged.

No encryption is claimed here beyond the local file-system trust documented in the
threat model.
"""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from aira.memory.guard.interface import Guard
from aira.memory.vault.errors import ImportRejectedError
from aira.memory.vault.mapper import EXPORT_SCHEMA_VERSION, dict_to_memory, memory_to_export
from aira.memory.vault.repository import MemoryRepository

# Bound import size to avoid resource exhaustion (a denial-of-service control).
MAX_IMPORT_BYTES = 5_000_000


def integrity_check(conn: sqlite3.Connection) -> bool:
    """Return whether SQLite reports the database as structurally intact."""
    row = conn.execute("PRAGMA integrity_check").fetchone()
    return bool(row) and row[0] == "ok"


def backup_database(conn: sqlite3.Connection, destination: str | Path) -> Path:
    """Write a consistent copy of the database to ``destination`` using SQLite's backup API."""
    dest = Path(destination)
    with sqlite3.connect(str(dest)) as target:
        conn.backup(target)
    return dest


def export_jsonl(
    repository: MemoryRepository, owner_id: str, *, include_inactive: bool = False
) -> str:
    """Serialize an owner's memories to newline-delimited JSON."""
    records = repository.export(owner_id, include_inactive=include_inactive)
    return "\n".join(json.dumps(memory_to_export(r)) for r in records)


def import_jsonl(repository: MemoryRepository, owner_id: str, text: str, *, guard: Guard) -> int:
    """Validate, guard-screen and atomically import owner-bound records from JSONL.

    Raises:
        ImportRejectedError: If the payload is too large, malformed, of an unknown schema
            version, or contains content the guard blocks. Nothing is written on rejection.
    """
    if len(text.encode("utf-8")) > MAX_IMPORT_BYTES:
        raise ImportRejectedError("import payload exceeds maximum size")

    records = []
    for lineno, raw in enumerate(text.splitlines(), start=1):
        line = raw.strip()
        if not line:
            continue
        try:
            data = json.loads(line)
        except json.JSONDecodeError as exc:
            raise ImportRejectedError(f"line {lineno}: invalid JSON") from exc
        if not isinstance(data, dict):
            raise ImportRejectedError(f"line {lineno}: expected a JSON object")
        if data.get("schema_version") != EXPORT_SCHEMA_VERSION:
            raise ImportRejectedError(f"line {lineno}: unknown or missing schema_version")

        content = data.get("content")
        if not isinstance(content, str) or not content.strip():
            raise ImportRejectedError(f"line {lineno}: missing content")
        scan = guard.scan(content)
        if scan.blocked:
            raise ImportRejectedError(f"line {lineno}: blocked by guard ({scan.reason})")

        try:
            record = dict_to_memory(data, owner_id=owner_id)
        except (KeyError, ValueError) as exc:
            raise ImportRejectedError(f"line {lineno}: {exc}") from exc
        records.append(record)

    return repository.import_records(owner_id, records)
