# ADR: Local training, versioned checkpoints, and seeded generation

- Status: Accepted
- Date: 2026-08-12
- Last reviewed: 2026-08-12

## Context

Step 12 makes Aira Core trainable and able to generate, on a single small machine, with
reproducibility. It must not download datasets, must stay within the M2 budget, and must
keep training and generation deterministic where seeded. No large corpus, no distributed
training, no quality claim.

## Decision

1. **Local, byte-level dataset.** `ByteDataset` tokenizes a caller-supplied string (or the
   tiny built-in `TINY_CORPUS`) into byte ids and splits off a validation tail. Batches
   are contiguous next-byte windows (`x[:, 1:] == y[:, :-1]`), sampled deterministically
   from a `torch.Generator`. Nothing is fetched from the network.
2. **Standard training loop.** AdamW with linear warmup then cosine decay, gradient
   clipping, periodic validation and full seed control (`set_seed` + a seeded batch
   generator). It tracks loss, perplexity, elapsed time and best-effort peak RSS.
3. **Interruptible.** A `KeyboardInterrupt` saves a checkpoint (if a path was given) and
   returns partial results rather than losing the run.
4. **Versioned checkpoints.** A checkpoint bundles model weights, optional optimizer
   state, the step and the model config, tagged with a schema version; loading rejects an
   unknown version instead of mis-loading. The `ModelConfig` is passed to the trainer
   explicitly (not reflected off the live module), keeping the checkpoint metadata exact
   and the code strictly typed. Loading uses `weights_only=False` because the payload
   holds plain config dicts — acceptable for local, user-created checkpoints.
5. **Greedy + temperature + top-k generation.** Greedy (`temperature <= 0`) is fully
   deterministic; sampling is reproducible when seeded (a CPU generator drives
   `multinomial`, so results are device-independent).
6. **Smoke-scale defaults.** A `SMOKE_TRAIN_CONFIG` and `aira train` run a few steps on
   the tiny corpus to prove the pipeline (train → validate → save → generate) end to end;
   `aira train` clearly labels the output as not meaningful language.

## Alternatives considered

- Auto-downloading a real corpus. Rejected: violates the offline/no-download constraint;
  the synthetic-data strategy (ADR-009) supplies data locally instead.
- Reflecting the model config off the live `nn.Module` for checkpoints. Rejected: torch's
  `ModuleList` typing makes this un-typeable under strict mypy and is fragile; passing the
  config explicitly is cleaner.
- Device-side seeded sampling. Rejected for portability: a CPU generator for `multinomial`
  keeps seeded sampling identical across CPU and MPS.

## Consequences

- The full local training/generation pipeline is reproducible and tested (deterministic
  batch, one-step, overfit-loss-decrease, checkpoint round-trip/resume, greedy determinism,
  seeded sampling, CPU smoke). On the M2 the default 6.5M model trains a smoke run in
  seconds on MPS.
- Trained quality is out of scope: the tiny model on the tiny corpus produces gibberish;
  whether memory *helps* is measured separately in Step 13.

## Traceability

- Requirements: local dataset + split; fixed-length causal batches; AdamW/clip/warmup;
  periodic validation; deterministic seeds; checkpoint save/load/resume with schema
  version; greedy/temperature/top-k generation; graceful interruption; loss/perplexity/
  time/peak-memory tracking.
- Upholds invariant 12 (measured, reproducible) and the offline constraint.
- Realized in stage 12; consumed by memory-conditioned evaluation (Step 13).

## Migration path

Bump `CHECKPOINT_SCHEMA_VERSION` when the payload changes; add real (still local,
user-supplied) corpora behind `ByteDataset`; a scheduler or longer schedule can wrap the
same `Trainer` without changing its contract.
