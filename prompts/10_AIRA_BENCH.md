# Step 10 — Aira Bench

## Objective

Create a versioned golden and adversarial evaluation system and enforce zero-tolerance security metrics.

## Prerequisites

Steps 08–09 complete.

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

- Define benchmark JSONL schema and versioning.
- Build scenarios from EVALUATION_PLAN.
- Implement precision, recall, recall@k, MRR, correction success, stale leakage, forgotten leakage, cross-owner leakage, secret persistence, budget violations, degraded-response success and latency.
- Compare no-memory, Aira Memory and practical full-history baselines.
- Produce machine-readable JSON and readable Markdown reports.
- Add regression thresholds.
- Add a CLI command.
- Ensure deterministic fixtures and fixed clocks.
- Document the difference between retrieval evaluation and generation evaluation.

## Required tests and verification

- benchmark schema validation
- metric unit tests
- all required golden cases
- all adversarial cases
- zero cross-owner leakage
- zero forgotten leakage
- zero secret persistence
- zero budget violations
- successful degraded responses
- report reproducibility
- full quality gates

## Done when

Aira Bench produces repeatable evidence and fails the build when a zero-tolerance invariant regresses.

## Explicit exclusions

No LLM-as-judge as sole evaluator, no public production claim.

## Completion report

Report files changed, commands actually run, exact results, measured metrics, limitations, ADR changes, and the command for the next step.
