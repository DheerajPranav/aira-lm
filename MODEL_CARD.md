# Model Card — Aira Core

> This card describes the *intended* model and its current state honestly. It will be
> updated with measured numbers as the model is actually built and trained.

## Current status (Step 01)

**No model exists yet.** There is no tokenizer, no transformer, no checkpoint and no
training run. This card is a commitment to what will be built and how it will be
reported, not a description of a working system. PyTorch is not even installed by
default at this stage (it is deferred to Step 11).

## Intended model

- **Type:** decoder-only causal transformer, implemented directly in PyTorch.
- **Tokenizer:** reversible byte-level, vocabulary 256 (Step 11).
- **Default size target:** ~5–10 million parameters (exact count reported at Step 11).
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

None yet. When training is implemented (Step 12) it will use small, local text
corpora that the user supplies or that ship as tiny sample fixtures. Data provenance
and size will be recorded here.

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
