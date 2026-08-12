# Model Card — Aira Core

> This card describes the *intended* model and its current state honestly. It will be
> updated with measured numbers as the model is actually built and trained.

## Current status (Step 12)

**The model can be trained locally, but only at smoke scale.** Implemented in PyTorch: a
reversible byte tokenizer (vocabulary 256), a decoder-only causal transformer
(**6,515,200 parameters** in the default config), a local training loop (AdamW, warmup +
cosine, clipping, validation, deterministic seeds, graceful interruption), versioned
checkpoints, and greedy/temperature/top-k generation. There is **no meaningfully trained
checkpoint**: `aira train` runs a few steps on a tiny built-in corpus purely to prove the
pipeline, and its output is not language. No dataset is downloaded. Whether retrieved
memory *helps* the model is measured in Step 13.

## Intended model

- **Type:** decoder-only causal transformer, implemented directly in PyTorch.
- **Tokenizer:** reversible byte-level, vocabulary 256 (Step 11).
- **Default size:** **6,515,200 parameters** (default `configs/aira_tiny.toml`).
- **Context length (default config):** 512 tokens.
- **Primary hardware target:** Apple M2, 8 GB unified memory; CPU-only supported.
- **Device selection:** MPS → CUDA → CPU.

Default shape is defined in `configs/aira_tiny.toml` and validated by `aira.config`.

## Intended use

- A research vehicle for studying whether **selective, secure, explainable memory**
  helps a compact model stay consistent over long horizons.
- Local, offline experimentation and evaluation.

## Out of scope / not claimed

- Not a general-purpose assistant; not competitive with frontier models.
- No claim of language quality, factual accuracy, or safety of generated text.
- Not production-ready; not audited; no hosted deployment.
- No automatic dataset downloads; training runs only on local corpora in smoke modes.

## Training data

None yet. When training is implemented (Step 12) it will use a small, local,
**synthetically generated** closed-domain corpus (plus an optional user-supplied
public-domain scaffold). The corpus design — grammar, held-out entity slots for
honest memory-conditioned evaluation, sizing and reproducibility — is specified in
[`docs/DATA_STRATEGY.md`](docs/DATA_STRATEGY.md) and [`adr/009`](adr/009-synthetic-closed-domain-data.md).
Data provenance, exact sizes and seeds will be recorded here once generated.

## Evaluation

Model behaviour will be measured with deterministic checks (tokenizer round-trip,
causal-mask correctness, output shapes, overfit-loss decrease, checkpoint
equivalence) and, for memory-conditioned tasks, against no-memory and full-history
baselines (Steps 11–13). No LLM judge is used as the sole evaluator.

## Limitations and risks

- A tiny model trained on a small local corpus will produce low-quality text; this is
  expected and not a defect.
- Memory correctness is a separate concern from generation quality and is evaluated
  independently (`aira.memory`, Step 10).

## Provenance of this card

Maintained alongside the code. Every quantitative claim added here must be backed by a
repeatable test or benchmark (project invariant 12).
