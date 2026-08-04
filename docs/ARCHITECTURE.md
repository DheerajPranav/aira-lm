# Architecture

## System boundary

```text
                         AIRA LM
                            |
                +-----------+-----------+
                |                       |
           AIRA CORE               AIRA MEMORY
        Small Transformer        Memory Runtime
                |                       |
                |              +--------+--------+
                |              |                 |
                |          WRITE PATH        READ PATH
                |              |                 |
                |          Aira Guard         Policy Filter
                |              |                 |
                |           Extractor          Retriever
                |              |                 |
                |           Evaluator          Ranker
                |              |                 |
                |       Conflict Resolver    Context Builder
                |              |                 |
                |          Aira Vault ----------+
                |              |
                +-------- Response Backend
                               |
                         Generated Answer
```

Cross-cutting components:

- **Aira Trail:** provenance and audit
- **Aira Guard:** safety, privacy and admission policy
- **Aira Fade:** decay, expiry and archival
- **Aira Bench:** golden and adversarial evaluation

## Write path

```text
message
→ owner resolution
→ safety and privacy screening
→ candidate extraction
→ utility evaluation
→ contradiction/update resolution
→ consent and retention policy
→ transactional storage
→ append-only audit event
```

## Read path

```text
query
→ owner and policy filter
→ active-state filter
→ keyword/BM25 retrieval
→ deterministic ranking
→ deduplication
→ context-budget enforcement
→ generation backend
```

## Memory classification

Kind and lifetime are independent.

### Kind

- episodic
- semantic
- procedural
- preference
- instruction

### Lifetime

- working
- session
- long-term
- knowledge

Working memory is the live context and is not persistent by default. Knowledge memory contains external reference material and remains logically separate from personal memory.

## Initial local topology

- Python package with a `src` layout
- SQLite for durable state
- SQLite FTS5 or a local BM25 implementation for keyword retrieval
- in-process services with explicit interfaces
- structured local logs and metrics
- scheduled work represented by manually invokable jobs
- deterministic mock backend for end-to-end memory tests
- PyTorch for Aira Core

## Evolution path

Interfaces may later support:

- PostgreSQL and row-level security
- pgvector
- Redis session cache
- workflow queues
- OpenTelemetry
- cloud key management
- vector and graph retrieval

These are migration targets, not first-release dependencies.
