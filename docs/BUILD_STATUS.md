# Build Status

## Current stage

- Stage: 00 — Control Tower
- Status: Complete (control plane only; no runtime code)
- Last verified commit: initial public commit of `aira-lm` (2026-08-04)
- Last updated: 2026-08-04 by Claude Code

## Stage checklist

| Step | Name | Status | Evidence |
|---:|---|---|---|
| 00 | Control tower and audit | Complete | `PROJECT_PLAN.md`, `ASSUMPTIONS.md`, `RISKS.md`, ADR-001..008, `scripts/verify_step00.sh` → PASS |
| 01 | Repository foundation | Pending | |
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

## Known limitations

- No runtime implementation exists yet; all security properties are design intent,
  not verified behaviour. Zero-tolerance metrics become measurable only at Step 10.
- Production readiness has not been established.
- License has not been selected; absent a `LICENSE`, the work is all-rights-reserved.
- Required docs `MODEL_CARD.md` (Step 01) and `SECURITY.md`/`PRIVACY.md` (Step 14)
  are not yet created.
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
