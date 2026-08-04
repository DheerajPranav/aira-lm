# Assumptions

> Stage 00 deliverable. Explicit assumptions the plan depends on. Each is testable
> or falsifiable; where an assumption has already been probed, the evidence is noted.
> Assumptions are not claims of production readiness.

## Environment

- **A1 — Single local operator.** The first release serves one trusted local user
  on one machine. Owner isolation is still enforced from version one so multi-user
  safety does not require a rewrite (ADR-007).
- **A2 — Apple M2, 8 GB unified memory is the primary target**, but CPU-only
  execution must remain fully supported. Configs stay tiny and M2-safe.
- **A3 — `uv` manages the toolchain.** Verified present: `uv 0.12.1`.
- **A4 — Python 3.12 is the target.** The system interpreter probed as **3.13.0**,
  so Step 01 must pin a 3.12 toolchain via `uv`. Building on 3.13 by accident is a
  risk, not an accepted default (see `RISKS.md` R1).
- **A5 — Offline runtime.** No cloud model APIs, no hidden network calls, no
  automatic large downloads in the Aira runtime or tests.

## Data & persistence

- **A6 — SQLite is sufficient for the local reference implementation** (ADR-002).
  Probed: `sqlite3` runtime 3.47.0.
- **A7 — SQLite FTS5 is available** on the target. Probed: a `CREATE VIRTUAL TABLE
  ... USING fts5` succeeds. Step 06 must still detect at runtime and retain a
  deterministic BM25 fallback (ADR-003).
- **A8 — Local file-system trust.** At-rest encryption and key management are out of
  scope for the first release and documented as a production gap, not implemented.
- **A9 — `runtime/` is disposable and git-ignored.** Databases, checkpoints and logs
  never enter version control.

## Memory system

- **A10 — Deterministic policy before learned policy** (ADR-004). Extraction and
  evaluation are transparent heuristics; an untrained tiny model must not decide
  what to remember.
- **A11 — Keyword retrieval before vector retrieval** (ADR-003). Exact facts, names
  and versions matter first; embeddings are a deferred migration target.
- **A12 — Retrieved memory is untrusted data**, always rendered as delimited quoted
  content and never promoted to system-level instructions (invariant 8).
- **A13 — The full memory lifecycle is testable with a deterministic `MockBackend`**
  and never requires a trained checkpoint (ADR-001).
- **A14 — Memory is personalization, not a prerequisite.** Any storage/retrieval
  failure degrades to a no-memory response (ADR-006, invariant 3).

## Aira Core

- **A15 — Direct PyTorch implementation.** No pretrained Hugging Face weights, no
  large downloads, no architectural-novelty claim.
- **A16 — Default configuration lands in the 5–10M parameter range** and trains only
  in smoke/overfit modes on a small local corpus. No language-quality claim is made.

## Evaluation & governance

- **A17 — Deterministic offline tests are the source of truth.** No LLM judge is the
  sole evaluator; zero-tolerance security metrics must be exactly 0.
- **A18 — Documentation reflects real status.** Nothing is claimed as implemented
  until a repeatable test or benchmark exists (invariant 12).

## Publishing (this session)

- **A19 — The repository may be published publicly** as `aira-lm` at the user's
  explicit request. The public README and GitHub Pages landing page describe the
  vision and architecture and state honestly that implementation is at Stage 00.
- **A20 — No license is selected.** Absent a `LICENSE` file, the work is
  all-rights-reserved by default; a license will be chosen only with user approval
  (`CLAUDE.md`, Step 14).
