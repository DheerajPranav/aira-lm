# Step 11 — Aira Core

## Objective

Implement the byte tokenizer and compact decoder-only transformer directly in PyTorch.

## Prerequisites

Memory runtime and benchmark through Step 10 complete.

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

- Implement reversible UTF-8 byte tokenizer with vocabulary 256.
- Implement learned token and positional embeddings.
- Implement pre-norm causal transformer blocks.
- Implement multi-head causal self-attention.
- Implement feed-forward GELU layers.
- Tie input/output embeddings where valid.
- Implement causal LM loss.
- Implement exact parameter count.
- Implement device selection integration.
- Keep default configuration near 5–10M parameters and M2-safe.
- Implement a TinyTransformerBackend adapter without requiring a checkpoint for other tests.

## Required tests and verification

- tokenizer English/Unicode/punctuation/empty/invalid bytes
- causal mask
- output shape
- loss
- no future-token influence
- parameter count range
- MPS/CPU smoke path
- deterministic initialization
- full quality gates

## Done when

Aira Core is a correct, readable tiny causal language model with independent tests and no training claims.

## Explicit exclusions

No pretrained Hugging Face model, no large download, no long training run, no architectural novelty claim.

## Completion report

Report files changed, commands actually run, exact results, measured metrics, limitations, ADR changes, and the command for the next step.
