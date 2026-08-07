"""SQLite connection factory for Aira Vault.

Opens a connection with sane defaults (row access by name, foreign keys on) and applies
migrations. Uses the default deferred isolation so ``with connection:`` blocks form
atomic transactions.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

from aira.memory.vault.schema import apply_migrations


def connect(database_path: str | Path) -> sqlite3.Connection:
    """Open (creating if needed) an Aira Vault database and migrate it to the latest schema.

    Args:
        database_path: Filesystem path, or ``":memory:"`` for an ephemeral database.

    Returns:
        An open, migrated :class:`sqlite3.Connection`.
    """
    conn = sqlite3.connect(str(database_path))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    apply_migrations(conn)
    return conn
