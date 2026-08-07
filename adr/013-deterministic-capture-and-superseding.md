# ADR: Deterministic capture with canonical-key superseding

- Status: Accepted
- Date: 2026-08-08
- Last reviewed: 2026-08-08

## Context

Step 05 decides *what* to remember from a raw turn, before any retrieval or model
exists. It must be transparent, testable and offline (no LLM, ADR-004), run Aira Guard
before anything is stored, never promote assistant statements to user facts (invariant
6), admit selectively (invariant 5), and correct facts by superseding rather than
duplicating.

## Decision

1. **Fixed pipeline order.** guard → assistant/do-not-remember policy → extraction →
   utility evaluation → conflict resolution. The guard runs first, so a blocked turn
   never reaches extraction or storage.
2. **Regex extraction into a canonical key.** Deterministic patterns recognize explicit
   remember/forget, ``my <attr> is <value>``, identity, project, instruction and
   ``I prefer <value>``. Structured attribute facts get a **subject-based** canonical
   key (``<kind>:<owner>:<attr>``) so a later restatement or correction of the same
   attribute collides on the key; free text and value-based preferences get
   content-based keys.
3. **Conflict resolution by key.** On a canonical-key collision with an existing active
   memory: identical content is a duplicate (ignored); different content supersedes the
   old memory (Step 04 links them). No collision means a new memory.
4. **Evidence tiers.** Explicit requests and corrections carry higher confidence than
   bare inferred statements; a confidence/importance threshold drops low-value and
   explicitly temporary text.
5. **Assistant non-promotion and override safety.** Assistant turns produce no user
   facts. Instruction-like/override content flagged by the guard is not promoted to a
   stored instruction.
6. **Plan then apply, with a policy trace.** Capture produces immutable operations
   (remember / supersede / forget / ignore) plus a trace; a separate apply step persists
   them. This keeps extraction and evaluation pure and independently testable.

## Alternatives considered

- LLM-based extraction/evaluation. Rejected by project constraints; also not repeatable.
- Content-hash keys for everything. Rejected: corrections change the value, so the hash
  changes and the old fact is never superseded — memory would accumulate contradictions.
- Store first, reconcile later. Rejected: violates selective admission and pollutes
  retrieval.

## Consequences

- The write path is deterministic and fully covered by scenario tests (remember,
  ignore, temporary, preference, project, correction→supersede, ambiguous correction,
  unsafe, assistant, duplicate, forget, provenance).
- Recall of the heuristics is limited by design; unrecognized phrasings simply are not
  stored rather than being stored wrongly. The pattern set can grow with tests.

## Traceability

- Upholds invariants: 4 (provenance recorded on every memory), 5 (selective admission),
  6 (no assistant→user promotion), 8 (override content not promoted), 9 (user
  correction/forget drive superseding and forgetting), 12 (deterministic, tested).
- Realized in stage 05; consumes Aira Guard (03) and Aira Vault (04); feeds retrieval
  (06) and chat (08).

## Migration path

A learned extractor/evaluator may later sit behind the same candidate/assessment
interface, but must preserve guard-first ordering, canonical-key superseding and the
policy trace.
