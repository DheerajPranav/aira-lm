# ADR: Separate Aira Core from Aira Memory

- Status: Accepted (ratified at Step 00 control-tower review)
- Date: 2026-08-04
- Last reviewed: 2026-08-04

## Context

A useful memory runtime must be testable before the tiny model is trained, and memory behavior must not depend on one model architecture.

## Decision

Maintain a backend protocol. Aira Memory depends on the protocol, not PyTorch. MockBackend is the initial end-to-end backend.

## Alternatives considered

Tightly integrate memory into transformer code; test only after training.

## Consequences

Improves testability and reuse, but adds an interface boundary.

## Migration path

Revisit when measured constraints or deployment requirements invalidate the assumptions. Preserve the public interface where practical and document any data migration.

## Traceability

- Upholds invariant: 3 (graceful degradation is possible because memory depends on a backend protocol, not on a trained model).
- Requirements: mock generation backend; backend interface for Aira Core.
- Verified in stages: 01 (namespaces), 08 (`MockBackend`), 11 (`TinyTransformerBackend`), 13 (integration without coupling memory to PyTorch).
