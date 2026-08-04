# ADR: Memory failure degrades to no-memory generation

- Status: Accepted (ratified at Step 00 control-tower review)
- Date: 2026-08-04
- Last reviewed: 2026-08-04

## Context

Memory is personalization, not a prerequisite for basic response generation.

## Decision

Bound memory operations and catch isolated failures. Generate with empty memory context and emit a degraded event.

## Alternatives considered

Fail the whole chat request; retry indefinitely.

## Consequences

Availability improves, while personalization may temporarily disappear.

## Migration path

Revisit when measured constraints or deployment requirements invalidate the assumptions. Preserve the public interface where practical and document any data migration.

## Traceability

- Upholds invariant: 3 (graceful degradation).
- Requirements: bound retrieval time; isolate memory exceptions from generation; degrade to a no-memory response.
- Verified in stages: 06 (bounded retrieval), 08 (timeout / DB-unavailable / malformed-memory fallbacks each still respond), 10 (degraded-response success measured).
