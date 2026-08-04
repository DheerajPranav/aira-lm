# Step 02 — Memory Schema Lifecycle

## Objective

Implement the typed memory domain model and a validated lifecycle state machine independent of persistence.

## Prerequisites

Step 01 complete.

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

- Implement enums for memory action, kind, lifetime, status, sensitivity, consent and retention.
- Implement immutable or carefully validated domain records.
- Include all schema fields required by REQUIREMENTS.
- Implement lifecycle transitions: create, update, supersede, archive, expire, forget and hard-delete tombstone.
- Reject illegal transitions.
- Use UTC-aware timestamps.
- Implement canonical keys, normalized content and content hashes.
- Implement decision/result records with human-readable reasons.
- Keep SQL and storage out of this step.
- Write ADR updates if schema choices differ from the supplied proposal.

## Required tests and verification

- score-range validation
- timestamp validation
- required owner and provenance
- every allowed transition
- every forbidden transition
- superseding links
- hard-delete tombstone contains no content
- deterministic hashing
- full pytest, lint and type checks

## Done when

The domain layer can represent and validate the entire memory lifecycle without persistence and without violating invariants.

## Explicit exclusions

No SQLite, no extraction heuristics, no retrieval, no secrets detector, no model code.

## Completion report

Report files changed, commands actually run, exact results, measured metrics, limitations, ADR changes, and the command for the next step.
