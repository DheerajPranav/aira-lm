# Step 05 — Capture And Evaluation

## Objective

Implement transparent extraction, admission and conflict/update policy without relying on an LLM.

## Prerequisites

Steps 02–04 complete.

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

- Implement candidate extraction for explicit remember, preference, identity, project, correction, update, forget and do-not-remember language.
- Keep heuristics isolated and data-driven where practical.
- Run Aira Guard before evaluation and persistence.
- Implement a deterministic utility evaluator.
- Score importance and confidence with explanations.
- Drop low-value temporary text.
- Never store assistant-generated claims as user facts.
- Resolve canonical-key corrections by superseding.
- Require stronger evidence for inferred facts than explicit requests.
- Expose a policy trace in debug mode.
- Preserve exact source provenance.

## Required tests and verification

- explicit remember
- explicit ignore/do-not-remember
- temporary low-value statement
- preference
- project fact
- correction and superseding
- ambiguous correction
- unsafe candidate
- assistant statement non-promotion
- repeat/duplicate candidate
- provenance correctness
- full quality gates

## Done when

A raw turn can safely produce zero or more approved memory operations with transparent reasons and correct lifecycle effects.

## Explicit exclusions

No LLM-based extraction, no embeddings, no retrieval, no model training.

## Completion report

Report files changed, commands actually run, exact results, measured metrics, limitations, ADR changes, and the command for the next step.
