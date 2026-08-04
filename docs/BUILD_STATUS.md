# Build Status

## Current stage

- Stage: 01 — Repository Foundation
- Status: Complete (foundation only; no memory or model behaviour)
- Last verified commit: Step 01 commit of `aira-lm` (2026-08-05)
- Last updated: 2026-08-05 by Claude Code

## Stage checklist

| Step | Name | Status | Evidence |
|---:|---|---|---|
| 00 | Control tower and audit | Complete | `PROJECT_PLAN.md`, `ASSUMPTIONS.md`, `RISKS.md`, ADR-001..008, `scripts/verify_step00.sh` → PASS |
| 01 | Repository foundation | Complete | `pyproject.toml`, `src/aira/{config,seed,device,cli}`, 42 tests; pytest/ruff/mypy all green; `aira doctor` OK |
| 02 | Schema and lifecycle | Pending | |
| 03 | Aira Guard | Pending | |
| 04 | Aira Vault and Trail | Pending | |
| 05 | Capture and evaluation | Pending | |
| 06 | Aira Recall | Pending | |
| 07 | Ranking and context | Pending | |
| 08 | Chat integration | Pending | |
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
| SQLite FTS5 | Available (re-verify at runtime in Step 06) |
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

## Known limitations

- Only the project foundation exists: config, determinism, device selection and a CLI
  skeleton. No memory or model behaviour is implemented.
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
