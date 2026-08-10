# ADR: Aira Core — a small GPT-style transformer written directly in PyTorch

- Status: Accepted
- Date: 2026-08-11
- Last reviewed: 2026-08-11

## Context

Step 11 builds the model half of the project: a byte tokenizer and a compact
decoder-only transformer. It must be correct, readable and M2-safe, land near 5–10M
parameters, and plug into the existing chat backend interface — with no pretrained
weights, no large download beyond PyTorch itself, and no training or quality claim yet.

## Decision

1. **Reversible byte tokenizer, vocabulary 256.** Each token is one UTF-8 byte. Any text
   round-trips exactly; decoding arbitrary ids never raises (invalid UTF-8 is replaced).
   No learned parameters, no training, and it satisfies the ranking `Tokenizer` protocol
   (`count`).
2. **Standard, readable GPT-style architecture.** Learned token + positional embeddings,
   pre-norm blocks with multi-head causal self-attention and a GELU feed-forward, a final
   norm and a language-model head. No architectural novelty is claimed.
3. **Explicit causal masking.** Attention builds a lower-triangular mask and fills future
   positions with `-inf` before softmax. This is written out (rather than relying on a
   fused causal kernel) so "no future-token influence" is directly verifiable and the code
   is legible.
4. **Tied embeddings by default.** The LM head shares the token-embedding weight when
   configured, so it is counted once. The default config yields **6,515,200** parameters —
   within the 5–10M target.
5. **Deterministic initialization.** Weights are initialized from a fixed normal (std
   0.02); `build_model(cfg, seed=...)` seeds torch first, so construction is reproducible.
6. **Backend adapter over a checkpoint-free model.** `TinyTransformerBackend` implements
   the chat `GenerationBackend` protocol using greedy decoding, so the model can serve chat
   and be tested without any trained checkpoint. Its output from an untrained model is
   meaningless but deterministic; no quality claim is made.
7. **PyTorch enters here.** torch is the `core` runtime extra and is added to the dev
   dependency group so the test suite exercises Core. The **memory runtime keeps zero torch
   imports** — the two-system boundary is preserved in code even though torch is now
   installed.

## Alternatives considered

- A fused causal-attention kernel (`scaled_dot_product_attention(is_causal=True)`).
  Rejected for the reference implementation: explicit masking is more readable and makes
  the no-future-influence property directly testable. A fused path can be an optimization
  later.
- A learned/BPE tokenizer. Rejected: byte-level keeps the vocabulary at 256, needs no
  training, and makes exact facts (names, versions) representable — matching the data
  strategy (ADR-009).
- Making torch a top-level runtime dependency. Kept it as the `core` extra plus the dev
  group, so a memory-only consumer can still install without torch; the code boundary is
  what actually enforces independence.

## Consequences

- Aira Core is a correct, readable tiny causal LM with independent tests (tokenizer
  round-trip/edge cases, causal mask, output shape, finite loss, no-future-influence,
  parameter-count range, deterministic init, CPU/MPS smoke, backend determinism).
- It is untrained: outputs are not meaningful yet. Training, checkpoints and
  temperature/top-k sampling arrive in Step 12; memory-conditioned evaluation in Step 13.

## Traceability

- Requirements: reversible byte tokenizer; decoder-only causal transformer; forward,
  causal loss; device selection; ~5–10M parameters; `TinyTransformerBackend`.
- Upholds invariants: 12 (measured — parameter count and correctness are tested), and the
  two-system boundary (memory has no torch dependency).
- Realized in stage 11; training/generation in Step 12; chat integration + evaluation in
  Step 13.

## Migration path

Swap the byte tokenizer or add a fused attention path behind the same interfaces if
justified by measurements. `TinyTransformerBackend` replaces `MockBackend` in chat at
Step 13 via the shared `GenerationBackend` protocol.
