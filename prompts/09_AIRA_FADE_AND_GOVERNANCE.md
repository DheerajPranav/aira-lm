# Step 09 — Aira Fade And Governance

## Objective

Implement lifecycle jobs and user-control operations for decay, expiry, archival, correction, inspection, export and deletion.

## Prerequisites

Step 08 complete.

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

- Implement manually invokable Aira Fade job.
- Calculate configurable type-specific decay.
- Separate retrieval from reinforcement; reinforce only after explicit usefulness evidence.
- Archive below threshold.
- Expire according to retention.
- Never automatically hard-delete.
- Implement inspect-all, explain-source, correct, archive, forget, hard-delete, export and delete-all.
- Validate imports with guard scanning and atomic rollback.
- Record audit events for every operation.
- Add consent and retention policy enforcement.
- Add CLI commands and documentation.

## Required tests and verification

- fixed-clock decay
- kind-specific rates
- retrieval without reinforcement
- explicit reinforcement
- archive threshold
- expiry
- no automatic hard delete
- inspect and explain
- correction
- export excludes forbidden states by default
- malformed/unsafe import rollback
- delete-all owner isolation
- full quality gates

## Done when

Users control their memory lifecycle, background policy is deterministic, and every action remains auditable without retaining hard-deleted content.

## Explicit exclusions

No scheduler daemon, no cloud key manager, no distributed worker.

## Completion report

Report files changed, commands actually run, exact results, measured metrics, limitations, ADR changes, and the command for the next step.
