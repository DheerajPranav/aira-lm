# Step 00 — Control Tower

## Objective

Establish the project control plane before implementation. Validate the supplied architecture, identify contradictions or missing decisions, and prepare a stage-by-stage execution plan.

## Prerequisites

None. This is the first step.

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

- Inspect every supplied document and prompt.
- Inspect the attached source study in `references/memory-system.html`.
- Verify that the architecture preserves the hard invariants.
- Create `PROJECT_PLAN.md` with stages, dependencies, deliverables and verification gates.
- Create `ASSUMPTIONS.md` and `RISKS.md`.
- Review ADR-001 through ADR-007 and improve them without changing their intent.
- Create a proposed final repository tree.
- Do not implement Python runtime code yet.
- Record unresolved decisions, including license choice, exact dependency versions, SQLite FTS5 availability and encryption scope.

## Required tests and verification

- Check that all required documents exist.
- Check internal links and referenced paths.
- Validate that each hard invariant maps to at least one planned test.
- Validate that every stage has a measurable completion gate.

## Done when

The repository has an executable written plan, traceability from requirements to tests, and no runtime implementation has started.

## Explicit exclusions

No Python package implementation, no dependency installation, no database schema, no model code.

## Completion report

Report files changed, commands actually run, exact results, measured metrics, limitations, ADR changes, and the command for the next step.
