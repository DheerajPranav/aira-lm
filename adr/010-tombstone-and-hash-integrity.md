# ADR: Content-free tombstone type and content-hash integrity on records

- Status: Accepted
- Date: 2026-08-06
- Last reviewed: 2026-08-06

## Context

Step 02 implements the typed memory domain and lifecycle. Two invariants must hold at
the domain level, before any persistence exists: hard deletion must leave no content
(invariants 2 and 7), and content hashes must be trustworthy and reproducible
(invariant 12). Enforcing these by convention (remembering to strip fields, remembering
to recompute a hash) is fragile.

## Decision

1. **Hard delete returns a distinct `Tombstone` type, not a `MemoryRecord` with a
   DELETED status.** The tombstone dataclass has only `id`, `owner_id`, `deleted_at`,
   `reason` and a fixed `DELETED` status — it has *no* `content`, `content_hash` or
   `canonical_key` field. "No content survives a hard delete" is therefore guaranteed
   by the type, not by discipline. A `MemoryRecord` is forbidden from holding DELETED
   status.
2. **`MemoryRecord` validates that `content_hash` equals the SHA-256 of its normalized
   content on every construction** (including every `dataclasses.replace`). Records are
   frozen; all content changes go through helpers that recompute the hash. A tampered
   or stale hash raises `ValidationError`.
3. **Records are immutable (frozen, slotted) value objects**; lifecycle transitions are
   pure functions returning new instances, rejecting transitions not allowed from the
   current status.

## Alternatives considered

- Represent deletion as a normal record with `status=DELETED` and content nulled out.
  Rejected: a single missed field or a later code path could leak content; the type
  cannot enforce absence.
- Trust callers to supply a correct `content_hash`. Rejected: no integrity guarantee
  and non-reproducible behaviour.

## Consequences

- Deletion integrity and hash integrity are enforced structurally and are cheap to
  test. Persistence (Step 04) maps the tombstone to an audit entry that likewise omits
  content.
- Slightly more code: a second type and a factory (`make_memory`) plus lifecycle
  helpers, rather than free-form construction.

## Traceability

- Upholds invariants: 2 (deletion integrity), 7 (secret/content non-persistence in
  deleted state), 11 (transition validity), 12 (deterministic, verifiable hashing).
- Realized in stage 02; consumed by Aira Vault and Trail (Step 04).

## Migration path

If storage later needs a deleted-row marker, persist the tombstone's minimal fields
only. Preserve the `MemoryRecord` / `Tombstone` split so no code path can serialize
deleted content.
