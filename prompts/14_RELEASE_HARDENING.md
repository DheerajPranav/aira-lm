# Step 14 — Release Hardening

## Objective

Prepare a reproducible local research release and clearly document what remains before any hosted production deployment.

## Prerequisites

All previous steps complete.

## Required procedure

1. Read `CLAUDE.md` and the imported project documents.
2. Inspect the repository and `docs/BUILD_STATUS.md`.
3. Confirm earlier stages are complete.
4. Write a concise implementation plan for this step.
5. Implement only the scope below.
6. Run the required verification.
7. Update `docs/BUILD_STATUS.md`.
8. Update relevant ADRs.
9. Stop. Do not begin the next stage.

## Build scope

- Run complete test, lint, format, type and benchmark suites.
- Add schema migration and backup/restore verification.
- Add dependency vulnerability and license review instructions.
- Add packaging and installation tests.
- Complete README, MODEL_CARD, SECURITY, PRIVACY and CONTRIBUTING docs.
- Add release checklist and reproducibility manifest.
- Measure default model parameters, smoke training resource use and benchmark metrics.
- Confirm runtime makes no hidden network calls.
- Review threat model and residual risk.
- Produce a production-gap document covering authentication, encryption keys, RLS, remote deployment, incident response, legal review and scale testing.
- Do not select a license without user approval.

## Required tests and verification

- fresh environment install
- complete quality gates
- all zero-tolerance metrics remain zero
- backup/restore
- migration
- package build/install
- offline runtime test
- documented measurements
- release checklist

## Done when

Aira LM is a reproducible, security-tested local research release with honest limitations and a precise hosted-production migration plan.

## Explicit exclusions

No claim of audited production readiness, no deployment to cloud, no invented license.

## Completion report

Report files changed, commands actually run, exact results, measured metrics, limitations, ADR changes, and the command for the next step.
