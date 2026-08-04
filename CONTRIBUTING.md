# Contributing to Aira LM

Aira LM is an early-stage research project built one verified stage at a time. These
notes describe how the code is developed and what "done" means here.

> **License note:** no license has been selected yet, so the project is
> all-rights-reserved by default. Until a license is added, please open an issue to
> discuss before reusing the code.

## Environment

- Python **3.12** (the target; `uv` pins it — the system interpreter may differ).
- [`uv`](https://docs.astral.sh/uv/) for dependency and environment management.
- Apple M2 / 8 GB is the primary target; CPU-only must keep working.

```bash
uv python pin 3.12     # once, if not already pinned
uv sync                # create the venv and install dev tools
uv run aira doctor     # sanity-check the environment
```

## Quality gates

Every change must pass all of these before it is considered complete:

```bash
uv run pytest
uv run ruff check .
uv run ruff format --check .
uv run mypy src
```

- Tests are **deterministic and offline**. A default guard blocks network access in
  tests; mark a test `@pytest.mark.network` only if it genuinely must connect.
- `mypy` runs in `strict` mode over `src`.
- Formatting and linting are enforced by `ruff`.

## How work is organized

- The build proceeds through the numbered prompts in `prompts/` (Steps 00–14).
- One step per change set. Do not begin the next step until the current step's gate
  passes and `docs/BUILD_STATUS.md` is updated with evidence.
- Architectural decisions are recorded as ADRs in `adr/`.

## Design rules (from `CLAUDE.md`)

- No cloud model APIs, no hidden network calls, no automatic large downloads in the
  runtime or tests.
- No orchestration frameworks (LangChain, LlamaIndex, CrewAI, AutoGen, …).
- Keep `aira.core` (the model) and `aira.memory` (the memory runtime) independent.
- Prefer the standard library; keep dependencies minimal and documented.
- Never claim a security, quality or performance property without a repeatable test
  or benchmark.

## Commit messages

Describe the behaviour changed and the evidence. Keep the two systems' concerns
separate in a single change where practical.
