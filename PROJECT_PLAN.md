# Aira LM — Project Plan (Control Tower)

> Stage 00 deliverable. This is the executable control plane for building Aira LM
> one verified stage at a time. It maps requirements to stages, stages to
> measurable completion gates, and every hard invariant to at least one planned
> test. No runtime code is implemented at this stage.

- Owner: Dheeraj Pranav
- Created: 2026-08-04 (UTC)
- Source study reviewed: `references/memory-system.html` — *"Designing a ChatGPT-Style Memory System"* (digested in `docs/SOURCE_REVIEW.md`)
- Governing documents: `CLAUDE.md`, `docs/MISSION.md`, `docs/REQUIREMENTS.md`, `docs/INVARIANTS.md`, `docs/ARCHITECTURE.md`, `docs/THREAT_MODEL.md`, `docs/DATA_CLASSIFICATION.md`, `docs/EVALUATION_PLAN.md`

## 1. Build principle

One numbered prompt per session. A stage is complete only when its **completion
gate** is met with recorded evidence and `docs/BUILD_STATUS.md` is updated. The
memory runtime must be fully testable with a deterministic `MockBackend` and must
never require a trained checkpoint.

Two independent systems, kept apart at all times:

- **Aira Core** — tokenizer, transformer, training, checkpoints, generation.
- **Aira Memory** — policy, storage, retrieval, governance, audit, decay, evaluation.

## 2. Stage graph (dependencies)

```text
00 ─▶ 01 ─▶ 02 ─▶ 03 ─▶ 04 ─▶ 05 ─▶ 06 ─▶ 07 ─▶ 08 ─▶ 09 ─▶ 10 ─┐
                     └───────────┘                                │
        (03 also feeds 04)                                        ▼
                                              11 ─▶ 12 ─▶ 13 ◀────┘
                                                          │
                                                          ▼
                                                          14
```

- Steps 02–10 build the memory runtime end to end with the mock backend.
- Steps 11–12 build Aira Core independently (no memory coupling).
- Step 13 integrates Core into chat and measures memory-conditioned behaviour.
- Step 14 hardens and documents the local research release.

## 3. Stage table — deliverables, dependencies, completion gates

