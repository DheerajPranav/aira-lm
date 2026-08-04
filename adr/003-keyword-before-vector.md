# ADR: Implement keyword retrieval before vector retrieval

- Status: Accepted (ratified at Step 00 control-tower review)
- Date: 2026-08-04
- Last reviewed: 2026-08-04

## Context

Exact facts, names and versions matter, while hosted embeddings violate the local-first boundary.

## Decision

Use FTS5 or deterministic BM25 first. Add a retriever interface for later vector search.

## Alternatives considered

Require embeddings immediately; use only vector similarity.

## Consequences

Gives explainable offline retrieval; semantic recall remains limited until a local embedding path is justified.

## Migration path

Revisit when measured constraints or deployment requirements invalidate the assumptions. Preserve the public interface where practical and document any data migration.

## Traceability

- Upholds invariants: 2 (lifecycle-aware retrieval excludes forbidden states), 8 (explainable, inspectable retrieval keeps memory as data).
- Requirements: keyword retrieval (FTS5/BM25), retriever interface with deferred vector path.
- Verified in stages: 06 (FTS5/BM25 retrieval, exact-string recall), 07 (deterministic ranking and score explanations).
- Probe (2026-08-04): FTS5 available; Step 06 must still detect at runtime and keep the BM25 fallback.
