# Step 08 — Chat Integration

## Objective

Connect memory to a deterministic chat backend and prove graceful degradation.

## Prerequisites

Steps 05–07 complete.

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

- Define a generation backend protocol.
- Implement deterministic MockBackend.
- Implement chat engine pipeline: guard, decide, mutate, retrieve, compose, generate.
- Add correlation IDs and latency measurement.
- Return debug metadata only when enabled.
- Implement no-memory fallback on storage/retrieval failure.
- Add CLI chat and memory inspection commands.
- Add `/memories`, `/memory`, `/forget`, `/debug`, `/stats`, `/reset`, `/exit`.
- Ensure user-visible answers do not expose internal IDs unless requested.
- Avoid claiming model intelligence from the mock backend.

## Required tests and verification

- end-to-end remember/recall
- correction
- forget and exact-match non-recall
- unsafe write block
- owner isolation through chat
- retrieval timeout fallback
- database-unavailable fallback
- malformed-memory fallback
- debug on/off
- latency metadata
- CLI integration smoke test
- full quality gates

## Done when

The complete Aira Memory lifecycle works through chat with a mock backend, and every injected memory failure still returns a response.

## Explicit exclusions

No PyTorch transformer integration, no web UI, no network APIs.

## Completion report

Report files changed, commands actually run, exact results, measured metrics, limitations, ADR changes, and the command for the next step.
