# Build Status

## Current stage

- Stage: 08 — Chat Integration
- Status: Complete (full memory lifecycle via mock backend; graceful degradation; no PyTorch)
- Last verified commit: Step 08 commit of `aira-lm` (2026-08-09)
- Last updated: 2026-08-09 by Claude Code

## Stage checklist

| Step | Name | Status | Evidence |
|---:|---|---|---|
| 00 | Control tower and audit | Complete | `PROJECT_PLAN.md`, `ASSUMPTIONS.md`, `RISKS.md`, ADR-001..008, `scripts/verify_step00.sh` → PASS |
| 01 | Repository foundation | Complete | `pyproject.toml`, `src/aira/{config,seed,device,cli}`, 42 tests; pytest/ruff/mypy all green; `aira doctor` OK |
| 02 | Schema and lifecycle | Complete | `src/aira/memory/domain/*` (enums, records, lifecycle, hashing, clock); 119 tests; pytest/ruff/mypy green; ADR-010 |
| 03 | Aira Guard | Complete | `src/aira/memory/guard/*` (interface, detectors, redaction, guard); 156 tests; pytest/ruff/mypy green; ADR-011 |
| 04 | Aira Vault and Trail | Complete | `src/aira/memory/{vault,trail}/*`; 180 tests; pytest/ruff/mypy green; ADR-012 |
| 05 | Capture and evaluation | Complete | `src/aira/memory/capture/*`; 200 tests; pytest/ruff/mypy green; ADR-013 |
| 06 | Aira Recall | Complete | `src/aira/memory/recall/*` + vault FTS index; 242 tests; pytest/ruff/mypy green; ADR-014 |
| 07 | Ranking and context | Complete | `src/aira/memory/ranking/*`; 267 tests; pytest/ruff/mypy green; ADR-015 |
| 08 | Chat integration | Complete | `src/aira/chat/*` + `aira chat`; 287 tests; pytest/ruff/mypy green; ADR-016 |
| 09 | Aira Fade and governance | Pending | |
| 10 | Aira Bench | Pending | |
| 11 | Aira Core | Pending | |
| 12 | Training and generation | Pending | |
| 13 | Memory-conditioned evaluation | Pending | |
| 14 | Release hardening | Pending | |

## Measured metrics

Stage 00 produces no runtime metrics (no code). Environment probes recorded:

| Probe | Result |
|---|---|
| Python interpreter (system) | 3.13.0 — target is 3.12; Step 01 must pin via `uv` (RISKS R1) |
| `uv` | 0.12.1 |
| SQLite runtime | 3.47.0 |
| SQLite FTS5 | Available and used (Step 06); BM25 fallback implemented and tested |
| Control-tower gate | `scripts/verify_step00.sh` → PASS (docs, links, 15 stage gates, 12 invariants, no runtime code) |

## Step 00 record — 2026-08-04

- **Files created:** `PROJECT_PLAN.md`, `ASSUMPTIONS.md`, `RISKS.md`,
  `scripts/verify_step00.sh`, `adr/008-staged-gates-and-public-research-release.md`,
  `README.md`, `docs/index.html`.
- **Files modified:** `adr/001..007` (ratified Accepted + traceability blocks,
  intent unchanged), `docs/BUILD_STATUS.md`.
- **Commands executed:** repository + document inspection; Python/`uv`/SQLite/FTS5
  probes; `./scripts/verify_step00.sh` → PASS.
- **Test/verification results:** control-tower gate PASS. No unit tests exist yet
  (no runtime code by design).
- **Measured metrics:** see table above.
- **ADR changes:** 001–007 ratified with traceability; 008 added (staged gates +
  public pre-license research release).
- **Remaining limitations:** see below.
- **Next permitted step:** Step 01 — `./scripts/start_step.sh 01`.

## Step 01 record — 2026-08-05

- **Files created:** `pyproject.toml`, `uv.lock`, `.python-version`,
  `src/aira/__init__.py`, `src/aira/config.py`, `src/aira/seed.py`,
  `src/aira/device.py`, `src/aira/cli/{__init__,main}.py`,
  `src/aira/{core,memory,chat,evaluation}/__init__.py`, `tests/conftest.py`,
  `tests/test_{imports,config,device,seed,cli,no_network}.py`, `MODEL_CARD.md`,
  `CONTRIBUTING.md`.
