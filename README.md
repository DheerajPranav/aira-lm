<h1 align="center">Aira LM</h1>

<p align="center"><strong>Small model. Long memory. Gentle by design.</strong></p>

<p align="center"><em>Remember what matters. Forget responsibly.</em></p>

<p align="center">
  <img alt="stage" src="https://img.shields.io/badge/stage-09_fade_and_governance-111318">
  <img alt="status" src="https://img.shields.io/badge/status-in_active_development-75A478">
  <img alt="runtime" src="https://img.shields.io/badge/local--first-offline-C8C5BC">
  <img alt="python" src="https://img.shields.io/badge/python-3.12-111318">
  <img alt="license" src="https://img.shields.io/badge/license-not_yet_chosen-A76E78">
</p>

---

> *Some things are worth keeping for a long time. The rest deserves to be let go of
> gently. Aira is an attempt to teach a small machine that difference — to hold what
> matters without carrying everything forever.*

Aira LM is a **local-first, memory-native small language model**. It is a research
project asking one question honestly:

> **Can a compact language model stay consistent over a long horizon through secure,
> selective, explainable remembering — and responsible forgetting?**

Not by growing larger. By remembering *well*: keeping the few things that matter,
proving where each memory came from, refusing secrets, and forgetting completely
when asked.

## Where this project is right now

**This repository is at Stage 06 of 15.** In place so far: the control plane; the
**project foundation** (Python 3.12 package, config, determinism/device utilities, an
`aira` CLI); the **typed memory domain** (immutable validated records, deterministic
hashing, a lifecycle state machine with content-free tombstones); **Aira Guard**, the
offline pre-persistence privacy gate that detects and redacts secrets without ever
emitting a raw value; **Aira Vault & Trail** — owner-scoped, parameterized SQLite
persistence with single-transaction memory-plus-audit writes, a content-free audit
trail, and guard-screened import/export; **Capture** — the deterministic write path
(extract → guard → evaluate → supersede on correction, with a policy trace); and **Aira
Recall** — owner-scoped, lifecycle-aware keyword retrieval (SQLite FTS5 with a
deterministic BM25 fallback) whose index holds only active content and re-checks owner
and status on every hit, so forgotten, superseded, expired, deleted and cross-owner
memories can never surface; and **Ranking & Context** — deterministic score fusion
(eight configurable signals with full breakdowns), canonical/near-identical dedup, and a
delimited **untrusted-memory** block held within an exact byte-token budget, so retrieved
memory is always quoted data, never instructions, and never overflows the context; and
**Chat Integration** — the full pipeline wired to a deterministic mock backend
(guard→decide→mutate→retrieve→rank→compose→generate), with correlation ids, latency
metadata, and isolated failures that degrade to a no-memory response, plus an `aira chat`
CLI; and **Aira Fade & Governance** — a manually-invokable decay/expiry/archival job
(type-specific, deterministic, and it *never* hard-deletes) plus explicit owner controls
(inspect, explain with audit trail, guard-screened correction, reinforcement only on
usefulness, forget, export, atomic guard-screened import, owner-scoped delete-all).
**The complete Aira Memory lifecycle now works end to end** — remember, recall, correct,
forget, decay/expire, block-unsafe, owner isolation — under passing test, lint and
type-check gates (306 tests). **The generation backend is a deterministic mock, not a
trained model**; there is no model, tokenizer or checkpoint yet. Nothing here claims to be
trained, fast, fluent, or production-ready. Every capability still ahead is a *design
commitment* that becomes real only when a repeatable test or benchmark proves it.

Try the memory lifecycle locally (mock backend, no model):

```bash
uv sync
printf 'my editor is vim\n/memories\nwhat is my editor?\n/exit\n' | uv run aira chat
```

That honesty is a rule of the project, not a disclaimer: *no security, quality, or
performance property is claimed without a test that demonstrates it.*

## Two systems, kept apart

Aira is built as two independent halves so the memory runtime can be fully tested
before any model is trained.

| System | What it is | Depends on |
|---|---|---|
| **Aira Core** | A compact decoder-only transformer written directly in PyTorch (≈5–10M params, M2-safe). | PyTorch |
| **Aira Memory** | A model-independent runtime for capturing, storing, retrieving, correcting, forgetting, auditing and evaluating memories. | A backend *protocol* — not a model |

The entire memory lifecycle runs against a deterministic `MockBackend`. **Memory
tests never require a trained checkpoint.**

## The named parts

Aira takes its name and temperament from elephants — quiet, deliberate, long of
memory.

