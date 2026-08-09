# ADR: Chat pipeline, model-agnostic backend, and graceful degradation

- Status: Accepted
- Date: 2026-08-09
- Last reviewed: 2026-08-09

## Context

Step 08 connects the memory runtime to a generator and proves the full lifecycle works
end to end with a deterministic backend. The pipeline must keep memory a personalization
layer rather than a prerequisite (invariant 3): any failure in the write or read path
must still yield a response. Retrieved memory crosses into the backend as untrusted data
(invariant 8) within the token budget (invariant 10), and user-visible answers must not
leak internal ids.

## Decision

1. **Fixed pipeline, dependency-injected.** One turn runs guard + decide + mutate (via
   `CaptureService`), then retrieve → rank → compose → generate. The engine's
   collaborators (capture, retriever, ranker, backend, tokenizer) are injected, so each
   can be tested or replaced in isolation; `create_chat_engine` wires the defaults.
2. **Model-agnostic backend interface.** A `GenerationBackend` receives a
   `GenerationRequest` carrying the delimited untrusted `memory_context` **and** the plain
   `memory_facts` (ranked contents). A trivial backend can answer from the facts; Aira
   Core's `TinyTransformerBackend` (Step 13) can build a byte prompt from the same
   request. `MockBackend` is deterministic and explicitly non-intelligent.
3. **Isolated failures, no-memory fallback.** The write path, read path and backend call
   are each wrapped so an exception is caught, logged without raw content, and the turn
   still returns a `ChatResponse` with `degraded=True` and an empty memory context. A
   slow/failing retriever, an unavailable database, or a malformed memory all degrade to
   a no-memory response rather than an error.
4. **Observability always; debug on demand.** Every response carries a correlation id and
   a latency measurement. Internal ids, capture reasons and the memory block are exposed
   only when the caller enables debug mode; normal answers never show ids.
5. **Testable CLI session.** The slash-command REPL (`/memories`, `/memory`, `/forget`,
   `/debug`, `/stats`, `/reset`, `/exit`) is a pure function over an input iterable and an
   output stream, so it is covered by deterministic tests; `aira chat` wires real streams.

## Alternatives considered

- Fail the whole request when memory errors. Rejected: violates invariant 3 and the
  availability goal.
- A prompt-only backend interface (like a hosted chat API). Rejected for the first
  release: passing structured facts keeps the mock trivial and keeps memory framed as
  data; a prompt-building backend still fits behind the same protocol.
- A real preemptive retrieval timeout via threads. Deferred: the SQLite connection is
  single-threaded, so hard preemption needs a thread-safe backend. The engine bounds work
  by catching failures (including a raised `TimeoutError`) and degrading; a hard timeout
  is a documented future enhancement.

## Consequences

- The complete memory lifecycle (remember, recall, correct, forget, block-unsafe, owner
  isolation) is demonstrable through `aira chat` and covered end to end, and every
  injected memory failure still returns a response — all tested.
- The mock backend makes no quality claim; language quality is out of scope until Aira
  Core and its evaluation (Steps 11–13).

## Traceability

- Upholds invariants: 3 (graceful degradation), 8 (untrusted memory to the backend), 10
  (bounded context), 6 (assistant non-promotion, enforced upstream by capture), 1 (owner
  isolation through chat).
- Realized in stage 08; the backend interface is the seam Aira Core plugs into at Step 13.

## Migration path

Replace `MockBackend` with `TinyTransformerBackend` (same `GenerationBackend` protocol)
at Step 13. If a hard retrieval timeout is required, introduce a thread-safe read path and
wrap retrieval in a bounded executor, preserving the degrade-to-no-memory contract.