- **Files modified:** `docs/BUILD_STATUS.md`, `README.md` (status bump); removed
  `src/aira/.gitkeep`, `tests/.gitkeep`.
- **Commands executed:** `uv python pin 3.12`; `uv sync`; `uv run pytest`;
  `uv run ruff check .`; `uv run ruff format --check .`; `uv run mypy src`;
  `uv run aira --version/--help/doctor`.
- **Test/verification results:**
  - `uv sync` → CPython **3.12.13** venv, 13 packages (pytest 9.1.1, ruff 0.16.1, mypy 2.3.0).
  - `pytest` → **42 passed** in ~0.1s.
  - `ruff check .` → **All checks passed**.
  - `ruff format --check .` → **62 files already formatted**.
  - `mypy src` (strict) → **no issues in 10 source files**.
  - `aira doctor` → Python 3.12.13 (target), device `cpu`, config OK.
- **Measured metrics:** 42 tests; 0 third-party runtime deps; 3 dev deps; interpreter
  pinned to 3.12.13 (RISKS R1 resolved in-venv); torch deferred (not installed).
- **ADR changes:** none required (foundation follows ADR-001/002/004/007; PyTorch
  deferral documented in `pyproject.toml` and `MODEL_CARD.md`).
- **Remaining limitations:** see below.
- **Next permitted step:** Step 02 — `./scripts/start_step.sh 02`.

## Step 02 record — 2026-08-06

- **Files created:** `src/aira/memory/domain/{__init__,enums,errors,clock,hashing,records,lifecycle}.py`,
  `tests/test_domain_{hashing,records,lifecycle}.py`,
  `adr/010-tombstone-and-hash-integrity.md`.
- **Files modified:** `src/aira/memory/__init__.py` (docstring), `tests/conftest.py`
  (domain fixtures: `fixed_now`, `provenance`, `make_record`), `tests/test_imports.py`
  (domain modules), `docs/BUILD_STATUS.md`.
- **Commands executed:** `uv run pytest`, `uv run ruff check .`,
  `uv run ruff format --check .`, `uv run mypy src`.
- **Test/verification results:**
  - `pytest` → **119 passed** (77 new domain tests + 42 existing).
  - `ruff check .` → **All checks passed**; `ruff format --check .` → **74 files formatted**.
  - `mypy src` (strict) → **no issues in 17 source files**.
- **What was built:** enums (action, kind, lifetime, status, sensitivity, consent,
  retention, provenance source); frozen `Provenance`, `MemoryRecord` and a content-free
  `Tombstone`; `make_memory` factory; deterministic normalization/hashing/canonical
  keys; lifecycle state machine (create/update/supersede/archive/expire/forget/
  hard-delete) with an allowed/forbidden transition table and human-readable reasons.
- **Invariant coverage (tested):** deletion integrity via type-level content-free
  tombstone (inv. 2/7); required owner + provenance (inv. 4); transition validity
  (inv. 11); deterministic hashing + hash-integrity validation (inv. 12); every allowed
  and every forbidden transition exercised.
- **Measured metrics:** 119 tests; 0 runtime deps still (pure stdlib domain).
- **ADR changes:** ADR-010 added (content-free tombstone type + content-hash integrity).
- **Remaining limitations:** see below.
- **Next permitted step:** Step 03 — `./scripts/start_step.sh 03`.

## Step 03 record — 2026-08-06

- **Files created:** `src/aira/memory/guard/{__init__,interface,detectors,redaction,guard}.py`,
  `tests/test_guard.py`, `adr/011-guard-deterministic-span-only-detection.md`.
- **Files modified:** `tests/test_imports.py` (guard modules), `docs/BUILD_STATUS.md`,
  `README.md` (status bump).
- **Commands executed:** `uv run pytest`, `uv run ruff check .`,
  `uv run ruff format --check .`, `uv run mypy src`.
- **Test/verification results:**
  - `pytest` → **156 passed** (37 new guard tests + 119 existing).
  - `ruff check .` → **All checks passed**; `ruff format --check .` → **81 files formatted**.
  - `mypy src` (strict) → **no issues in 22 source files**.
