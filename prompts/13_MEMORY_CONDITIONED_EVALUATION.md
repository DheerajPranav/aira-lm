# Step 13 — Memory Conditioned Evaluation

## Objective

Integrate Aira Core with Aira Memory and measure whether retrieved memory improves controlled tasks.

## Prerequisites

Steps 10–12 complete.

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

- Connect TinyTransformerBackend to chat without coupling memory to PyTorch internals.
- Create controlled memory-conditioned evaluation tasks.
- Compare no-memory, Aira Memory and full-history baselines.
- Measure factual adherence, correction adherence, forgotten-fact non-disclosure, context cost and latency.
- Separate retriever failures from generator failures.
- Record model/checkpoint/config versions.
- Report negative or inconclusive results honestly.
- Add ablation controls for ranking signals where practical.

## Required tests and verification

- backend adapter integration
- no-memory baseline
- memory baseline
- correction scenario
- forgetting scenario
- context budget
- result reproducibility
- benchmark report
- full quality gates

## Done when

The repository contains a reproducible experiment answering whether memory helps the current tiny checkpoint on controlled tasks, without overstating results.

## Explicit exclusions

No cherry-picked public claim, no frontier-model comparison, no automatic online learning.

## Completion report

Report files changed, commands actually run, exact results, measured metrics, limitations, ADR changes, and the command for the next step.
