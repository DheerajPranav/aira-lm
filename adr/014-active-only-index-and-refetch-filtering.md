# ADR: Active-only search index with re-fetch filtering, and a BM25 fallback

- Status: Accepted
- Date: 2026-08-08
- Last reviewed: 2026-08-08

## Context

Step 06 adds keyword retrieval. It must be owner-scoped and lifecycle-aware with
**zero** leakage of forgotten, superseded, expired, deleted or cross-owner memories
(invariants 1, 2), explainable, deterministic (invariant 12), and work whether or not
the SQLite build ships FTS5 (ADR-003). Retrieved memory remains untrusted data
(invariant 8) — retrieval only finds and ranks; it does not compose context.

## Decision

1. **FTS5 when available, BM25 otherwise.** `connect()` creates an FTS5 index if the
   build supports it and records availability; `build_retriever()` returns an
   `Fts5Retriever`, else the pure-Python `Bm25Retriever`. Both implement one `Retriever`
   protocol.
2. **The index holds only active content.** The repository maintains the FTS index
   inside its write transactions: active rows are indexed on insert/update; any
   transition to a non-active status (archive/expire/forget/supersede-old) and hard
   delete remove the entry. Forbidden content is therefore never in the index.
3. **Re-fetch filtering as defense in depth.** The FTS retriever uses the index only to
   generate candidate ids, then re-fetches each through the owner-scoped, active-only
   `get`. Even a hypothetically stale index entry cannot surface — the owner and status
   are re-checked against the source of truth.
4. **BM25 over the live active set.** The fallback scores the active, owner-scoped rows
   read through the repository, so there is no separate index to fall out of sync; it is
   also the reference implementation and is fully deterministic (score desc, then oldest,
   then id).
5. **Safe, bounded queries.** Queries are tokenized to alphanumeric terms; the FTS MATCH
   expression is built from quoted terms, so arbitrary input (operators, quotes,
   injection-looking strings) cannot cause an FTS syntax error or injection. Query
   length, term count and top-k are bounded.
6. **Vector and graph retrievers are deferred protocols, not fakes.** They are declared
   as interfaces with no first-release implementation.

## Alternatives considered

- Index everything and filter forbidden states only at query time. Rejected: content of
  deleted/forgotten memories would remain in the index — an index-leakage risk the
  threat model calls out.
- Trust the FTS index alone (no re-fetch). Rejected: a single missed maintenance path
  would leak; re-fetching against the owner-scoped active `get` makes leakage impossible.
- Require FTS5. Rejected: the BM25 fallback keeps the system working on minimal SQLite
  builds and serves as a deterministic reference.

## Consequences

- Zero forbidden-state and cross-owner leakage is structurally guaranteed and tested
  across both backends (forgotten/superseded/expired/hard-deleted exclusion, owner
  isolation, index purge on hard delete).
- The BM25 fallback is O(n) per query over the active set — fine at local scale, and the
  FTS path scales further. No semantic-quality claim is made; this is keyword retrieval.

## Traceability

- Upholds invariants: 1 (owner isolation), 2 (deletion/lifecycle integrity via
  active-only index + re-fetch), 8 (retrieval returns data, not instructions), 12
  (deterministic, explainable).
- Realized in stage 06; consumed by ranking and context building (Step 07) and chat (08).

## Migration path

A future vector or hybrid retriever implements the same `Retriever` protocol and must
preserve owner scoping, the active-only guarantee and re-fetch filtering.
