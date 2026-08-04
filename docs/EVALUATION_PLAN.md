# Evaluation Plan

## Memory-system metrics

- precision
- recall
- recall@k
- mean reciprocal rank
- correction success rate
- stale-memory retrieval rate
- forgotten-memory leakage rate
- cross-owner leakage rate
- secret-persistence rate
- context-budget violation rate
- degraded-response success rate
- retrieval latency
- average context tokens
- memory utilization

## Required zero-tolerance metrics

These must equal zero in the deterministic test suite:

- cross-owner leakage
- forgotten-memory leakage
- secret persistence
- context-budget violations

## Baselines

1. No memory
2. Aira Memory
3. Full-history context where practical

## Golden scenarios

- explicit preference recall
- delayed fact recall
- correction and superseding
- irrelevant distractors
- explicit forgetting
- expiry
- project relevance
- conflicting instructions
- context-budget pressure
- messages that should be ignored

## Adversarial scenarios

- owner A asks for owner B’s memories
- forgotten memory exactly matches the query
- API key embedded in ordinary prose
- memory contains prompt-injection language
- duplicate write event
- malformed import
- deletion followed by export
- retrieval database unavailable
- high-volume irrelevant memories
- stale preference competing with a recent correction

## Aira Core evaluation

- tokenizer round-trip
- causal mask correctness
- output shapes
- deterministic greedy generation
- checkpoint equivalence
- validation loss
- perplexity
- CPU/MPS smoke execution
- peak memory use for the default configuration

## Research evaluation

Compare memory-conditioned generation against no-memory generation using:

- factual consistency with stored user facts
- correction adherence
- forgotten-fact non-disclosure
- context token cost
- response latency

Do not use an LLM judge as the only evaluator. Prefer deterministic checks where expected facts are known.
