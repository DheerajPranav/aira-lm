# ADR: Staged build gates and a public pre-license research release

- Status: Accepted (Step 00 control-tower review)
- Date: 2026-08-04
- Last reviewed: 2026-08-04

## Context

Aira LM is built one numbered prompt at a time. Two things needed a recorded
decision at the control tower: (1) how "done" is judged for each stage, and (2)
whether the repository may be published publicly before a license is chosen and
before hosted-production hardening exists. The owner asked for the work to be
published as a public `aira-lm` GitHub repository with a landing page.

## Decision

1. **Per-stage completion gates.** Each stage 00–14 has a measurable gate recorded
   in `PROJECT_PLAN.md`. A stage is complete only when its gate passes with recorded
   evidence and `docs/BUILD_STATUS.md` is updated. No stage begins until the previous
   gate is met (`CLAUDE.md` hard workflow rule).
2. **Zero-tolerance metrics.** Cross-owner leakage, forgotten-memory leakage, secret
   persistence and context-budget violations must equal 0 in the Step 10 suite; a
   regression fails the build (invariant 12).
3. **Public research release before license.** The repository may be published
   publicly to describe the vision, architecture and honest status. No `LICENSE` is
   invented; absent one, the work is all-rights-reserved by default. The public
   README and Pages landing page must state the real status (Stage 00, no runtime
   code) and must not claim production readiness.

## Alternatives considered

- Keep the repository private until Step 14. Rejected: the owner explicitly asked
  to publish now, and an honest early landing page carries no correctness claim.
- Pick a permissive license now to "unblock" publishing. Rejected: `CLAUDE.md`
  forbids inventing a license; the choice stays with the owner.

## Consequences

- Readers get an accurate picture of an in-progress project; contributors have no
  granted license until one is chosen (a deliberate, documented limitation).
- Every later claim must be backed by a repeatable test or benchmark.

## Traceability

- Upholds invariant: 12 (measured claims).
- Requirements: documentation set; evaluation gates; honest status reporting.
- Verified in stages: 00 (`scripts/verify_step00.sh`), 10 (Aira Bench), 14 (release).

## Migration path

When the owner selects a license, add `LICENSE` and update README/Pages. Before any
hosted deployment, satisfy the production-gap document (Step 14): authentication,
at-rest encryption and key management, row-level security, remote deployment,
incident response, legal review and scale testing.
