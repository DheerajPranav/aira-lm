# Step 01 — Repository Foundation

## Objective

Create a minimal, reproducible Python project foundation for Aira LM without implementing substantive memory or model behavior.

## Prerequisites

Step 00 complete and recorded.

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

- Create `pyproject.toml` for Python 3.12 using a src layout.
- Add minimal runtime and development dependencies, documenting every dependency.
- Configure pytest, ruff and mypy.
- Create package namespaces for core, memory, chat, evaluation and CLI.
- Add configuration loading and validation for `configs/aira_tiny.toml`.
- Implement deterministic seed utilities.
- Implement device selection: MPS, CUDA, CPU.
- Create CLI skeleton with `aira --help`, `aira doctor`, and version output.
- Add a no-network test marker or guard.
- Create README, MODEL_CARD and contribution notes that accurately state current status.
- Avoid placeholder classes; package modules may be minimal but importable.

## Required tests and verification

- `uv sync`
- import smoke test
- CLI help and doctor tests
- configuration validation tests
- device selection tests using mocks
- `uv run pytest`
- `uv run ruff check .`
- `uv run ruff format --check .`
- `uv run mypy src`

## Done when

Fresh checkout setup works, all quality gates pass, and no memory or transformer feature is falsely claimed as implemented.

## Explicit exclusions

No database, retrieval, tokenizer, transformer, hosted API, Docker or web UI.

## Completion report

Report files changed, commands actually run, exact results, measured metrics, limitations, ADR changes, and the command for the next step.
