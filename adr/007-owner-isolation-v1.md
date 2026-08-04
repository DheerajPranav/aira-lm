# ADR: Require owner isolation from version one

- Status: Accepted (ratified at Step 00 control-tower review)
- Date: 2026-08-04
- Last reviewed: 2026-08-04

## Context

Single-user prototypes often embed assumptions that make later multi-user safety expensive.

## Decision

Require owner_id in domain records, repository methods, retrieval, export and deletion from the first implementation.

## Alternatives considered

Add ownership only during hosted deployment.

## Consequences

Slightly more verbose local API, substantially safer migration path.

## Migration path

Revisit when measured constraints or deployment requirements invalidate the assumptions. Preserve the public interface where practical and document any data migration.

## Traceability

- Upholds invariant: 1 (owner isolation).
- Requirements: `owner_id` required by every persistent operation, retrieval, export and deletion; never return one owner's memory to another.
- Verified in stages: 04 (owner A cannot get/list/update/delete/export owner B), 06 (owner-scoped retrieval), 08 (chat owner isolation), 10 (**cross-owner leakage = 0**).
