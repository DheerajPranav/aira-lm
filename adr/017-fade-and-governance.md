# ADR: Manual fade job and explicit user governance

- Status: Accepted
- Date: 2026-08-09
- Last reviewed: 2026-08-09

## Context

Step 09 adds lifecycle maintenance and user controls. Background aging must be
deterministic and off the request path, must never silently destroy data, and must
respect the feedback-poisoning control (no reinforcement just because a memory was
retrieved). Users must be able to inspect, explain, correct, forget, export and delete
their own memories, and imports must stay safe. There is no scheduler daemon or
distributed worker in the first release.

## Decision

1. **Fade is a manually-invokable, deterministic job.** `FadeJob.run(now=...)` archives
   memories whose per-kind decay score falls below the configured threshold and expires
   memories by retention policy (fixed-expiry past `expires_at`, and session-only). Decay
   is a pure function of age since `updated_at` and a kind half-life, so an update or a
   reinforcement refreshes it. The job runs on demand (`aira fade`, `/fade`), not on a
   timer.
2. **Fade never hard-deletes.** It only moves memories to ARCHIVED or EXPIRED (both
   audited, both filtered from normal retrieval). Destructive hard deletion is always an
   explicit user action.
3. **Reinforcement is explicit only.** `reinforce` increments the count and refreshes
   recency, and is called only on explicit usefulness evidence — never as a side effect
   of retrieval (the read path does not touch reinforcement). This guards against
   feedback poisoning.
4. **Governance = owner-scoped, audited user control.** Inspect, explain (record + audit
   trail), correct (guard-screened supersede), archive, forget, set-retention, export
   (forbidden states excluded by default), guard-screened atomic import, and a
   `delete_all` that hard-deletes only the requesting owner's memories. User control
   overrides automated retention (invariant 9).
5. **Corrections and imports are guarded.** New correction content and every imported
   record's content pass through Aira Guard before anything is written; a block aborts
   the operation with nothing persisted.

## Alternatives considered

- A background scheduler/daemon for decay. Rejected for the first release (excluded);
  a manually-invoked job is deterministic and testable, and a scheduler can wrap it later.
- Reinforce on retrieval for "natural" strengthening. Rejected: it is exactly the
  feedback-poisoning vector the threat model calls out.
- Let fade hard-delete very stale memories. Rejected: deletion must be a deliberate user
  act; fade archives/expires instead, keeping everything recoverable and auditable.

## Consequences

- Aging is reproducible and covered by fixed-clock tests (decay determinism, kind-specific
  rates, archive threshold, expiry, no-auto-hard-delete). User controls are covered
  (inspect/explain, correction incl. guard block, export filtering, import rollback,
  owner-scoped delete-all, explicit reinforcement).
- Because fade is manual, stale memories persist until a run is invoked — an accepted
  trade-off for the local release; a scheduler is a future enhancement.

## Traceability

- Upholds invariants: 9 (user control overrides automation), 2 (archived/expired excluded
  from retrieval; no implicit destruction), 4 (provenance/audit on every action), 5/12
  (deterministic, tested), and the feedback-poisoning control (reinforcement gating).
- Realized in stage 09; surfaced through the chat session and `aira fade`.

## Migration path

A scheduler or workflow engine may later call `FadeJob.run` on an interval without
changing its contract. Governance operations keep their signatures if a hosted API wraps
them; the guard-before-write and owner-scoping rules must be preserved.
