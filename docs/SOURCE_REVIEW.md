# Source Review — Attached Memory-System Study

The attached HTML study is retained at:

`references/memory-system.html`

## What Aira adopts

- Memory as selective retention, not bulk storage
- Separate capture, storage, retrieval, evaluation, decay and governance concerns
- Typed memory and memory lifetimes
- A write gate before persistence
- Importance, confidence and provenance
- Hybrid-retrieval evolution
- Decay and archival off the request path
- Four hard invariants around isolation, deletion, degradation and provenance
- Observability, security and governance as cross-cutting planes
- A staged build order with tests and evaluation gates
- One orchestrator before specialized or multi-agent designs
- Architecture decisions before technology selection

## What Aira changes

- SQLite-first instead of PostgreSQL for the local reference implementation
- No hosted embedding or language-model APIs
- No Temporal, Redis, Docker or Kubernetes initially
- Deterministic heuristic evaluator before an LLM evaluator
- Secret detection beyond generic PII filtering
- Hard-delete audit events that omit deleted content
- Explicit untrusted-memory protections against stored prompt injection
- Separation of Aira Core and Aira Memory
- Zero-tolerance deterministic security metrics

## Deferred source ideas

- vector retrieval
- graph retrieval
- reflection and consolidation
- distributed services
- row-level security
- workflow engines
- observability exporters
- dedicated caches

These remain migration targets and must be justified by measured constraints.