- **What was built:** a replaceable `Guard` protocol and `DeterministicGuard`; span-only
  detectors for private keys, API keys (AWS/GitHub/Google/Slack/Stripe/OpenAI +
  keyword-anchored), bearer/JWT, password assignments, credential URLs, cookies, and
  Luhn-checked payment cards; policy detectors for do-not-remember and
  instruction/override language; redaction with token replacement; a conservative
  sensitivity classifier; an input-size limit; and an audit-safe `GuardEvent`.
- **Invariant coverage (tested):** no raw secret in preview, reason, `repr`, serialized
  event, or logs (inv. 7); one test per secret category + secret-in-prose + multiline
  private key; benign look-alikes not blocked; oversized input blocked without scanning;
  do-not-remember / instruction-like flagged but not blocked (inv. 5, 8).
- **Measured metrics:** 156 tests; secret-persistence scaffold reports **0** raw values
  in any output; still **0** third-party runtime deps.
- **ADR changes:** ADR-011 added (deterministic span-only detection, precision over recall).
- **Remaining limitations:** see below.
- **Next permitted step:** Step 04 — `./scripts/start_step.sh 04`.

## Step 04 record — 2026-08-07

- **Files created:** `src/aira/memory/trail/{__init__,events}.py`,
  `src/aira/memory/vault/{__init__,errors,schema,connection,mapper,repository,backup}.py`,
  `tests/test_vault.py`, `adr/012-vault-persistence-and-audit.md`.
- **Files modified:** `tests/test_imports.py` (vault/trail modules), `docs/BUILD_STATUS.md`,
  `README.md` (status bump).
- **Commands executed:** `uv run pytest`, `uv run ruff check .`,
  `uv run ruff format --check .`, `uv run mypy src`.
- **Test/verification results:**
  - `pytest` → **180 passed** (24 new vault/trail tests + 156 existing).
  - `ruff check .` → **All checks passed**; `ruff format --check .` → **92 files formatted**.
  - `mypy src` (strict) → **no issues in 31 source files**.
- **What was built:** versioned SQLite migrations; owner-scoped, parameterized
  `MemoryRepository` with create/get/list/update/supersede/archive/expire/forget/
  hard-delete; single-transaction state+audit writes; idempotent create; append-only
  `AuditEvent` trail (content-free detail); row-deleting hard delete; JSONL export/import
  (schema-checked, size-bounded, owner-rebinding, guard-screened, atomic); backup +
  integrity check.
- **Invariant coverage (tested):** owner A cannot get/list/update/forget/delete/export
  owner B (inv. 1); rollback on injected audit failure (inv. 11); forgotten/superseded/
  expired excluded by default (inv. 2); hard delete removes content and its audit holds
  none (inv. 2, 7); audit event per mutation; parameterized SQL resists injection;
  idempotency dedup; restart persistence; migration idempotency; import rejects
  secrets/malformed/unknown-schema and writes nothing on rejection.
- **Measured metrics:** 180 tests; still **0** third-party runtime deps (stdlib
  `sqlite3`); zero content in hard-delete audit (asserted).
- **ADR changes:** ADR-012 added (owner-scoped persistence, single-transaction audit,
  row-deleting hard delete).
- **Remaining limitations:** see below.
- **Next permitted step:** Step 05 — `./scripts/start_step.sh 05`.

## Step 05 record — 2026-08-08

- **Files created:** `src/aira/memory/capture/{__init__,models,extraction,evaluation,service}.py`,
  `tests/test_capture.py`, `adr/013-deterministic-capture-and-superseding.md`.
- **Files modified:** `src/aira/memory/vault/repository.py`
  (`find_active_by_canonical_key`), `tests/test_imports.py`, `docs/BUILD_STATUS.md`,
  `README.md` (status bump).
- **Commands executed:** `uv run pytest`, `uv run ruff check .`,
  `uv run ruff format --check .`, `uv run mypy src`.
- **Test/verification results:**
  - `pytest` → **200 passed** (15 new capture tests + 185 existing).
  - `ruff check .` → **All checks passed**; `ruff format --check .` → **99 files formatted**.
  - `mypy src` (strict) → **no issues in 36 source files**.
- **What was built:** deterministic candidate extraction (explicit remember/forget,
  `my <attr> is <value>`, identity, project, instruction, `I prefer <value>`) into
  subject-based canonical keys; a utility evaluator with importance/confidence,
  reasons, and temporary/low-value dropping; and a `CaptureService` that runs guard
  first, refuses assistant promotion, honours do-not-remember, resolves canonical-key
  collisions into supersede/duplicate/new, plans forget operations, and exposes a
  policy trace. Plan-then-apply keeps extraction/evaluation pure.
