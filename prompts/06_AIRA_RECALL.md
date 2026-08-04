# Step 06 — Aira Recall

## Objective

Implement owner-scoped keyword retrieval using SQLite FTS5 or a documented local BM25 fallback.

## Prerequisites

Steps 04–05 complete.

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

- Determine and record SQLite FTS5 availability.
- Implement a retriever interface.
- Implement FTS5 retrieval when available.
- Implement a small deterministic BM25 fallback when necessary.
- Filter owner and lifecycle status before candidates reach ranking.
- Support kind, lifetime, tag and project filters.
- Return score explanations.
- Keep vector and graph retriever interfaces deferred, not fake implementations.
- Add index maintenance for create/update/supersede/forget/delete.
- Bound query size, top-k and execution time where practical.

## Required tests and verification

- exact-string name/version retrieval
- relevant keyword ranking
- owner isolation
- forgotten exact-match exclusion
- superseded and expired exclusion
- filter behavior
- empty query
- malformed query
- index update after correction
- hard delete removes searchable content
- deterministic results
- retrieval latency benchmark on a small fixture
- full quality gates

## Done when

Keyword retrieval is correct, owner-scoped, lifecycle-aware and explainable, with zero forbidden-state leakage.

## Explicit exclusions

No embeddings, no graph database, no semantic-quality claims.

## Completion report

Report files changed, commands actually run, exact results, measured metrics, limitations, ADR changes, and the command for the next step.
