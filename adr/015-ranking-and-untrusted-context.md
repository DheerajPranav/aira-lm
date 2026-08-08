# ADR: Deterministic score fusion and a delimited, budgeted untrusted-memory block

- Status: Accepted
- Date: 2026-08-08
- Last reviewed: 2026-08-08

## Context

Step 07 turns retrieval results into the memory block a backend will see. It must fuse
several signals into one ranking, be reproducible (invariant 12), keep retrieved memory
as untrusted *data* rather than instructions (invariant 8), and never exceed the context
token budget (invariant 10). The full tokenizer is Aira Core (Step 11), but budgeting
needs an exact token count now.

## Decision

1. **Configurable, fully-broken-out score fusion.** The final score is a weighted sum of
   eight normalized [0, 1] components — lexical relevance, importance, confidence,
   recency, reinforcement, project relevance, kind priority — minus a decay penalty.
   Weights come from the `[retrieval]` config; decay half-lives from `[decay]`. Every
   result carries the full weighted breakdown, and ordering is deterministic (score
   desc, then oldest first, then id).
2. **Active-only, defense in depth.** Ranking drops any non-active memory even though
   retrieval already excludes them (invariant 2).
3. **Deterministic deduplication.** Walking the ranked list, the first memory per
   canonical key is kept, then the first per content hash — so the survivor is always the
   highest-ranked representative, and near-identical duplicates are removed.
4. **Delimited untrusted-memory block.** Memories are wrapped in explicit
   `<untrusted_memory>` … `</untrusted_memory>` delimiters with a preamble that marks
   them as user-provided data, never instructions. Delimiter strings appearing inside a
   memory are sanitized so a memory cannot break out of the block.
5. **Exact byte-token budget.** A minimal `ByteTokenizer` counts UTF-8 bytes. The
   composer adds memories greedily in ranked order, re-measuring the whole block
   (including wrapper) after each, and only keeps a memory if the block still fits. It
   also enforces top-k. The result never exceeds the budget, for any input including
   multibyte text, and records why each memory was included or excluded.
6. **Debug ids off by default.** Internal memory ids appear only in debug mode; normal
   output shows sequential `[n]` labels.

## Alternatives considered

- Merge retrieved instructions into the system prompt for "better obedience". Rejected
  outright: violates invariant 8 and the threat model's stored-injection control.
- Truncate the final string to the budget. Rejected: could split a memory or a multibyte
  character; per-item measurement keeps the block valid and whole.
- A learned reranker. Out of scope (Step 07 excludes it); the deterministic fusion is the
  baseline and reference.

## Consequences

- Ranking and context are reproducible and fully explainable, and the budget can never be
  exceeded — both are covered by tests (exact boundary, multibyte, never-overflow,
  injection-stays-quoted, delimiter-breakout-sanitized).
- The byte tokenizer is a stand-in; when Aira Core's tokenizer lands it implements the
  same `Tokenizer` protocol, so budgeting can switch without changing the composer.

## Traceability

- Upholds invariants: 8 (untrusted, delimited memory), 10 (bounded context), 2
  (active-only defense in depth), 12 (deterministic, explainable).
- Realized in stage 07; consumed by chat integration (Step 08).

## Migration path

Swap `ByteTokenizer` for Aira Core's tokenizer (same protocol) when measuring in model
tokens is preferred. A learned reranker may replace the fusion behind the ranker
interface, preserving determinism guarantees where required.