- **Invariant coverage (tested):** provenance on every memory (inv. 4); selective
  admission incl. temporary drop (inv. 5); assistant statements not promoted (inv. 6);
  instruction-override content not promoted (inv. 8); correction supersedes and forget
  removes (inv. 9); explicit evidence stronger than inferred; duplicate ignored; unsafe
  content blocked by guard before storage; deterministic (inv. 12).
- **Measured metrics:** 200 tests; still **0** third-party runtime deps.
- **ADR changes:** ADR-013 added (deterministic capture, canonical-key superseding).
- **Remaining limitations:** see below.
- **Next permitted step:** Step 06 — `./scripts/start_step.sh 06`.

## Step 06 record — 2026-08-08

- **Files created:** `src/aira/memory/recall/{__init__,models,tokenize,interface,bm25,fts,factory}.py`,
  `tests/test_recall.py`, `adr/014-active-only-index-and-refetch-filtering.md`.
- **Files modified:** `src/aira/memory/vault/{schema,connection,repository,__init__}.py`
  (FTS5 index + maintenance + `fts_search`/`fts_enabled`), `tests/test_imports.py`,
  `docs/BUILD_STATUS.md`, `README.md` (status bump).
- **Commands executed:** `uv run pytest`, `uv run ruff check .`,
  `uv run ruff format --check .`, `uv run mypy src`.
- **Test/verification results:**
  - `pytest` → **242 passed** (42 new recall tests across both backends + 200 existing).
  - `ruff check .` → **All checks passed**; `ruff format --check .` → **108 files formatted**.
  - `mypy src` (strict) → **no issues in 43 source files**.
- **What was built:** a `Retriever` protocol; an FTS5 index maintained by the vault so it
  holds only active content; an `Fts5Retriever` that uses the index as a candidate
  generator then re-fetches through the owner-scoped, active-only `get`; a deterministic
  pure-Python `Bm25Retriever` fallback over the live active set; kind/lifetime/project/
  tag filters; safe bounded query tokenization; explainable scores; and deferred
  vector/graph protocols.
- **Invariant coverage (tested, both backends):** owner isolation (inv. 1); forgotten /
  superseded / expired / hard-deleted content excluded and FTS index purged (inv. 2);
  index updates after correction; empty/malformed/zero-limit queries safe; deterministic
  results (inv. 12); retrieval latency bounded on a 300-memory fixture.
- **Measured metrics:** 242 tests; FTS5 available and used; retrieval < 2 s on 300
  memories; still **0** third-party runtime deps.
- **ADR changes:** ADR-014 added (active-only index + re-fetch filtering + BM25 fallback).
- **Remaining limitations:** see below.
- **Next permitted step:** Step 07 — `./scripts/start_step.sh 07`.

## Step 07 record — 2026-08-08

- **Files created:** `src/aira/memory/ranking/{__init__,tokenizer,models,scoring,dedup,context}.py`,
  `tests/test_ranking.py`, `adr/015-ranking-and-untrusted-context.md`.
- **Files modified:** `tests/test_imports.py`, `docs/BUILD_STATUS.md`, `README.md` (status bump).
- **Commands executed:** `uv run pytest`, `uv run ruff check .`,
  `uv run ruff format --check .`, `uv run mypy src`.
- **Test/verification results:**
  - `pytest` → **267 passed** (19 new ranking tests + 248 existing).
  - `ruff check .` → **All checks passed**; `ruff format --check .` → **116 files formatted**.
  - `mypy src` (strict) → **no issues in 49 source files**.
- **What was built:** a minimal `Tokenizer` protocol + UTF-8 `ByteTokenizer`; a
  deterministic `Ranker` fusing eight configurable, normalized components with full
  weighted breakdowns; canonical + near-identical deduplication; and a `ContextComposer`
  that wraps memories in delimited untrusted-data markers (with delimiter-breakout
  sanitization), enforces top-k and an exact byte-token budget, and records per-memory
  include/exclude reasons (debug ids hidden by default).
