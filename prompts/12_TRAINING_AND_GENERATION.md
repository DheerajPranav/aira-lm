# Step 12 — Training And Generation

## Objective

Implement local training, checkpointing and autoregressive generation with safe smoke modes.

## Prerequisites

Step 11 complete.

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

- Implement local text dataset and train/validation split.
- Implement fixed-length causal batches.
- Add AdamW, clipping, warmup and configurable schedule.
- Add periodic validation.
- Add deterministic seed control.
- Add checkpoint save/load/resume with schema version.
- Add greedy, temperature and top-k generation.
- Add graceful interruption handling.
- Add tiny sample corpus and smoke config.
- Track loss, perplexity, elapsed time and peak memory where possible.
- Do not automatically download datasets.

## Required tests and verification

- dataset boundaries
- deterministic batch
- one-step training
- loss finite and generally decreases on an overfit fixture
- checkpoint round trip
- resume
- deterministic greedy generation
- sampling validation
- smoke training completes on CPU
- full quality gates

## Done when

A local smoke run trains, validates, saves, reloads and generates text reproducibly without exceeding the intended small-machine scope.

## Explicit exclusions

No large corpus, no claimed language quality, no distributed training.

## Completion report

Report files changed, commands actually run, exact results, measured metrics, limitations, ADR changes, and the command for the next step.
