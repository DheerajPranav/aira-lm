# Step 04 — Aira Vault And Trail

## Objective

Implement local transactional persistence and append-only audit events while preserving owner isolation and deletion integrity.

## Prerequisites

Steps 02 and 03 complete.

## Required procedure

1. Read `CLAUDE.md` and the imported project documents.
2. Inspect the repository and `docs/BUILD_STATUS.md`.
3. Confirm earlier stages are complete.
4. Write a concise implementation plan for this step.
5. Implement only the scope below.
6. Run the required verification.
7. Update `docs/BUILD_STATUS.md`.
8. Update relevant ADRs.
9. Stop. Do not begin the next stage.

## Build scope

- Implement SQLite connection and migrations.
- Create memory and audit-event tables.
- Require owner scope in every repository method.
- Use parameterized SQL.
- Store lifecycle records and provenance.
- Store content hashes and idempotency keys.
- Write memory state and audit event in one transaction.
- Implement create, get, list, update, supersede, archive, expire, forget and hard-delete.
- Ensure hard-delete audit entries omit content and content-derived metadata.
- Add import/export scaffolding with strict validation.
- Add integrity checks and a local backup/export command.
- Exclude runtime data from Git.

## Required tests and verification

- restart persistence
- owner A cannot get/list/update/delete/export owner B
- transaction rollback after injected interruption
- duplicate idempotency key
- forgotten/superseded/expired default filters
- hard delete removes content
- audit event exists for every successful mutation
- audit event contains no hard-deleted content
- parameterization/injection-oriented tests
- migration test
- full quality gates

## Done when

Aira Vault and Aira Trail persist lifecycle state atomically and pass zero-leakage owner tests.

## Explicit exclusions

No FTS retrieval, no evaluator, no chat engine, no encryption claim beyond documented local controls.

## Completion report

Report files changed, commands actually run, exact results, measured metrics, limitations, ADR changes, and the command for the next step.
