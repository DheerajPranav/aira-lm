# ADR: Audit deletion without retaining deleted content

- Status: Accepted (ratified at Step 00 control-tower review)
- Date: 2026-08-04
- Last reviewed: 2026-08-04

## Context

An append-only audit log can undermine hard deletion if it retains the original content.

## Decision

Retain event ID, actor, time, memory ID and reason, but omit deleted content and content-derived previews.

## Alternatives considered

Keep full before/after records in audit history.

## Consequences

Supports deletion intent while preserving operational traceability; reduces forensic detail.

## Migration path

Revisit when measured constraints or deployment requirements invalidate the assumptions. Preserve the public interface where practical and document any data migration.

## Traceability

- Upholds invariants: 2 (deletion integrity), 7 (secret non-persistence extends to audit metadata).
- Requirements: append-only audit stream; hard deletion must not preserve content in audit events.
- Verified in stages: 04 (hard-delete audit omits content and content-derived previews), 09 (governance operations remain auditable), 10 (**forgotten leakage = 0**, **secret persistence = 0**).
