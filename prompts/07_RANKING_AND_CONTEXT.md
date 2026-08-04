# Step 07 — Ranking And Context

## Objective

Implement deterministic score fusion, deduplication and actual-tokenizer context-budget enforcement.

## Prerequisites

Step 06 complete. A tokenizer interface may be implemented minimally here if required for budget counting, but full Aira Core remains Step 11.

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

- Implement score components for lexical relevance, importance, confidence, recency, reinforcement, project relevance, kind priority and decay penalty.
- Normalize components safely.
- Keep weights configurable.
- Return complete score breakdowns.
- Deduplicate canonical and near-identical results using deterministic rules.
- Implement a delimited untrusted-memory context format.
- Prevent retrieved instructions from becoming system policy.
- Enforce top-k and exact byte-token budget.
- Support debug IDs but hide them in normal mode.
- Record why each memory was included or excluded.

## Required tests and verification

- score component tests
- ordering tests
- tie determinism
- inactive-state defense in depth
- deduplication
- prompt-injection-like memory remains quoted data
- exact budget boundary
- multibyte Unicode budget
- no context overflow
- full quality gates

## Done when

Aira can produce a bounded, transparent and safely delimited memory block from retrieved candidates.

## Explicit exclusions

No response generation integration, no vector retrieval, no learned reranker.

## Completion report

Report files changed, commands actually run, exact results, measured metrics, limitations, ADR changes, and the command for the next step.
