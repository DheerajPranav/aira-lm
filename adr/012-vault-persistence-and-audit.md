# ADR: Owner-scoped SQLite persistence with single-transaction audit and row-deleting hard delete

- Status: Accepted
- Date: 2026-08-07
- Last reviewed: 2026-08-07

## Context

Step 04 gives memories durable local storage and an append-only audit trail, on SQLite
(ADR-002). Several invariants must hold at the persistence boundary: owner isolation
(1), deletion integrity (2), secret/content non-persistence in audit (7), and
transactional lifecycle where state and audit succeed or fail together (11).

## Decision

1. **Owner scope on every method.** Every repository read and write takes an
   ``owner_id`` and includes ``WHERE owner_id = ?``. There is one repository layer and
   all SQL is parameterized. A cross-owner request returns nothing (reads) or raises
   ``NotFoundError`` (writes) — it cannot observe another owner's data.
2. **State and audit in one transaction.** Each mutation wraps the memory write and its
   audit insert in a single ``with connection:`` block, so both commit or both roll back
   (invariant 11). A failure injected into the audit write leaves no memory row.
3. **Hard delete removes the row.** Hard deletion ``DELETE``s the memory row and writes
   an audit event whose ``detail`` is empty; ``AuditEvent`` rejects any content-derived
   key defensively. Nothing content-bearing survives a hard delete (invariants 2, 7).
   Forgotten / superseded / expired memories remain as rows in their status and are
   filtered out of normal reads by default.
4. **Globally-unique memory ids.** ``id`` is the primary key across all owners; owner
   scoping is access control, not an id namespace. Import into a store that already
   holds an id is a conflict (and rolls back).
5. **Idempotent create.** A create carrying an existing ``(owner_id, idempotency_key)``
   returns the existing record and writes nothing (a unique partial index backs it).
6. **Read-time integrity.** Rebuilding a record from a row runs full domain validation,
   including content-hash verification, so tampered or corrupt rows are rejected on read.
7. **Bounded, validated, guard-screened import.** JSONL import checks the schema
   version, bounds payload size, rebinds records to the importing owner, screens each
   record's content through Aira Guard, and writes atomically. No at-rest encryption is
   claimed beyond documented local file-system trust.

## Alternatives considered

- Keep a deleted row with content nulled instead of deleting it. Rejected: a missed
  column or code path could leak; deleting the row makes leakage impossible.
- Separate transactions for state and audit. Rejected: a crash between them breaks
  invariant 11.
- Per-owner id namespaces. Rejected: needless complexity; global ids keep references
  (supersedes/superseded_by) and audit simple.

## Consequences

- Zero-leakage owner and deletion properties are cheap to test and are covered by
  adversarial two-owner tests, a rollback-injection test, and a hard-delete-audit test.
- Hard delete is irreversible by design; recovery relies on the backup/export commands.
- SQLite gives transactions and portability but not hosted multi-tenant controls
  (e.g. PostgreSQL row-level security); that remains a documented migration target.

## Traceability

- Upholds invariants: 1 (owner isolation), 2 (deletion integrity), 7 (no content in
  audit), 11 (transactional lifecycle), 12 (read-time hash integrity).
- Realized in stage 04; consumed by capture (Step 05), recall (Step 06) and governance
  (Step 09).

## Migration path

Preserve the repository interface and the versioned migration list. A move to
PostgreSQL would add row-level security and replace the connection/schema modules while
keeping method contracts and the audit-content-omission rule intact.
