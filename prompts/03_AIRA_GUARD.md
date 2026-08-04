# Step 03 — Aira Guard

## Objective

Implement the pre-persistence safety and privacy gate with deterministic secret detection and redaction.

## Prerequisites

Step 02 complete.

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

- Create a replaceable Guard interface.
- Detect common API-key forms, bearer tokens, private-key blocks, password assignments, credential-bearing URLs, cookies and payment-card-like patterns.
- Add explicit “do not remember” and memory-policy override detection.
- Produce decision, category, reason, confidence and redacted preview.
- Never return or log raw matched secrets.
- Add input-size limits.
- Add classification hooks for personal, sensitive and restricted data.
- Keep false-positive trade-offs documented.
- Ensure debug output is safe.
- Add structured guard events without raw sensitive content.

## Required tests and verification

- one test per secret category
- secret embedded in normal prose
- multiline private key
- redaction correctness
- no secret in exception text
- no secret in captured logs
- no secret in serialized guard event
- benign values that resemble secrets
- oversized input
- full quality gates

## Done when

Guard behavior is deterministic, safely redacted and independently testable. The secret-persistence test scaffold reports zero persisted values.

## Explicit exclusions

No database writes except test fakes, no third-party PII service, no LLM evaluator.

## Completion report

Report files changed, commands actually run, exact results, measured metrics, limitations, ADR changes, and the command for the next step.