- **Aira Core** — the language model
- **Aira Guard** — safety and privacy gate; blocks secrets before they can be stored
- **Aira Vault** — durable, owner-scoped, transactional storage
- **Aira Trail** — provenance and append-only audit
- **Aira Recall** — owner-scoped keyword retrieval
- **Aira Fade** — decay, expiry and archival, off the request path
- **Aira Bench** — golden and adversarial evaluation

## What Aira promises to prove

These are the hard invariants the build is organized around. Each maps to at least
one planned, deterministic, offline test (see `PROJECT_PLAN.md`):

1. **Owner isolation** — one person's memory is never returned to another.
2. **Deletion integrity** — forgotten, expired, superseded or deleted memories never
   resurface in retrieval or model context.
3. **Graceful degradation** — if memory fails, the model still answers.
4. **Provenance** — every stored memory records how it was learned.
5. **Selective admission** — nothing becomes memory without passing the write gate.
6. **No assistant→user fact promotion** — the model's own words don't become your facts.
7. **Secret non-persistence** — credentials never enter memory, logs, exports or audit.
8. **Untrusted retrieval** — retrieved memory is quoted *data*, never a system instruction.
9. **User control** — your correction, forgetting and deletion always win.
10. **Bounded context** — composed memory never exceeds its token budget.
11. **Transactional lifecycle** — state and its audit event commit or roll back together.
12. **Measured claims** — nothing is asserted without a repeatable test.

Four of these are **zero-tolerance**: cross-owner leakage, forgotten-memory leakage,
secret persistence, and context-budget violations must all read exactly **0** in the
benchmark suite.

## How it will be built

One verified stage at a time. A stage is finished only when its measurable gate
passes and `docs/BUILD_STATUS.md` records the evidence.

```text
00  Control tower              08  Chat integration + graceful degradation
01  Repository foundation      09  Aira Fade + governance
02  Memory schema + lifecycle  10  Aira Bench (zero-tolerance metrics)
03  Aira Guard (privacy)       11  Aira Core transformer
04  Aira Vault + Trail         12  Training, checkpoints, generation
05  Capture + evaluation       13  Memory-conditioned evaluation
06  Aira Recall (FTS5/BM25)    14  Release hardening
07  Ranking + context budget
```

Full plan, dependencies and gates: **[`PROJECT_PLAN.md`](PROJECT_PLAN.md)** ·
assumptions: **[`ASSUMPTIONS.md`](ASSUMPTIONS.md)** · risks:
**[`RISKS.md`](RISKS.md)** · decisions: **[`adr/`](adr/)**

## Design principles

- **Local-first.** No cloud model APIs, no hidden network calls, no automatic large
  downloads. It runs on one machine — an Apple M2 with 8 GB is the primary target,
  and CPU-only stays supported.
- **Deterministic before learned.** Transparent heuristics decide what to remember
  before any model is trusted to.
- **Keyword before vector.** Exact facts, names and versions first; embeddings are a
  deferred, justified migration — not a day-one dependency.
- **Small dependencies, standard library where practical.** No orchestration
  frameworks.

## Status, plainly

| Area | State |
|---|---|
| Architecture, invariants, threat model, evaluation plan | Documented |
| Stage 00 control plane (plan, risks, ADRs, gate) | Complete |
| Stage 01 foundation (package, config, CLI, gates) | Complete |
| Stage 02 memory domain (records, lifecycle, hashing) | Complete |
| Stage 03 Aira Guard (secret detection + redaction) | Complete |
| Stage 04 Aira Vault & Trail (SQLite storage + audit) | Complete |
| Stage 05 Capture (extraction, write-gate, superseding) | Complete |
| Stage 06 Aira Recall (FTS5/BM25 keyword retrieval) | Complete |
| Stage 07 Ranking & Context (fusion, dedup, budget) | Complete |
| Stage 08 Chat Integration (mock backend, degradation) | Complete |
| Stage 09 Aira Fade & Governance (decay + user controls) | Complete |
| Aira Bench — golden + adversarial evaluation (Stage 10) | Not started |
| Aira Core model (Stages 11–13) | Not started |
| Trained checkpoint / language quality | None claimed |
| License | **Not chosen** — all rights reserved until one is selected |
| Hosted production | Out of scope; a production-gap document is planned for Step 14 |

## Documentation

`docs/` holds the mission, requirements, invariants, architecture, threat model,
data classification, evaluation plan, failure modes, roadmap and branding. The
original design study that informed the approach is preserved in
`references/memory-system.html` and reviewed in `docs/SOURCE_REVIEW.md`.

---

<p align="center"><sub>Built quietly, one honest stage at a time.</sub></p>
