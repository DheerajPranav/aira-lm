# ADR: Use deterministic memory policy before learned policy

- Status: Accepted (ratified at Step 00 control-tower review)
- Date: 2026-08-04
- Last reviewed: 2026-08-04

## Context

An untrained tiny model cannot safely decide what to remember, and policy decisions require repeatability.

## Decision

Use transparent heuristics and deterministic scoring, with a later learned-policy experiment behind the same interface.

## Alternatives considered

Use the response model as extractor/evaluator from day one.

## Consequences

More predictable and testable, but lower linguistic coverage.

## Migration path

Revisit when measured constraints or deployment requirements invalidate the assumptions. Preserve the public interface where practical and document any data migration.

## Traceability

- Upholds invariants: 5 (selective admission through a transparent write gate), 6 (no assistant→user fact promotion), 12 (measured, repeatable decisions).
- Requirements: deterministic evaluator; importance/confidence with explanations; explicit-source distinction.
- Verified in stage: 05 (extraction, admission, conflict resolution with policy trace and provenance).