| Step | Name | Depends on | Primary deliverables | Measurable completion gate |
|---:|---|---|---|---|
| 00 | Control Tower | — | `PROJECT_PLAN.md`, `ASSUMPTIONS.md`, `RISKS.md`, improved ADR-001..007, invariant→test matrix, repo tree, open decisions | `scripts/verify_step00.sh` exits 0: all required docs exist, referenced paths resolve, 12 invariants each mapped, every stage has a gate; **no runtime code present** |
| 01 | Repository Foundation | 00 | `pyproject.toml` (src layout, Py 3.12), pytest/ruff/mypy config, package namespaces (core, memory, chat, evaluation, cli), config loader for `configs/aira_tiny.toml`, seed + device utils, `aira` CLI (`--help`, `doctor`, `--version`), no-network guard, `README.md`, `MODEL_CARD.md`, `CONTRIBUTING.md` | `uv sync` ok; `aira --help/doctor/--version` exit 0; config-validation + device-mock tests pass; `pytest`, `ruff check`, `ruff format --check`, `mypy src` all green |
| 02 | Memory Schema & Lifecycle | 01 | Enums (action/kind/lifetime/status/sensitivity/consent/retention), validated domain records, lifecycle state machine, canonical keys + content hashes, decision/result records | Every allowed transition passes; every forbidden transition rejected; hard-delete tombstone holds **no content**; hashing deterministic; gates green |
| 03 | Aira Guard | 02 | Replaceable guard interface; detectors for API keys, bearer tokens, private-key blocks, password assignments, credential URLs, cookies, PAN-like patterns; "do-not-remember"/policy-override detection; redaction; safe structured events | One test per secret category passes; **no raw secret** in output, exceptions, logs, or serialized events (asserted); benign look-alikes not blocked; oversized input handled; gates green |
| 04 | Aira Vault & Trail | 02, 03 | SQLite connection + migrations; memory + audit tables; owner-scoped parameterized repository; single-transaction state+event writes; create/get/list/update/supersede/archive/expire/forget/hard-delete; import/export scaffolding; backup/integrity command | Restart persistence; owner A cannot get/list/update/delete/export owner B; injected-interruption rollback; duplicate idempotency key; forbidden-state default filters; hard-delete audit holds no content; audit per mutation; gates green |
| 05 | Capture & Evaluation | 02–04 | Deterministic candidate extraction (remember/preference/identity/project/correction/update/forget/do-not-remember); guard-before-eval; deterministic utility evaluator (importance + confidence + reasons); conflict resolution by superseding; policy trace | All admission scenarios pass incl. assistant-statement non-promotion, correction→supersede, unsafe-candidate block, duplicate detection, provenance correctness; gates green |
| 06 | Aira Recall | 04, 05 | FTS5 availability recorded; retriever interface; FTS5 retrieval + documented BM25 fallback; owner + lifecycle filtering before ranking; kind/lifetime/tag/project filters; index maintenance; bounds | Exact-string retrieval; owner isolation; forgotten/superseded/expired excluded; malformed/empty query safe; index updates after correction; hard-delete removes searchable content; deterministic; latency benchmark recorded; gates green |
| 07 | Ranking & Context | 06 | Deterministic score fusion (lexical, importance, confidence, recency, reinforcement, project, kind, decay penalty); dedup; delimited untrusted-memory context format; token-budget enforcement via real tokenizer interface | Score-component + ordering + tie determinism tests; inactive-state defense-in-depth; injection-like memory stays quoted data; exact byte budget boundary + multibyte Unicode; **no context overflow**; gates green |
| 08 | Chat Integration | 05–07 | Generation backend protocol; deterministic `MockBackend`; chat pipeline (guard→decide→mutate→retrieve→compose→generate); correlation IDs + latency; no-memory fallback; CLI chat + `/memories`, `/memory`, `/forget`, `/debug`, `/stats`, `/reset`, `/exit` | End-to-end remember/recall/correct/forget; **every injected memory failure still returns a response** (timeout, DB-unavailable, malformed); owner isolation through chat; debug on/off; CLI smoke; gates green |
| 09 | Aira Fade & Governance | 08 | Manually-invokable decay job (type-specific half-lives); reinforcement only on explicit usefulness; archive-below-threshold; expiry; user ops: inspect-all/explain-source/correct/archive/forget/hard-delete/export/delete-all; validated atomic import | Fixed-clock decay + kind-specific rates; retrieval-without-reinforcement vs explicit reinforcement; archive threshold; expiry; **no automatic hard-delete**; export excludes forbidden states; malformed/unsafe import rolls back; delete-all owner-isolated; gates green |
| 10 | Aira Bench | 08, 09 | Versioned benchmark JSONL schema; golden + adversarial scenarios; metrics (precision, recall, recall@k, MRR, correction success, stale/forgotten/cross-owner leakage, secret persistence, budget violations, degraded success, latency); JSON + Markdown reports; regression thresholds | Schema + metric unit tests; all golden + adversarial cases present; **cross-owner leakage = 0, forgotten leakage = 0, secret persistence = 0, budget violations = 0**; report reproducible; gates green |
| 11 | Aira Core | 10 | Reversible UTF-8 byte tokenizer (vocab 256); token + positional embeddings; pre-norm causal blocks; multi-head causal self-attention; GELU FFN; tied embeddings; causal LM loss; exact param count; `TinyTransformerBackend` adapter | Tokenizer round-trip (English/Unicode/punct/empty/invalid bytes); causal mask blocks future tokens; output shape + finite loss; **param count in 5–10M**; MPS/CPU smoke; deterministic init; gates green |
| 12 | Training & Generation | 11 | Local text dataset + split; fixed-length causal batches; AdamW + clip + warmup; periodic validation; checkpoint save/load/resume (versioned); greedy/temperature/top-k generation; tiny sample corpus + smoke config | Dataset boundaries; deterministic batch; one-step train; **loss decreases on overfit fixture**; checkpoint round-trip + resume; deterministic greedy; CPU smoke completes within small-machine scope; gates green |
| 13 | Memory-Conditioned Eval | 10–12 | `TinyTransformerBackend`→chat without coupling memory to PyTorch; controlled tasks; no-memory / memory / full-history baselines; metrics (factual adherence, correction adherence, forgotten non-disclosure, context cost, latency); versioned run records | Reproducible experiment answering *does memory help this checkpoint*; correction + forgetting scenarios; context-budget respected; results reproducible; **negative/inconclusive results reported honestly**; gates green |
| 14 | Release Hardening | 00–13 | Full suite run; migration + backup/restore verification; dependency + license review instructions; packaging tests; README/MODEL_CARD/SECURITY/PRIVACY/CONTRIBUTING; release checklist + reproducibility manifest; production-gap document | Fresh-env install; all zero-tolerance metrics remain 0; backup/restore; migration; package build/install; offline runtime test; documented measurements; **no license invented without approval** |

