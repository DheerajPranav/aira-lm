# ADR: Synthetic closed-domain data with held-out slots for memory-conditioned evaluation

- Status: Accepted
- Date: 2026-08-05
- Last reviewed: 2026-08-05

## Context

Aira Core is a 5–10M-parameter byte-level model (vocabulary 256) that will never be
fluent, by design. Its only purpose is to answer one research question: does a
retrieved memory placed in the context change generation the way it should, beyond
what the weights alone produce? Training and evaluating for that does not require a
large or realistic corpus, and a real corpus would conflict with three project
constraints — offline/no-download, unresolved licensing, and unknown ground truth.

A concern was raised that "even a tiny model needs *some* data." It does; the question
is where that data comes from.

## Decision

Generate the training and evaluation data with a **seeded, closed-domain template
generator** rather than collecting a real corpus. The generator's output *is* the
dataset.

1. A bounded grammar over a fixed pool of invented entities emits short declarative
   sentences whose statement kinds map onto the memory taxonomy (preference, semantic,
   project, instruction, episodic).
2. Evaluation uses `(memory, prompt, expected)` triples with short, deterministically
   checkable answers (no LLM judge), driving the no-memory / Aira-Memory / full-history
   baselines.
3. The entity pool is split into **train** and **held-out** partitions. The primary
   evaluation set uses only held-out entities, so a correct answer is impossible from
   the weights and must come from the retrieved memory in context. This defeats the
   memorization confound and is the site of Step 13's ranking-signal ablations.
4. Everything is byte-for-byte reproducible from an explicit seed; sizes are chosen
   empirically at Step 12 against measured loss and peak memory.

Full design: `docs/DATA_STRATEGY.md`.

## Alternatives considered

- **Scrape / download a real corpus.** Rejected: violates offline/no-download,
  introduces licensing and provenance problems, gives no ground truth, and a byte-level
  tiny model cannot fit an open-vocabulary long tail well enough to test the contrast.
- **Manually hand-author a fixed dataset.** Rejected: not scalable, hard to keep the
  train/held-out split clean, and not reproducibly regenerable.
- **Use a public-domain text as the primary corpus.** Rejected as primary because the
  facts under test do not occur in generic text; retained only as an optional,
  user-supplied, guard-scanned fluency scaffold.

## Consequences

- The corpus is offline, license-clean, reproducible, and carries the exact facts we
  test (or deliberately withholds them).
- Results are honest but narrow: they say whether memory helps *this* tiny checkpoint
  on *this* controlled domain, and must not be generalized to larger models or real
  corpora. Step 13 must report negative or inconclusive results plainly.
- Some engineering cost: the grammar and the train/held-out split must be designed
  carefully to avoid distribution leakage.

## Traceability

- Upholds invariants: 12 (measured, reproducible claims), 7 (guard-scanned data holds
  no secrets), 1 (evaluation triples carry `owner_id`, enabling cross-owner-leakage checks).
- Requirements: local-only data, deterministic offline evaluation, no automatic downloads.
- Realized in stages: 11 (byte tokenizer makes the closed vocabulary free), 12
  (generator + smoke fixture + training), 13 (held-out memory-conditioned evaluation
  and baselines).

## Migration path

Revisit if the research question changes or if a larger model justifies a real corpus.
Preserve the generator interface and the JSONL task-set schema so Aira Bench (Step 10)
can consume the same evaluation format. Any real-text scaffold must remain
user-supplied, offline, guard-scanned and recorded in `MODEL_CARD.md`.
