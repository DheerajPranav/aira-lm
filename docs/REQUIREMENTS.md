# Requirements

## Functional requirements

### Aira Memory

- Support explicit actions: `REMEMBER`, `UPDATE`, `IGNORE`, `RECALL`, `FORGET`.
- Classify memory by kind: episodic, semantic, procedural, preference, instruction.
- Classify lifetime: working, session, long-term, knowledge.
- Persist approved memories locally.
- Require an `owner_id` for every persistent operation.
- Support create, inspect, search, retrieve, update, supersede, archive, expire, forget, hard-delete, import, and export.
- Preserve provenance for active memories.
- Maintain an append-only audit event stream.
- Enforce configurable context budgets using the actual tokenizer.
- Offer a deterministic mock generation backend.
- Offer a backend interface for Aira Core.
- Degrade to a no-memory response when retrieval fails.

### Aira Core

- Reversible byte-level tokenizer.
- Decoder-only causal transformer implemented directly in PyTorch.
- Configurable model size with an initial 5–10 million parameter target.
- Forward pass, causal loss, generation, checkpoint save/load.
- Greedy, temperature and top-k generation.
- MPS, CUDA and CPU device selection.
- Local-text-file training and smoke tests.

## Security and privacy requirements

- Block common passwords, API keys, tokens, private keys, credential-bearing connection strings, and authentication cookies before persistence.
- Redact blocked values in all output.
- Treat retrieved memory as untrusted data.
- Never return one owner’s memory to another.
- Never return forgotten, expired, deleted, archived by default, or superseded memory in normal retrieval.
- Allow users to inspect, correct, export and delete their memories.
- Hard deletion must not preserve content in audit events.
- Do not make network calls from tests or runtime core.

## Reliability requirements

- Use transactions for multi-step writes.
- Support idempotency keys for write events.
- Detect duplicates.
- Roll back interrupted writes.
- Bound memory-retrieval time.
- Isolate memory exceptions from generation.
- Persist through process restart.
- Provide recoverable local migrations.

## Observability requirements

Collect structured local measurements for:

- candidate, accepted, rejected and blocked writes
- retrieval count, hit rate and latency
- correction rate
- stale and forgotten-memory leakage
- cross-owner leakage
- context token usage
- degraded requests
- database and policy errors

## Documentation requirements

Maintain:

- mission
- requirements
- invariants
- threat model
- data classification
- architecture
- failure modes
- evaluation plan
- ADRs
- build status
- model card
- roadmap