## 4. Requirements → stage traceability (summary)

| Requirement area (REQUIREMENTS.md) | Stages |
|---|---|
| Memory actions REMEMBER/UPDATE/IGNORE/RECALL/FORGET | 05, 08, 09 |
| Kind + lifetime classification | 02, 05 |
| Local persistence, owner_id required, full CRUD lifecycle | 02, 04, 09 |
| Provenance + append-only audit | 04, 05, 09 |
| Context budget via real tokenizer | 07, 11 |
| Mock backend + Core backend interface | 08, 11, 13 |
| Degrade to no-memory response | 06, 08 |
| Secret blocking + redaction | 03, 04 |
| Untrusted retrieval, owner non-leakage, forbidden-state exclusion | 04, 06, 07, 10 |
| Reliability (transactions, idempotency, rollback, bounds, restart) | 04, 06, 08 |
| Observability metrics | 08, 09, 10 |
| Aira Core (tokenizer, transformer, generation, checkpoints, devices) | 11, 12 |
| Documentation set | 00, 01, 14 |

## 5. Hard-invariant → planned-test traceability

Every invariant in `docs/INVARIANTS.md` maps to at least one planned, deterministic,
offline test. Zero-tolerance items must equal **0** in the Step 10 suite.

| # | Invariant | Primary enforcing stages | Planned tests / gate (zero-tolerance in **bold**) |
|---:|---|---|---|
| 1 | Owner isolation | 04, 06, 08, 10 | Owner A cannot get/list/update/delete/export owner B (04); retrieval owner scope (06); chat owner isolation (08); **cross-owner leakage = 0 (10)** |
| 2 | Deletion integrity | 04, 06, 07, 10 | Default filters exclude forgotten/expired/superseded (04); forgotten exact-match excluded (06); inactive-state defense-in-depth (07); **forgotten leakage = 0 (10)** |
| 3 | Graceful degradation | 06, 08, 10 | Retrieval timeout / DB-unavailable / malformed-memory fallbacks each return a response (08); bounded retrieval (06); degraded-response success (10) |
| 4 | Provenance | 02, 04, 05, 09 | Required provenance on records (02); provenance stored + returned (04); source correctness (05); explain-source (09) |
| 5 | Selective admission | 03, 05 | Guard runs before evaluation (03); write-gate accepts/rejects with reasons; low-value dropped (05) |
| 6 | No assistant→user fact promotion | 05 | Assistant statement is not persisted as a user fact (05) |
| 7 | Secret non-persistence | 03, 04, 10 | Per-category detection; no raw secret in output/logs/exceptions/events (03); audit holds no secret content (04); **secret persistence = 0 (10)** |
| 8 | Untrusted retrieval | 07, 10 | Memory rendered as delimited quoted data; injection text never becomes system policy (07); injection benchmark (10) |
| 9 | User control | 08, 09 | `/forget` via chat (08); correct / forget / hard-delete / delete-all override retention (09) |
| 10 | Bounded context | 07, 10 | Exact byte-token budget boundary + multibyte Unicode; no overflow (07); **budget violations = 0 (10)** |
| 11 | Transactional lifecycle | 02, 04 | Legal/illegal transition tests (02); state + audit event commit or roll back together; injected-interruption rollback (04) |
| 12 | Measured claims | 10, 14, all | Every stage gate requires recorded evidence; Bench produces machine-readable metrics (10); release re-runs full suite (14) |

## 6. Proposed final repository tree

Target end-state after Step 14. Directories marked *(exists)* are present now; the
rest are created by the stage noted in parentheses. This is a plan, not current state.