- **Invariant coverage (tested):** retrieved memory kept as delimited untrusted data and
  injection/breakout neutralized (inv. 8); exact budget boundary + multibyte + never-
  overflow across budgets (inv. 10); inactive-state defense in depth (inv. 2); score
  components, ordering, tie determinism, dedup, top-k (inv. 12).
- **Measured metrics:** 267 tests; context never exceeds budget for any input; still
  **0** third-party runtime deps.
- **ADR changes:** ADR-015 added (score fusion + delimited budgeted untrusted context).
- **Remaining limitations:** see below.
- **Next permitted step:** Step 08 — `./scripts/start_step.sh 08`.

## Step 08 record — 2026-08-09

- **Files created:** `src/aira/chat/{__init__,backend,models,engine,session}.py`,
  `tests/test_chat.py`, `adr/016-chat-pipeline-and-graceful-degradation.md`.
- **Files modified:** `src/aira/cli/main.py` (`aira chat` subcommand),
  `tests/test_imports.py`, `docs/BUILD_STATUS.md`, `README.md` (status bump).
- **Commands executed:** `uv run pytest`, `uv run ruff check .`,
  `uv run ruff format --check .`, `uv run mypy src`, `uv run aira chat` (piped smoke).
- **Test/verification results:**
  - `pytest` → **287 passed** (20 new chat tests + 267 existing).
  - `ruff check .` → **All checks passed**; `ruff format --check .` → **122 files formatted**.
  - `mypy src` (strict) → **no issues in 53 source files**.
  - `aira chat` piped smoke → stored, listed and recalled "my editor is vim".
- **What was built:** a model-agnostic `GenerationBackend` protocol + deterministic
  `MockBackend`; a `ChatEngine` running guard→decide→mutate→retrieve→rank→compose→
  generate with correlation ids, latency, debug-only metadata, and isolated write/read/
  backend failures that degrade to a no-memory response; a testable slash-command session
  (`/memories /memory /forget /debug /stats /reset /exit`); and the `aira chat` CLI.
- **Invariant coverage (tested):** end-to-end remember/recall/correct/forget; unsafe
  write blocked, nothing stored; owner isolation through chat (inv. 1); retrieval-timeout,
  db-unavailable and malformed-memory all still return a response (inv. 3); untrusted
  block reaches the backend (inv. 8); debug hides ids by default; latency + correlation id
  present.
- **Measured metrics:** 287 tests; the full Aira Memory lifecycle works through chat on a
  deterministic mock backend; still **0** third-party runtime deps.
- **ADR changes:** ADR-016 added (chat pipeline, model-agnostic backend, graceful degradation).
- **Remaining limitations:** see below.
- **Next permitted step:** Step 09 — `./scripts/start_step.sh 09`.

## Known limitations

- The backend is a deterministic mock that echoes recalled facts; it makes no language-
  quality claim. Aira Core integration is Step 13.
- Retrieval failures degrade by catching exceptions (including a raised `TimeoutError`); a
  hard preemptive timeout needs a thread-safe read path and is deferred (ADR-016).
- Governance jobs (decay/expiry/archival, inspect/export/delete-all) are Step 09; no
  model, training or benchmark yet.
- No at-rest encryption or key management is claimed; local file-system trust only
  (documented in the threat model; a production gap for Step 14).
- SQLite gives transactions but not hosted multi-tenant controls (e.g. row-level
  security); that is a documented migration target.
- The guard detects a documented, non-exhaustive set of secret formats (ADR-011).
- Only the project foundation + domain exist: config, determinism, device selection, a
  CLI skeleton, and the typed memory domain. No memory *runtime* or model behaviour yet.
- `MODEL_CARD.md` explicitly states no model/tokenizer/checkpoint exists yet.
- `MODEL_CARD.md` explicitly states no model/tokenizer/checkpoint exists yet.
- All security properties remain design intent; zero-tolerance metrics become
  measurable only at Step 10.
- Production readiness has not been established.
- License has not been selected; absent a `LICENSE`, the work is all-rights-reserved.
- `SECURITY.md` / `PRIVACY.md` are scheduled for Step 14.
- PyTorch is not installed by default (deferred to Step 11 via the `core` extra), so
  `aira doctor` reports device `cpu` until then.
- The source architecture is a design reference, not independently validated
  production evidence.

## Update format

After every step add:

- date
- files changed
- commands executed
- test results
- measured metrics
- ADR changes
- remaining limitations
- next permitted step
