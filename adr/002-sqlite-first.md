# ADR: Use SQLite for the local reference implementation

- Status: Accepted (ratified at Step 00 control-tower review)
- Date: 2026-08-04
- Last reviewed: 2026-08-04

## Context

The primary target is one M2 Mac with 8 GB RAM and no infrastructure requirement.

## Decision

Use SQLite with migrations and explicit repository interfaces. Preserve a migration path to PostgreSQL.

## Alternatives considered

Start with PostgreSQL and pgvector; use an embedded vector database.

## Consequences

Simple setup and transactions; lacks hosted multi-tenant controls such as PostgreSQL row-level security.

## Migration path

Revisit when measured constraints or deployment requirements invalidate the assumptions. Preserve the public interface where practical and document any data migration.

## Traceability

- Upholds invariants: 1 (owner isolation via one owner-scoped repository layer), 2 (deletion integrity), 11 (transactional lifecycle).
- Requirements: local persistence, parameterized SQL, transactions for multi-step writes, recoverable local migrations.
- Verified in stage: 04 (connection, migrations, transactional state+event writes, restart persistence).
- Probe (2026-08-04): system `sqlite3` runtime is 3.47.0 with FTS5 available.