```text
aira-lm/
├── CLAUDE.md                       (exists) project instructions
├── README.md                       (00/01) public overview + honest status
├── MODEL_CARD.md                   (01)  model scope, limits, no-quality claims
├── SECURITY.md                     (14)  reporting + threat surface
├── PRIVACY.md                      (14)  data handling + user controls
├── CONTRIBUTING.md                 (01)  contribution notes
├── PROJECT_PLAN.md                 (00)  this file
├── ASSUMPTIONS.md                  (00)
├── RISKS.md                        (00)
├── pyproject.toml                  (01)  Py 3.12, src layout, tool config
├── Makefile                        (exists)
├── configs/
│   └── aira_tiny.toml              (exists)
├── docs/                           (exists) mission, requirements, invariants,
│   │                                        architecture, threat model, data
│   │                                        classification, evaluation, failure
│   │                                        modes, roadmap, branding, source review,
│   │                                        build status, model card, adr index
│   ├── DATA_STRATEGY.md            (01)  synthetic corpus design for Steps 11–13
│   ├── index.html                  (00)  GitHub Pages landing page
│   └── PRODUCTION_GAP.md            (14)
├── adr/                            (exists) 001..009 + new records per stage
├── prompts/                        (exists) 00..14 stage prompts
├── references/
│   └── memory-system.html          (exists) source study
├── scripts/                        (exists) env/list/verify helpers
│   ├── verify_step00.sh            (00)  control-tower checker
│   └── verify.sh                   (exists) post-01 quality gates
├── src/aira/
│   ├── __init__.py                 (01)
│   ├── config.py                   (01)  load/validate aira_tiny.toml
│   ├── seed.py  device.py          (01)  determinism + MPS/CUDA/CPU
│   ├── cli/                        (01→) aira CLI (doctor, chat, memory ops)
│   ├── core/                       (11–12) tokenizer, model, train, generate, checkpoint
│   ├── memory/
│   │   ├── domain/                 (02)  enums, records, lifecycle
│   │   ├── guard/                  (03)  detectors, redaction, events
│   │   ├── vault/                  (04)  sqlite, migrations, repository
│   │   ├── trail/                  (04)  audit events
│   │   ├── capture/                (05)  extraction + evaluation + conflict
│   │   ├── recall/                 (06)  retriever (FTS5/BM25), filters
│   │   ├── ranking/                (07)  score fusion, dedup, context builder
│   │   ├── fade/                   (09)  decay, expiry, archival, governance
│   │   └── backends/               (08,11) protocol, MockBackend, TinyTransformerBackend
│   ├── chat/                       (08)  chat engine pipeline
│   └── evaluation/                 (10,13) Aira Bench + memory-conditioned eval
├── tests/                          (02→) deterministic offline tests per module
├── benchmarks/                     (10)  golden + adversarial JSONL, reports
└── runtime/                        (exists, git-ignored) aira.db, checkpoints, logs
```

## 7. Open decisions (unresolved at Step 00)

Tracked here and in `RISKS.md`; each must be resolved before the stage that needs it.

| Decision | Status | Resolve by | Notes |
|---|---|---|---|
| License | **Open — do not invent** | Before public release / Step 14 | `CLAUDE.md` forbids inventing one. Repo may be published without a license file until the user chooses (all-rights-reserved by default). |
| Exact dependency versions | Open | Step 01 | Pin `torch`, `pytest`, `ruff`, `mypy`, `tomli`/stdlib `tomllib`, etc. in `pyproject.toml` with a lockfile. Keep minimal + documented. |
| SQLite FTS5 availability | **Resolved (probe) / re-verify at runtime** | Step 06 | System Python `sqlite3` reports FTS5 **available** (SQLite 3.47.0) on this M2. Step 06 must still detect at runtime and keep the BM25 fallback. |
| Encryption scope | Open | Step 14 | First release: local file-system trust only; no at-rest encryption or key management claimed. Documented as a production gap, not implemented. |
| Python interpreter | **Risk** | Step 01 | System `python3` is 3.13.0 but the project targets 3.12. `uv` must pin a 3.12 toolchain; do not silently build on 3.13. See `RISKS.md`. |
| Model card + SECURITY/PRIVACY docs | Planned | 01 / 14 | `MODEL_CARD.md` (Step 01) and `SECURITY.md`/`PRIVACY.md` (Step 14) are required by REQUIREMENTS but not yet created. |

## 8. Verification gate for this stage (Step 00)

Run `scripts/verify_step00.sh`. It passes only when:

1. Every required governing document exists.
2. Every path referenced by the docs resolves.
3. All 12 hard invariants appear in the traceability matrix above.
4. Every stage 00–14 has a completion gate in the stage table.
5. No Python runtime/package code has been introduced (control-tower discipline).

The plan is "done" when the repository has an executable written plan, requirement→test
traceability, and no runtime implementation has started.
